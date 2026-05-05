# Runbook v2 — AI Readiness Pipeline

System: ai-readiness-pipeline (questionnaire v2)
Stack: Python 3.12 + FastAPI + SQLite (aiosqlite) + Structlog + React 19 + Vite

---

## 1. Arrancar el sistema

```bash
# Build de frontend (solo si hubo cambios en frontend/)
cd frontend && npm run build && cd ..

# Levantar con Docker Compose
docker-compose up -d

# Aplicar migraciones pendientes
docker-compose exec app alembic upgrade head

# Verificar que levantó
curl http://localhost:8100/api/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "schema_version": "1.0",
  "db_connection": "ok",
  "llm_availability": "unknown",
  "uptime_seconds": 12,
  "git_sha": "abc1234"
}
```

Si `status` es `"degraded"`, revisar `db_connection`.

---

## 2. Verificar healthcheck

```bash
curl -s http://localhost:8100/api/health | python3 -m json.tool
```

Campos clave:
- `status`: `"ok"` o `"degraded"`
- `db_connection`: `"ok"` o `"fail"` — si es `"fail"`, revisar la DB
- `schema_version`: debe coincidir con el `schema_version` en `schemas/questionnaire-v2/_root.yaml`
- `uptime_seconds`: tiempo desde startup
- `git_sha`: SHA del commit desplegado (requiere env var `GIT_SHA` o acceso a `.git/HEAD`)
- `rate_limit_blocks`: contador de 429s emitidos (útil para detectar abuso)

---

## 3. Correr una nueva migration de Alembic

```bash
# Crear nueva revisión (auto-detect de cambios en modelos)
docker-compose exec app alembic revision --autogenerate -m "descripcion_breve"

# Revisar el archivo generado en alembic/versions/ ANTES de aplicar
# Editar si es necesario

# Aplicar
docker-compose exec app alembic upgrade head

# Verificar estado
docker-compose exec app alembic current
```

Para rollback de la última migración:

```bash
docker-compose exec app alembic downgrade -1
```

---

## 4. Revisar logs (formato structlog)

Los logs se emiten en JSON por stdout. Para leerlos con jq:

```bash
docker-compose logs -f app | grep "^{" | jq -c '{ts: .timestamp, ev: .event, lead: .lead_id}'
```

Eventos clave a monitorear:

| Evento | Cuándo | Campos relevantes |
|--------|--------|-------------------|
| `lead_created` | POST /public/triage/submit | lead_id, bucket, score |
| `lead_bucket_assigned` | POST /public/triage/submit | lead_id, bucket, override_applied |
| `lead_accepted` | PATCH /admin/leads/{id} | lead_id, consultant_id |
| `lead_rejected` | PATCH /admin/leads/{id} | lead_id, reason |
| `intake_session_started` | POST /intake/{id}/area-selection | lead_id, primary_area |
| `block_submitted` | POST /intake/{id}/blocks/{bid}/submit | lead_id, block_id, payload_size |
| `block_analyzed` | BackgroundTask (LLM analysis) | block_id, llm_model, latency_ms, suggestions_count |
| `suggestion_action` | POST /intake/{id}/suggestions/{sid}/action | lead_id, suggestion_id, action |
| `session1_closed` | POST /intake/{id}/session1/close | lead_id, deep_branches_created |
| `deep_branch_sent` | POST /intake/{id}/deep/{bid}/send | lead_id, branch_id |
| `deep_branch_received` | POST /client/deep/{token}/submit | lead_id, branch_id, response_count |
| `email_sent` | async (BackgroundTask) | recipient, template, lead_id |
| `rate_limit_exceeded` | POST /public/triage/submit | ip_hash, endpoint |

Para filtrar bloques fallidos:

```bash
docker-compose logs app | grep "block_analysis_failed" | jq .
```

---

## 5. Recuperar BlockAnalysis huérfanas (status=pending_analysis sin avance)

Una `BlockAnalysis` queda huérfana si el proceso se reinicia mid-task. Para detectarlas y re-dispararlas:

```bash
# Conectar a SQLite
sqlite3 app/data/app.db

SELECT id, block_id, status, created_at
FROM block_analyses
WHERE status = 'pending_analysis'
ORDER BY created_at;
```

Para re-disparar manualmente vía CLI:

```bash
docker-compose exec app python3 -c "
import asyncio
from app.db.session import async_session_factory
from app.services.ai_analysis.block_analyzer import BlockAnalyzer

async def rerun(ba_id: str, block_id: str):
    async with async_session_factory() as db:
        analyzer = BlockAnalyzer(db=db)
        await analyzer.analyze(block_analysis_id=ba_id, block_id=block_id)

asyncio.run(rerun('BLOCK_ANALYSIS_ID_AQUI', 'block-1-strategic'))
"
```

