# AI Readiness Pipeline — Documentación completa del sistema
*Actualizado: 29 marzo 2026*

## Arquitectura general

```
Cliente rellena formulario (código ZNV-XXXX)
    ↓
Google Sheet (respuestas) + AppScript (onFormSubmit)
    → Scoring matemático (pts_tools, pts_automation, etc.)
    → Escribe en pestaña 'analysis' y 'report_output'
    → Email "AIR-ASSESSMENT:" a pepe@zanovix.com con JSON del assessment
    ↓
Cron OpenClaw (ID: 54215d5d, cada 15 min)
    → Detecta email AIR-ASSESSMENT: en inbox
    → Extrae JSON del email
    → Ejecuta pipeline.py con el JSON
    ↓
pipeline.py (orquestador autónomo)
    1. llm_enricher.py → genera TODOS los campos LLM (16 campos) en una sola llamada
       - textos simples: executive_summary, current_state, opportunities, etc.
       - estructurados: inventory_table, risk_findings_structured, opportunity_matrix,
                        economic_estimate, roadmap_structured, dependencies, scoring_answers
    2. scoring_engine.py → construye tablas trazables desde pts_* del AppScript
    3. report_generator.py → genera .docx 12-15 páginas con branding Zanovix
    4. generate-deck.mjs → genera .pptx 8 slides
    5. Sube ambos a Drive (carpeta: 1ZIz3o01cSOZWaRk_YrnRuM5krBIgkTih)
    6. Actualiza report_output del sheet (todos los campos llm_*)
    7. Email de confirmación a pepe@zanovix.com
    8. Actualiza Notion Assessments (estado=Completado, URLs Drive)
```

## Archivos del sistema

### AppScript (Google Sheets trigger)
- **Sheet**: `1cMZuWl2t3dH_7-6LIKMkXL9S8ueMMKPz69rK_AiZoZ8`
- **Script ID**: `1s95dO5tSr_bbE0n-dZrXBtBTiU5Ji9ByzC7OkKsIHzzXJjGlNJQSV6Cg`
- **Código fuente**: `appscript_v2_correct.js` (también en Drive: `1cqLugrDyO31VLbi4GnaaDeTz3-5ftAbA`)
- Trigger: `onFormSubmit → processNewSubmission_`
- Escribe pts_* en AMBAS pestañas: `analysis` y `report_output`

### Pipeline local (`/workspace/ai-readiness-pipeline/`)
- `pipeline.py` — orquestador completo y autónomo. Llama al enricher, genera doc+deck, sube a Drive.
- `llm_enricher.py` — genera 16 campos LLM en una sola llamada (max_tokens=8000). **Fuente única de enriquecimiento.**
- `report_generator.py` — genera .docx con branding Zanovix (11 secciones)
- `scoring_engine.py` — construye tablas trazables desde pts_* del AppScript
- `PIPELINE_INSTRUCTIONS.md` — instrucciones del enricher (ya no se usa para subagente externo)
- `appscript_v2_correct.js` — código del AppScript listo para sincronizar con Google

### Deck (.pptx)
- `/workspace/tools/ai-readiness-deck/generate-deck.mjs`
- 8 slides: Portada, Madurez, Costes, Oportunidades, Riesgo, Roadmap, Propuesta, Certificado

## Formulario

- **Form ID**: `1cbBlBXfu2Usel_vl0_PLoISGOqaRdQipvXufy0DOcI8`
- **Link**: https://docs.google.com/forms/d/e/1FAIpQLSd71PcoOHFbwaoY2WFou7VBrW1PxE6kpfANwDEBgGPJAVGwwA/viewform
- 45 preguntas v2 (incluye proceso prioritario, DPA, política IA, presupuesto)
- P1 = Código de acceso (ZNV-XXXX)

## Notion

- **BD Clientes**: `33118d57-3b10-817f-988d-de404714b98d`
- **BD Assessments**: `33118d57-3b10-81d3-a7a0-c56f70f41853`
- Relación: Assessment → Cliente (1 cliente puede tener N assessments)
- Campo "Codigo acceso" en Assessments = ZNV-XXXX

## Gestión de códigos de acceso

```bash
# Crear cliente + assessment (genera el código ZNV-XXXX)
python3 /workspace/tools/assessment-codes/generate-code.py \
  --create "Empresa XYZ" --sector "Retail/Comercio"

# Verificar un código
python3 /workspace/tools/assessment-codes/generate-code.py --verify ZNV-XXXX

# Listar todos los códigos activos
python3 /workspace/tools/assessment-codes/generate-code.py --list
```

## Variables de entorno requeridas

```bash
OPENROUTER_API_KEY=sk-or-v1-...   # Para llm_enricher.py (modelo claude-sonnet-4-5)
```
(La key se pasa directamente en el cron del pipeline)

## Ejecución manual

```bash
cd /home/pepe/.openclaw/workspace/ai-readiness-pipeline
OPENROUTER_API_KEY=sk-or-v1-... python3 pipeline.py '<JSON_DEL_ASSESSMENT>'
```

El JSON mínimo necesario es el que genera el AppScript (incluye access_code, scores, pts_*, respuestas del formulario).

## Cron del pipeline

- **ID**: `54215d5d-cb92-493e-b3b7-2f0dfa3bdfc3`
- **Frecuencia**: cada 15 minutos
- **Acción**: detecta email AIR-ASSESSMENT: → extrae JSON → ejecuta pipeline.py
- El pipeline es completamente autónomo desde el JSON

## Sheet report_output — columnas

Las 49 columnas cubren:
- Identificadores: assessment_id, company_name, access_code, sector, employee_range
- Scoring: pts_tools → pts_incident, maturity_score, maturity_level, risk_score, risk_level
- Interno (no cliente): deal_fit_score, deal_fit_level, top_gaps, top_opportunities
- LLM textos: llm_executive_summary, llm_current_state, llm_opportunities, etc.
- LLM estructurados: llm_scoring_answers, llm_inventory_table, llm_risk_findings_structured,
                     llm_opportunity_matrix, llm_economic_estimate, llm_roadmap_structured,
                     llm_dependencies
- Estado: drive_url, deck_url, processed_at, review_status, last_updated

## Bugs conocidos / historial

- **2026-03-29**: max_tokens 5000→8000 (assessments complejos ~5500 tokens de output)
- **2026-03-29**: scores resumen≠tabla resuelto (pts_* ahora en report_output + score canónico del sheet)
- **2026-03-29**: claves económicas técnicas normalizadas en report_generator
- **2026-03-29**: enricher integrado en pipeline.py (autónomo, no depende de subagente externo)
- **2026-04-08**: Fallback LLM agregado (claude-sonnet-4-5 → claude-3-haiku si falla)
- **2026-04-08**: Retry exponencial en webhook AppScript (3 intentos, delay 2s/4s/8s)
- **2026-04-08**: Webhook config via Script Properties (elimina IP hardcodeada)
- **2026-04-08**: Logging estructurado JSON + métricas en pipeline.py
- **2026-04-08**: Scoring siempre desde sheet (eliminado cálculo duplicado en Python)
