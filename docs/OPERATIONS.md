# AI Readiness Platform — Operations Runbook

Tactical reference for running the platform in production. Recipes, not prose.

---

## 1. First Deploy

```bash
# 1. Build and start
docker compose build
docker compose up -d

# 2. Create the first admin user
docker exec ai-readiness python -m app.cli create_admin \
  --email pepe@zanovix.com \
  --password '<strong-password-from-1password>'

# 3. Verify
curl -s https://<host>/api/health | jq .
# Browser: navigate to https://<host>/admin/login → login → empty assessments list
```

Migrations run automatically on startup via `scripts/entrypoint.sh` (`alembic upgrade head`).

---

## 2. Daily Operations

```bash
# View logs (last 100 lines, follow)
docker compose logs -f --tail=100 pipeline

# Restart
docker compose restart pipeline

# Shell into the container
docker exec -it ai-readiness bash

# List active admin sessions (DB query)
docker exec ai-readiness python -c "
import asyncio
from app.db.session import async_session_factory
from app.models.session_row import SessionRow
from sqlalchemy import select
from datetime import datetime, timezone

async def run():
    async with async_session_factory() as db:
        rows = (await db.execute(
            select(SessionRow).where(SessionRow.revoked_at.is_(None),
                                     SessionRow.expires_at > datetime.now(tz=timezone.utc))
        )).scalars().all()
        for r in rows:
            print(r.id[:8], r.user_id, r.last_seen_at)

asyncio.run(run())
"
```

---

## 3. Backups

### Setup (run once on the host)

```bash
# Install sqlite3 if not present
apt-get install -y sqlite3

# Create backup directory
mkdir -p /backups

# Add daily cron at 3am
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/ai-readiness/scripts/backup.sh >> /var/log/ai-readiness-backup.log 2>&1") | crontab -
```

### Manual backup

```bash
./scripts/backup.sh
# Output: /backups/app-YYYYMMDD_HHMMSS.db.gz
```

Default retention: 30 days. Override with `RETENTION_DAYS=90 ./scripts/backup.sh`.

Default DB path: `/var/lib/docker/volumes/ai-readiness-pipeline_app_db/_data/app.db`.
Override with `DB_PATH=/custom/path.db` if your Docker project name differs.

### Verify a backup

```bash
# Decompress to temp location and check integrity
gunzip -c /backups/app-20260503_030000.db.gz > /tmp/check.db
sqlite3 /tmp/check.db "PRAGMA integrity_check"
# Expected output: ok
```

---

## 4. Restore

```bash
./scripts/restore.sh /backups/app-20260503_030000.db.gz
```

The script stops the container, swaps the DB file, and restarts. After restore, verify:

```bash
curl -s https://<host>/api/health | jq .
curl -s https://<host>/api/admin/auth/me   # expect 401, not 500
```

**Manual fallback** (if Docker compose commands fail):

```bash
docker stop ai-readiness
gunzip -c /backups/app-20260503_030000.db.gz \
  > /var/lib/docker/volumes/ai-readiness-pipeline_app_db/_data/app.db
docker start ai-readiness
```

---

## 5. Rotating Secrets

### SECRET_KEY (signs download URLs)

```bash
# Generate new key
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
# Add to .env: SECRET_KEY=<new-value>
docker compose up -d  # rolling restart picks up new env
```

**Warning**: rotating SECRET_KEY invalidates ALL outstanding signed download URLs.
Clients who have not yet downloaded their report will get a 403 error. Rotate only
if the key is compromised; not on a schedule.

### WEBHOOK_SECRET (authenticates public form submissions)

```bash
# Generate new secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Update in .env AND in the React wizard's VITE_WEBHOOK_SECRET (rebuild frontend)
docker compose build frontend
docker compose up -d
```

---

## 6. Manual Maintenance

```bash
# Prune expired sessions
docker exec ai-readiness python -c "
import asyncio; from app.db.session import async_session_factory; from app.auth.sessions import prune_expired
async def r():
    async with async_session_factory() as db:
        print('Pruned', await prune_expired(db)); await db.commit()
asyncio.run(r())"

# Prune login_attempts (rows > 7 days)
docker exec ai-readiness python -c "
import asyncio; from app.db.session import async_session_factory; from sqlalchemy import text
async def r():
    async with async_session_factory() as db:
        res = await db.execute(text(\"DELETE FROM login_attempts WHERE attempted_at < datetime('now', '-7 days')\")); await db.commit(); print('Pruned', res.rowcount)
asyncio.run(r())"

# Debug a stuck job: check logs, then restart (startup re-enqueue recovers pending_review)
docker compose logs pipeline | grep <assessment_id>
docker compose restart pipeline
```

---

## 7. Troubleshooting

| Symptom | Check |
|---|---|
| Container won't start | `docker compose logs pipeline` — usually missing env var or migration failure |
| Alembic migration fails | `docker exec ai-readiness alembic current` then `alembic history` to compare |
| Login fails after deploy | Verify `SECRET_KEY` set; check user via `docker exec ai-readiness python -m app.cli list_admins` |
| PDF generation hangs | `docker exec ai-readiness pkill soffice` then `docker compose restart pipeline` |
| Email not sent | Check `SMTP_HOST/PORT/USER/PASSWORD`; `docker compose logs pipeline \| grep smtp` |
| Signed URL 403 | Rotated `SECRET_KEY` after URL was issued — use "Reenviar email" to reissue |
| Signed URL 410 | Link expired (>7 days) — use "Reenviar email" in admin editor |

---

## 8. Frontend smoke after admin-frontend-independence change

Manual checklist — run after any deploy that touches the admin editor or form_data pipeline.

1. Login at `/admin/login`.
2. Click "Nuevo assessment", fill 6 minimum fields, save → redirected to editor.
3. Verify all 11 tabs load: Empresa, Stack, Cliente, Marketing, Operaciones, Finanzas, RRHH, Compliance, Presupuesto, Enriquecimientos, Scoring.
4. In Stack tab, edit `software_used` to `["Notion","Slack"]`. Wait 1s. In browser Network tab verify a PATCH fired with `form_data_patch`. Refresh → value persists.
5. In Stack tab, type a value AND change `company_name` in Empresa tab within 500ms. Verify ONE coalesced PATCH fired with both fields.
6. Click "Re-correr LLM" with sparse data → `SparseConfirmDialog` appears with "X de 42 campos" message. Click Cancelar → no job queued.
7. Click again, click "Sí, continuar de todas formas" → job queued. Polling shows status updates.
8. Click "Aprobar y enviar" → existing modal appears. Click Confirmar. Sparse amber banner appears. Click "Sí, continuar de todas formas" → approve POST fires.

---

## 9. Deploying the admin-frontend-independence change

No DB migration needed — only `form_data` blob shape changes, not the column schema.

```bash
# 1. Pull latest code
git pull

# 2. Rebuild the backend image
docker compose build pipeline

# 3. Restart the container
docker compose up -d

# 4. Clean up legacy orphan keys (dry-run first)
docker exec air-pipeline python -m app.cli cleanup-form-data-keys
# Review the output. If comfortable, apply:
docker exec air-pipeline python -m app.cli cleanup-form-data-keys --apply

# 5. Run the manual frontend smoke checklist (§ 8 above)
```