Reemplazar `BLOCK_ANALYSIS_ID_AQUI` con el UUID real y `block-1-strategic` con el block_id correspondiente.

---

## 6. Emitir signed URL manualmente para debug

Útil cuando un cliente dice que su URL de DEEP no funciona o expiró.

```bash
docker-compose exec app python3 -c "
from app.signed_urls import sign_payload
import json

# Ajustar lead_id, branch_ids y TTL
token = sign_payload(
    {'lead_id': 'LEAD_UUID', 'branch_ids': ['BRANCH_UUID'], 'purpose': 'deep_form'},
    ttl_seconds=90 * 86400,  # 90 días
)
print('Token:', token)
print('URL: https://air.zanovix.com/deep/' + token)
"
```

Para verificar un token existente:

```bash
docker-compose exec app python3 -c "
from app.signed_urls import verify_payload
import json

token = 'TOKEN_AQUI'
try:
    payload = verify_payload(token)
    print('Valid:', json.dumps(payload, indent=2))
except Exception as e:
    print('Invalid:', e)
"
```

---

## 7. Cargar nuevo schema YAML

El schema se carga al startup desde `schemas/questionnaire-v2/`. No hay hot-reload.

Proceso:

1. Editar los archivos YAML en `schemas/questionnaire-v2/`
2. Validar localmente antes de deployar:
   ```bash
   python3 -c "from app.services.questionnaire.schema_loader import load_all; load_all(); print('OK')"
   ```
3. Si OK, deployar y reiniciar:
   ```bash
   docker-compose up -d --force-recreate app
   ```
4. Verificar que el schema cargó:
   ```bash
   curl -s http://localhost:8100/api/health | jq .schema_version
   ```

Si el schema es inválido, el startup falla con error structlog `schema_v2_load_failed` y el container no levanta.

---

## 8. Borrar lead + consents respetando retención RGPD

Las `Consents` tienen FK con `ondelete=RESTRICT` — no se puede borrar un Lead con consents vigentes.

Proceso correcto:

```bash
sqlite3 app/data/app.db

-- 1. Verificar consents del lead
SELECT id, type, accepted, timestamp FROM consents WHERE lead_id = 'LEAD_UUID';

-- 2. Anonimizar lead (no borrar — retención RGPD 5 años en consents)
UPDATE leads SET
    full_name = '[ANONIMIZADO]',
    email = 'anon_' || id || '@deleted.invalid',
    phone = NULL,
    company_name = '[ANONIMIZADO]',
    triage_payload = '{}'
WHERE id = 'LEAD_UUID';

-- 3. Si se necesita borrar consents (solo tras vencer retención 5 años):
--    SET lead_id = NULL antes de borrar el lead
UPDATE consents SET lead_id = NULL WHERE lead_id = 'LEAD_UUID';
DELETE FROM leads WHERE id = 'LEAD_UUID';

-- NOTA: los consents quedan en la tabla con lead_id=NULL como audit trail AEPD
```

Política de retención:
- `consents`: mínimo 5 años desde `timestamp`
- `leads` rechazados (status=rejected): anonimizar PII a 6 meses
- `leads` convertidos (status=converted): retención indefinida

---

## 9. Variables de entorno requeridas

Definidas en `.env` en la raíz del proyecto. Ver `config.py` para valores por defecto.

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Sí | API key de Anthropic para análisis LLM |
| `SECRET_KEY` | Sí | HMAC key para signed URLs y sesiones admin |
| `DB_URL` | No | SQLAlchemy URL (default: `sqlite+aiosqlite:///app/data/app.db`) |
| `WEBHOOK_SECRET` | No | Bearer token para el endpoint público (vacío = dev mode) |
| `SMTP_HOST` | Sí (prod) | Host SMTP para envío de emails |
| `SMTP_PORT` | No | Puerto SMTP (default: 587) |
| `SMTP_USER` | Sí (prod) | Usuario SMTP |
| `SMTP_PASSWORD` | Sí (prod) | Contraseña SMTP |
| `SMTP_FROM` | No | Dirección From (default: SMTP_USER) |
| `SMTP_USE_TLS` | No | STARTTLS (default: true) |
| `CORS_ORIGINS` | No | Orígenes CORS permitidos (default: assess.zanovix.com) |
| `TRUSTED_PROXY` | No | Trust X-Forwarded-For (default: false) |
| `IP_HASH_SALT` | Sí (prod) | Salt para hash de IPs (RGPD) |
| `CONSULTANT_EMAIL` | No | Email del consultor para notificaciones |
| `DEEP_SESSION_TTL_DAYS` | No | TTL signed URL DEEP (default: 90) |
| `GIT_SHA` | No | SHA del commit (para /api/health git_sha) |

Generar claves seguras:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
