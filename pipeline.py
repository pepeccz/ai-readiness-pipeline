"""
AI Readiness Pipeline
Orquesta el flujo completo:
  1. Lee email de pepe@zanovix.com con subject "AIR-ASSESSMENT:"
  2. Extrae el JSON del assessment
  3. Llama al LLM enricher
  4. Genera el .docx con branding Zanovix
  5. Sube a Drive en la carpeta correcta
  6. Escribe los campos llm_* en el sheet
  7. Envía email de confirmación a pepe@zanovix.com

Ejecutado por OpenClaw cuando detecta un email de assessment.
"""

import os
import json
import subprocess
import sys
import requests
import time
import logging
from datetime import datetime
from enum import Enum


# Logging estructurado
class PipelineStep(Enum):
    START = "start"
    VERIFY_CODE = "verify_code"
    ENRICH_LLM = "enrich_llm"
    ENRICH_RECOMMENDATIONS = "enrich_recommendations"
    SCORING = "scoring"
    GENERATE_DOCX = "generate_docx"
    GENERATE_DECK = "generate_deck"
    UPLOAD_DRIVE = "upload_drive"
    WRITE_SHEET = "write_sheet"
    SEND_EMAIL = "send_email"
    UPDATE_NOTION = "update_notion"
    COMPLETE = "complete"
    ERROR = "error"


def log_step(
    step: PipelineStep, status: str, details: dict = None, duration_ms: int = None
):
    """Log estructurado JSON para observabilidad."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step.value,
        "status": status,
    }
    if duration_ms is not None:
        log_entry["duration_ms"] = duration_ms
    if details:
        log_entry.update(details)

    # Print como JSON para consumo por log agregators
    print(f"[LOG] {json.dumps(log_entry, ensure_ascii=False)}")


def log_metric(name: str, value, tags: dict = None):
    """Log de métrica individual."""
    metric = {
        "type": "metric",
        "name": name,
        "value": value,
        "timestamp": datetime.now().isoformat(),
    }
    if tags:
        metric["tags"] = tags
    print(f"[METRIC] {json.dumps(metric)}")


# Config de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
GENERATOR = os.path.join(SCRIPT_DIR, "report_generator.py")
ENRICHER = os.path.join(SCRIPT_DIR, "llm_enricher.py")
from config import settings

ANTHROPIC_API_KEY = settings.anthropic_api_key.get_secret_value()

# Legacy v1 config (only used by process_assessment, not v2)
SHEET_ID = ""
DRIVE_FOLDER = ""
OUTPUT_EMAIL = ""


def get_access_token() -> str:
    """Legacy: obtiene token de Google. Solo usado por process_assessment v1."""
    try:
        import google_client
        return google_client.get_access_token()
    except ImportError:
        raise RuntimeError("google_client not available — use process_assessment_v2")


def upload_to_drive(
    file_path: str,
    access_token: str,
    folder_id: str,
    company_name: str,
    mime: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
) -> dict:
    """Sube un archivo a Drive y devuelve {id, webViewLink}."""
    fname = os.path.basename(file_path)
    meta = {"name": fname, "parents": [folder_id]}
    boundary = "----MultipartBoundary"
    with open(file_path, "rb") as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
        + json.dumps(meta).encode()
        + b"\r\n"
        + f"--{boundary}\r\nContent-Type: {mime}\r\n\r\n".encode()
        + file_data
        + f"\r\n--{boundary}--".encode()
    )
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,webViewLink",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        data=body,
    )
    r.raise_for_status()
    return r.json()


def generate_deck(rec: dict, docx_path: str) -> str | None:
    """Genera el deck .pptx a partir del rec del assessment. Devuelve la ruta del archivo."""
    import tempfile, subprocess as sp

    DECK_SCRIPT = os.path.join(
        os.path.dirname(SCRIPT_DIR), "tools", "ai-readiness-deck", "generate-deck.mjs"
    )
    if not os.path.exists(DECK_SCRIPT):
        print(f"   [deck] Script no encontrado: {DECK_SCRIPT}")
        return None

    # Construir el JSON de datos para el deck
    def safe_list(v, default):
        return v if isinstance(v, list) and v else default

    nivel_map = {
        (0, 20): "Muy inicial",
        (21, 40): "Inicial",
        (41, 60): "En adopción",
        (61, 80): "Operativa",
        (81, 100): "Avanzada",
    }
    madurez = int(rec.get("maturity_score", 0) or 0)
    nivel = next(
        (v for (lo, hi), v in nivel_map.items() if lo <= madurez <= hi), "Inicial"
    )
    riesgo = int(rec.get("risk_score", 0) or 0)

    deck_data = {
        "empresa": rec.get("company_name", "Empresa"),
        "sector": rec.get("sector", "No especificado"),
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "assessment_id": rec.get("assessment_id", ""),
        "madurez": madurez,
        "nivel_madurez": nivel,
        "riesgo": riesgo,
        "coste_hora": 20,
        "hallazgos": safe_list(
            rec.get("llm_quick_wins"),
            [
                rec.get("llm_executive_summary", "Ver informe detallado"),
            ],
        )[:3],
        "costes": [
            {
                "x": p.get("proceso", p.get("area", f"Proceso {i + 1}")),
                "y": int(p.get("horas_semana", p.get("ahorro_horas", 5)) or 5),
            }
            for i, p in enumerate(
                safe_list(
                    rec.get("llm_processes_analyzed"),
                    [{"proceso": "Proceso manual", "horas_semana": 10}],
                )[:4]
            )
        ],
        "oportunidades": [
            {
                "problema": op.get("proceso", op.get("titulo", f"Área {i + 1}")),
                "solucion": op.get(
                    "solucion", op.get("descripcion", "Automatización con IA")
                ),
                "ahorro": op.get("ahorro", op.get("ahorro_estimado", "—")),
                "prioridad": op.get("prioridad", "Media"),
            }
            for i, op in enumerate(
                safe_list(
                    rec.get("llm_quick_wins"),
                    [
                        {
                            "proceso": "Ver informe",
                            "solucion": "Automatización IA",
                            "ahorro": "—",
                            "prioridad": "Alta",
                        }
                    ],
                )[:3]
            )
        ],
        "puntos_regulatorios": safe_list(
            rec.get("llm_regulatory_flags"),
            [
                "Revisar cumplimiento RGPD en tratamiento de datos",
                "Evaluar aplicación del AI Act según uso previsto",
            ],
        )[:2],
        "roadmap": safe_list(
            rec.get("llm_roadmap"),
            [
                {
                    "nombre": "Fase 1 — Quick Wins",
                    "plazo": "Semanas 1–4",
                    "descripcion": "Primeras automatizaciones de alto impacto",
                    "resultado": "Ahorro visible en 30 días",
                },
                {
                    "nombre": "Fase 2 — Integración",
                    "plazo": "Semanas 5–10",
                    "descripcion": "Conexión con sistemas existentes",
                    "resultado": "Reducción de carga operativa",
                },
                {
                    "nombre": "Fase 3 — Escala",
                    "plazo": "Semanas 11–16",
                    "descripcion": "IA en procesos clave + compliance",
                    "resultado": "ROI consolidado",
                },
            ],
        )[:3],
        "propuesta": {
            "servicio": "Plan de Implementación IA",
            "descripcion": rec.get(
                "llm_executive_summary",
                "Implementación progresiva de IA adaptada a las necesidades de la empresa.",
            )[:200],
            "precio": "—",
            "plazo": "8–16 semanas",
            "roi": "3–6 meses",
            "cta": "Contacta con Zanovix para diseñar tu plan personalizado · hola@zanovix.com",
        },
    }

    # Escribir JSON temporal
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(deck_data, f, ensure_ascii=False)
        json_path = f.name

    company_safe = (
        rec.get("company_name", "Assessment").replace(" ", "_").replace("/", "_")
    )
    deck_out = docx_path.replace(".docx", "_deck.pptx")

    try:
        result = sp.run(
            ["node", DECK_SCRIPT, "--input", json_path, "--output", deck_out],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"   [deck] Error: {result.stderr[:200]}")
            return None
        return deck_out
    except Exception as e:
        print(f"   [deck] Excepción: {e}")
        return None
    finally:
        try:
            os.unlink(json_path)
        except:
            pass


def write_llm_to_sheet(rec: dict, access_token: str):
    """Escribe los campos llm_* en report_output buscando el assessment_id."""
    assessment_id = rec.get("assessment_id", "")
    if not assessment_id:
        return

    # Read report_output to find the row
    r = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/report_output!A:A",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    r.raise_for_status()
    vals = r.json().get("values", [])
    row_num = None
    for i, row in enumerate(vals):
        if row and row[0] == assessment_id:
            row_num = i + 1
            break

    # Get headers
    rh = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/report_output!1:1",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    headers = rh.json().get("values", [[]])[0]

    if not row_num:
        print(
            f"Assessment ID {assessment_id} no encontrado en report_output; creando fila nueva"
        )
        row_values = [""] * len(headers)
        base_fields = {
            "assessment_id": rec.get("assessment_id", ""),
            "company_name": rec.get("company_name", ""),
            "access_code": rec.get("access_code", ""),
            "sector": rec.get("sector", ""),
            "employee_range": rec.get("employee_range", ""),
            # pts individuales (fuente canónica para breakdowns del informe)
            "pts_tools": rec.get("pts_tools", 0),
            "pts_automation": rec.get("pts_automation", 0),
            "pts_area_usage": rec.get("pts_area_usage", 0),
            "pts_governance": rec.get("pts_governance", 0),
            "pts_goal_clarity": rec.get("pts_goal_clarity", 0),
            "maturity_score": rec.get("maturity_score", ""),
            "maturity_level": rec.get("maturity_level", ""),
            "pts_data_risk": rec.get("pts_data_risk", 0),
            "pts_ai_personal_data": rec.get("pts_ai_personal_data", 0),
            "pts_dpa": rec.get("pts_dpa", 0),
            "pts_dpia": rec.get("pts_dpia", 0),
            "pts_automated_decisions": rec.get("pts_automated_decisions", 0),
            "pts_sector": rec.get("pts_sector", 0),
            "pts_incident": rec.get("pts_incident", 0),
            "risk_score": rec.get("risk_score", ""),
            "risk_level": rec.get("risk_level", ""),
            "deal_fit_score": rec.get("deal_fit_score", ""),
            "deal_fit_level": rec.get("deal_fit_level", ""),
            "top_gaps": rec.get("top_gaps", ""),
            "top_opportunities": rec.get("top_opportunities", ""),
            "recommended_next_step": rec.get("recommended_next_step", ""),
            "internal_summary": rec.get("internal_summary", ""),
            "llm_input_json": json.dumps(rec, ensure_ascii=False),
            "review_status": "pending",
            "last_updated": datetime.now().isoformat(),
        }
        for field, value in base_fields.items():
            if field in headers:
                row_values[headers.index(field)] = value
        append_resp = requests.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/report_output!A1:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"values": [row_values]},
        )
        append_resp.raise_for_status()
        updates = append_resp.json().get("updates", {})
        updated_range = updates.get("updatedRange", "")
        if updated_range:
            import re

            m = re.search(r"![A-Z]+(\d+):", updated_range)
            if m:
                row_num = int(m.group(1))
        if not row_num:
            r_retry = requests.get(
                f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/report_output!A:A",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r_retry.raise_for_status()
            vals_retry = r_retry.json().get("values", [])
            for i, row in enumerate(vals_retry):
                if row and row[0] == assessment_id:
                    row_num = i + 1
                    break
        if not row_num:
            print("No se pudo localizar la fila recién creada en report_output")
            return

    # Build update — todos los campos llm_* generados por el enricher
    # Campos de texto simple
    SIMPLE_LLM_FIELDS = [
        "llm_executive_summary",
        "llm_current_state",
        "llm_opportunities",
        "llm_final_recommendation",
        "llm_final_narrative",
        "llm_tools_list",
        "llm_next_step_proposal",
        "llm_risk_findings",
        "llm_roadmap_30_60_90",
    ]
    # Campos estructurados — se serializan como JSON string para el sheet
    STRUCTURED_LLM_FIELDS = [
        "llm_scoring_answers",
        "llm_inventory_table",
        "llm_risk_findings_structured",
        "llm_opportunity_matrix",
        "llm_economic_estimate",
        "llm_roadmap_structured",
        "llm_dependencies",
        "llm_tool_recommendations",
        "llm_followup_questions",
        "llm_ai_policy_draft",
        "llm_dpa_guidance",
    ]

    def _col_letter(idx_1based: int) -> str:
        """Convierte índice 1-based a letra(s) de columna de Sheets."""
        idx = idx_1based - 1
        if idx < 26:
            return chr(65 + idx)
        return chr(64 + idx // 26) + chr(65 + idx % 26)

    data = []
    for field in SIMPLE_LLM_FIELDS:
        value = rec.get(field, "")
        if field in headers and value:
            col = _col_letter(headers.index(field) + 1)
            data.append(
                {"range": f"report_output!{col}{row_num}", "values": [[str(value)]]}
            )

    for field in STRUCTURED_LLM_FIELDS:
        value = rec.get(field)
        if field in headers and value is not None:
            col = _col_letter(headers.index(field) + 1)
            serialized = (
                json.dumps(value, ensure_ascii=False)
                if not isinstance(value, str)
                else value
            )
            data.append(
                {"range": f"report_output!{col}{row_num}", "values": [[serialized]]}
            )

    # Actualizar también drive_url, deck_url y status
    for field, value in [
        ("review_status", "completed"),
        ("last_updated", datetime.now().isoformat()),
    ]:
        if field in headers:
            col = _col_letter(headers.index(field) + 1)
            data.append({"range": f"report_output!{col}{row_num}", "values": [[value]]})

    if data:
        r2 = requests.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"valueInputOption": "RAW", "data": data},
        )
        r2.raise_for_status()
        print(f"Sheet actualizado: {len(data)} campos llm_*")


def send_completion_email(rec: dict, drive_url: str, access_token: str):
    """Envía email de confirmación con el enlace al Doc."""
    company = rec.get("company_name", "Empresa")
    assessment_id = rec.get("assessment_id", "-")
    maturity = f"{rec.get('maturity_score', '-')} ({rec.get('maturity_level', '-')})"
    risk = f"{rec.get('risk_score', '-')} ({rec.get('risk_level', '-')})"
    priority = f"{rec.get('priority_score', '-')} ({rec.get('priority_level', '-')})"
    fit = f"{rec.get('deal_fit_score', '-')} ({rec.get('deal_fit_level', '-')})"
    next_step = rec.get("recommended_next_step", "-")

    subject = f"✅ Informe AI Readiness generado — {company}"
    body = f"""Hola Pepe,

El informe AI Readiness Assessment para {company} está listo.

── Resumen ──────────────────────────────
Assessment ID: {assessment_id}
Empresa: {company}

Madurez:        {maturity}
Riesgo:         {risk}
Prioridad:      {priority}
Encaje comercial: {fit}

Siguiente paso recomendado:
{next_step}

── Documento ───────────────────────────
{drive_url}

── Próximos pasos ──────────────────────
- Revisa el informe y ajusta si necesitas
- Agenda la sesión de discovery con el cliente
- Una vez confirmado: envía propuesta del Assessment Express

Natalia · Zanovix
"""
    success = google_client.gmail_send(to=OUTPUT_EMAIL, subject=subject, body_text=body)
    if success:
        print("Email de confirmación enviado")
    else:
        print("   ⚠ No se pudo enviar email de confirmación")


# Legacy Notion config (v1 only)
NOTION_ASS_DB = getattr(settings, "notion_assessments_db", "")
NOTION_CLI_DB = getattr(settings, "notion_clients_db", "")


def verify_access_code(code: str) -> dict | None:
    """Verifica el código ZNV-XXXX contra la BD Assessments de Notion."""
    if not code or "ZNV-" not in code.upper():
        return None
    notion_key = getattr(settings, "notion_api_key", None)
    notion_key = notion_key.get_secret_value() if notion_key else ""
    headers = {
        "Authorization": f"Bearer {notion_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    r = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_ASS_DB}/query",
        headers=headers,
        json={"page_size": 100},
    )
    if not r.ok:
        print(f"   [código] Error consultando Notion: {r.status_code}")
        return None
    for page in r.json().get("results", []):
        props = page.get("properties", {})
        rt = props.get("Codigo acceso", {}).get("rich_text", [])
        stored = rt[0]["plain_text"] if rt else ""
        if stored.upper() == code.upper().strip():
            # Obtener nombre empresa via relación Cliente
            empresa = ""
            rel = props.get("Cliente", {}).get("relation", [])
            if rel:
                r2 = requests.get(
                    f"https://api.notion.com/v1/pages/{rel[0]['id']}", headers=headers
                )
                if r2.ok:
                    t = (
                        r2.json()
                        .get("properties", {})
                        .get("Empresa", {})
                        .get("title", [])
                    )
                    empresa = t[0]["plain_text"] if t else ""
            nombre_prop = props.get("Nombre", {}).get("title", [])
            nombre = nombre_prop[0]["plain_text"] if nombre_prop else "—"
            return {
                "empresa": empresa,
                "assessment_nombre": nombre,
                "page_id": page["id"],
                "code": stored,
            }
    return None


def mark_assessment_completed(
    page_id: str,
    drive_url: str = None,
    deck_url: str = None,
    maturity_score: int = None,
    maturity_level: str = None,
    risk_score: int = None,
    risk_level: str = None,
):
    """Marca el assessment como completado en Notion y guarda los resultados."""
    notion_key = getattr(settings, "notion_api_key", None)
    notion_key = notion_key.get_secret_value() if notion_key else ""
    headers = {
        "Authorization": f"Bearer {notion_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    props = {
        "Estado": {"select": {"name": "Completado"}},
        "Fecha completado": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
    }
    if drive_url:
        props["Informe Word"] = {"url": drive_url}
    if deck_url:
        props["Informe Deck"] = {"url": deck_url}
    if maturity_score is not None:
        props["Madurez score"] = {"number": maturity_score}
    if maturity_level:
        props["Nivel madurez"] = {"select": {"name": maturity_level}}
    if risk_score is not None:
        props["Riesgo score"] = {"number": risk_score}
    if risk_level:
        props["Nivel riesgo"] = {"select": {"name": risk_level}}
    requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=headers,
        json={"properties": props},
    )


def process_assessment(json_str: str):
    """Función principal. Recibe el JSON string del assessment."""
    start_time = time.time()
    log_step(PipelineStep.START, "started", {"json_length": len(json_str)})

    print("── Pipeline iniciado ──────────────────────────────")
    rec = json.loads(json_str)

    # 0. Verificar código de acceso
    step_start = time.time()
    access_code = rec.get("access_code", rec.get("Codigo de acceso", ""))
    if access_code:
        print(f"0. Verificando código de acceso: {access_code}")
        notion_data = verify_access_code(access_code)
        if notion_data:
            print(f"   ✓ Código válido — empresa: {notion_data['empresa']}")
            if not rec.get("company_name"):
                rec["company_name"] = notion_data["empresa"]
            rec["_notion_page_id"] = notion_data["page_id"]
            log_step(
                PipelineStep.VERIFY_CODE,
                "success",
                {"found": True, "empresa": notion_data.get("empresa", "")},
                int((time.time() - step_start) * 1000),
            )
        else:
            print(
                f"   ⚠ Código no encontrado en CRM: {access_code} — continuando sin verificación"
            )
            log_step(
                PipelineStep.VERIFY_CODE,
                "not_found",
                {"code": access_code},
                int((time.time() - step_start) * 1000),
            )

    print(f"Assessment: {rec.get('assessment_id')} | {rec.get('company_name')}")
    log_metric(
        "assessment_start",
        1,
        {"assessment_id": rec.get("assessment_id"), "company": rec.get("company_name")},
    )

    # 1. Enriquecimiento LLM — genera todos los campos del informe en una sola llamada
    step_start = time.time()
    print("1. Enriqueciendo con LLM...")
    llm_fields_already = [k for k in rec if k.startswith("llm_") and rec[k]]
    if len(llm_fields_already) >= 6:
        # El JSON ya viene enriquecido (flujo legacy con subagente externo)
        print(
            f"   Campos LLM ya presentes ({len(llm_fields_already)}), omitiendo llamada LLM"
        )
        log_step(
            PipelineStep.ENRICH_LLM,
            "skipped",
            {"reason": "already_enriched", "fields_count": len(llm_fields_already)},
            int((time.time() - step_start) * 1000),
        )
    else:
        if ANTHROPIC_API_KEY:
            from llm_enricher import enrich_assessment

            rec = enrich_assessment(rec)
            llm_fields_new = [k for k in rec if k.startswith("llm_") and rec[k]]
            print(f"   Enricher OK → {len(llm_fields_new)} campos LLM generados")
            log_step(
                PipelineStep.ENRICH_LLM,
                "success",
                {"fields_generated": len(llm_fields_new)},
                int((time.time() - step_start) * 1000),
            )
        else:
            print(
                "   ⚠ ANTHROPIC_API_KEY no configurada — saltando enriquecimiento LLM"
            )
            log_step(
                PipelineStep.ENRICH_LLM,
                "skipped",
                {"reason": "no_api_key"},
                int((time.time() - step_start) * 1000),
            )

    # 1b. Enriquecimiento con recomendaciones inteligentes
    print("1b. Enriqueciendo con recomendaciones inteligentes...")
    step_start = time.time()
    try:
        from recommendation_enricher import enrich_recommendations

        rec = enrich_recommendations(rec)
        reco_count = len(rec.get("llm_tool_recommendations", []))
        questions_count = len(rec.get("llm_followup_questions", []))
        print(
            f"   Recomendaciones OK → {reco_count} herramientas, {questions_count} preguntas"
        )
        log_step(
            PipelineStep.ENRICH_RECOMMENDATIONS,
            "success",
            {
                "tools_recommended": reco_count,
                "followup_questions": questions_count,
                "has_policy_draft": bool(rec.get("llm_ai_policy_draft")),
                "has_dpa_guidance": bool(rec.get("llm_dpa_guidance")),
            },
            int((time.time() - step_start) * 1000),
        )
    except Exception as e:
        print(f"   ⚠ Recomendaciones: error ({e}), continuando sin ellas")
        log_step(
            PipelineStep.ENRICH_RECOMMENDATIONS,
            "error",
            {"error": str(e)},
            int((time.time() - step_start) * 1000),
        )

    # 2. Scoring engine: construir tablas trazables desde pts_* reales
    print("2. Calculando scoring trazable...")
    sys.path.insert(0, SCRIPT_DIR)
    from scoring_engine import enrich_with_scoring, fix_employee_range

    # Limpiar campos que pueden tener valores corruptos (fechas seriales de Sheets)
    rec["employee_range"] = fix_employee_range(rec.get("employee_range"))
    # Los llm_scoring_answers los generó el enricher — extraerlos para pasarlos al engine
    llm_answers = rec.pop("llm_scoring_answers", None)
    # Pasar sheet_id y account para que enrich_with_scoring lea pts_* desde analysis
    rec = enrich_with_scoring(
        rec, llm_answers, sheet_id=SHEET_ID
    )
    rec["llm_scoring_answers"] = (
        llm_answers  # restaurar para que se escriba en el sheet
    )
    print("   Scoring OK")

    # 3. Generar .docx
    print("3. Generando .docx...")
    from report_generator import generate_report

    docx_path = generate_report(rec)
    print(f"   Generado: {docx_path}")

    # 3. Obtener access token (necesario para Drive)
    print("3. Obteniendo credenciales...")
    access_token = get_access_token()

    # 4. Generar deck .pptx
    print("4. Generando deck de presentación...")
    deck_path = None
    deck_url = None
    try:
        deck_path = generate_deck(rec, docx_path)
        if deck_path:
            deck_result = upload_to_drive(
                deck_path,
                access_token,
                DRIVE_FOLDER,
                rec.get("company_name", ""),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
            deck_url = deck_result.get("webViewLink")
            print(f"   Deck: {deck_url}")
        else:
            print("   Deck: omitido (error en generación)")
    except Exception as e:
        print(f"   Deck: error ({e}), continuando...")

    # 5. Subir Word a Drive
    print("5. Subiendo Word a Drive...")
    drive_result = upload_to_drive(
        docx_path, access_token, DRIVE_FOLDER, rec.get("company_name", "")
    )
    drive_url = drive_result.get("webViewLink", "URL no disponible")
    print(f"   Drive: {drive_url}")

    # 6. Escribir llm_* en sheet
    print("6. Actualizando sheet...")
    write_llm_to_sheet(rec, access_token)

    # 7. Email de confirmación
    print("7. Enviando email de confirmación...")
    send_completion_email(rec, drive_url, access_token)

    # Limpiar
    try:
        os.unlink(docx_path)
    except Exception:
        pass

    # Marcar assessment como completado en Notion con todos los resultados
    notion_page = rec.get("_notion_page_id")
    if notion_page:
        try:
            mark_assessment_completed(
                notion_page,
                drive_url=drive_url,
                deck_url=deck_url,
                maturity_score=int(rec.get("maturity_score", 0) or 0),
                maturity_level=rec.get("maturity_level", ""),
                risk_score=int(rec.get("risk_score", 0) or 0),
                risk_level=rec.get("risk_level", ""),
            )
            print("   ✓ Notion: assessment completado con resultados")
        except Exception as e:
            print(f"   Notion: error actualizando ({e})")

    print("── Pipeline completado ────────────────────────────")

    # Logging estructurado de completion
    total_duration = int((time.time() - start_time) * 1000)
    log_step(
        PipelineStep.COMPLETE,
        "success",
        {
            "assessment_id": rec.get("assessment_id"),
            "company": rec.get("company_name"),
            "maturity_score": rec.get("maturity_score"),
            "risk_score": rec.get("risk_score"),
        },
        total_duration,
    )

    # Métricas finales
    log_metric(
        "pipeline_duration_ms",
        total_duration,
        {
            "assessment_id": rec.get("assessment_id"),
            "company": rec.get("company_name"),
        },
    )
    log_metric("pipeline_success", 1, {"assessment_id": rec.get("assessment_id")})

    return drive_url


# ─── V2: Self-hosted pipeline (no Google/Notion dependencies) ─────────────────


def map_form_to_rec(payload: dict) -> dict:
    """Transform web form payload to internal rec format expected by scoring + LLM."""
    import uuid

    rec = {}

    # Identity
    rec["assessment_id"] = "AIR-" + str(uuid.uuid4())[:8].upper()
    rec["company_name"] = payload.get("company_name", payload.get("contact_name", "Empresa"))
    rec["respondent_name_role"] = payload.get("contact_name", "")
    if payload.get("contact_role"):
        rec["respondent_name_role"] += f" — {payload['contact_role']}"
    rec["sector"] = payload.get("sector", "")
    rec["employee_range"] = payload.get("employee_range", "")
    rec["revenue_range"] = payload.get("revenue_range", "")
    rec["who_decides"] = payload.get("tech_decision_maker", "")

    # Tools and automation — scoring engine expects these as strings
    ai_tools = payload.get("ai_tools_used", [])
    rec["tools_used"] = ", ".join(ai_tools) if ai_tools else ""
    rec["chatbot"] = "Sí" if payload.get("has_chatbot") else "No"
    rec["chatbot_desc"] = payload.get("chatbot_desc", "")
    rec["custom_ai"] = "No"
    rec["custom_ai_desc"] = ""
    rec["auto_system"] = "Sí" if payload.get("has_automations") else "No"

    # Software stack
    software = payload.get("software_used", [])
    rec["sistemas_existentes"] = ", ".join(software) if software else ""

    # Customer service
    channels = payload.get("contact_channels", [])
    rec["contact_channels"] = ", ".join(channels) if channels else ""
    rec["daily_queries"] = payload.get("daily_queries", "")
    rec["support_team_desc"] = payload.get("support_team_desc", "")
    rec["top_repetitive_queries"] = payload.get("top_repetitive_queries", "")
    rec["avg_resolution_time"] = payload.get("avg_resolution_time", "")

    # Marketing and sales
    content_gen = payload.get("content_generation", [])
    rec["content_generation"] = ", ".join(content_gen) if content_gen else ""
    lead_acq = payload.get("lead_acquisition", [])
    rec["lead_acquisition"] = ", ".join(lead_acq) if lead_acq else ""
    rec["has_lead_tracking"] = "Sí" if payload.get("has_lead_tracking") else "No"
    rec["lead_tracking_desc"] = payload.get("lead_tracking_desc", "")
    rec["monthly_marketing_budget"] = payload.get("monthly_marketing_budget", "")

    # Operations — process to improve
    rec["process_to_improve"] = payload.get("most_time_consuming_process", "")
    rec["proceso_nombre"] = payload.get("most_time_consuming_process", "")
    rec["proceso_personas"] = payload.get("process_people_count", "")
    rec["proceso_horas"] = payload.get("process_hours_per_week", "")
    data_channels = payload.get("data_entry_channels", [])
    rec["proceso_dato_input"] = ", ".join(data_channels) if data_channels else ""
    pain_points = payload.get("process_pain_points", [])
    rec["proceso_falla"] = ", ".join(pain_points) if pain_points else ""
    rec["proceso_resultado_esperado"] = ""

    # Finance
    rec["invoicing_method"] = payload.get("invoicing_method", "")
    rec["admin_hours_per_week"] = payload.get("admin_hours_per_week", "")

    # HR
    rec["is_hiring"] = "Sí" if payload.get("is_hiring") else "No"
    rec["hiring_desc"] = payload.get("hiring_desc", "")
    rec["hr_management_method"] = payload.get("hr_management_method", "")
    rec["hr_hours_per_week"] = payload.get("hr_hours_per_week", "")

    # Compliance
    rec["datos_personales_ia"] = "Sí" if payload.get("collects_personal_data") else "No"
    rec["data_types"] = payload.get("personal_data_types", "")
    rec["data_in_ai"] = payload.get("knows_ai_gdpr", "No sé")
    rec["dpa"] = payload.get("has_dpa", "No sé qué es")
    rec["dpa_with_whom"] = payload.get("dpa_with_whom", "")
    rec["ai_act"] = "Sí, lo conozco" if payload.get("knows_ai_act") else "No lo conozco"
    rec["politica_ia"] = "Sí, documentada" if payload.get("has_ai_policy") else "No tenemos"
    rec["formacion_ia"] = ""
    rec["eipd"] = "No"
    rec["auto_decisions"] = "No"

    # Budget and priority
    rec["budget"] = payload.get("investment_budget", "")
    rec["proceso_urgencia"] = payload.get("urgency", "")
    rec["additional_context"] = payload.get("additional_notes", "")
    rec["main_pain"] = payload.get("most_time_consuming_process", "")
    rec["goals_12m"] = ""
    rec["hours_lost"] = ""
    rec["priority"] = "Alta" if "ahora" in payload.get("urgency", "").lower() else "Media"

    # Legacy area fields — default to "" (Sprint 1: 0 pts for pts_area_usage)
    for area in [
        "area_atencion", "area_marketing", "area_ventas", "area_rrhh",
        "area_operaciones", "area_finanzas", "area_producto",
    ]:
        rec[area] = ""

    return rec


def convert_to_pdf(docx_path: str) -> str | None:
    """Convert .docx to .pdf using LibreOffice headless. Returns PDF path or None."""
    try:
        output_dir = os.path.dirname(docx_path)
        result = subprocess.run(
            [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", output_dir, docx_path,
            ],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            pdf_path = docx_path.rsplit(".", 1)[0] + ".pdf"
            if os.path.exists(pdf_path):
                # Clean up the .docx
                try:
                    os.unlink(docx_path)
                except OSError:
                    pass
                return pdf_path
        print(f"   [pdf] LibreOffice error: {result.stderr[:200]}")
        return None
    except Exception as e:
        print(f"   [pdf] Conversión falló: {e}")
        return None


def process_assessment_v2(form_data: dict) -> str:
    """
    Self-hosted pipeline v2: Form → LLM → Scoring → Report → docx path.
    No Google, Notion, or email dependencies.
    Returns the path to the generated .docx file.
    """
    start_time = time.time()

    # 1. Map form data to internal rec format
    rec = map_form_to_rec(form_data)
    print(f"── Pipeline v2 iniciado: {rec['assessment_id']} | {rec['company_name']} ──")

    # 2. LLM enrichment
    print("1. Enriqueciendo con LLM...")
    step_start = time.time()
    from llm_enricher import enrich_assessment

    rec = enrich_assessment(rec)
    llm_count = len([k for k in rec if k.startswith("llm_") and rec[k]])
    print(f"   Enricher OK → {llm_count} campos LLM generados")
    log_step(
        PipelineStep.ENRICH_LLM, "success",
        {"fields_generated": llm_count},
        int((time.time() - step_start) * 1000),
    )

    # 3. Recommendation enrichment
    print("2. Enriqueciendo con recomendaciones...")
    step_start = time.time()
    try:
        from recommendation_enricher import enrich_recommendations

        rec = enrich_recommendations(rec)
        reco_count = len(rec.get("llm_tool_recommendations", []))
        questions_count = len(rec.get("llm_followup_questions", []))
        print(f"   Recomendaciones OK → {reco_count} herramientas, {questions_count} preguntas")
        log_step(
            PipelineStep.ENRICH_RECOMMENDATIONS, "success",
            {"tools_recommended": reco_count, "followup_questions": questions_count},
            int((time.time() - step_start) * 1000),
        )
    except Exception as e:
        print(f"   ⚠ Recomendaciones: error ({e}), continuando sin ellas")

    # 4. Scoring — NO sheet reads, purely from form answers
    print("3. Calculando scoring...")
    from scoring_engine import enrich_with_scoring, fix_employee_range

    rec["employee_range"] = fix_employee_range(rec.get("employee_range"))
    llm_answers = rec.pop("llm_scoring_answers", None)
    rec = enrich_with_scoring(rec, llm_answers, sheet_id=None)
    rec["llm_scoring_answers"] = llm_answers
    print("   Scoring OK")

    # 5. Generate .docx report
    print("4. Generando informe .docx...")
    from report_generator import generate_report

    docx_path = generate_report(rec)
    print(f"   Informe generado: {docx_path}")

    # 6. Convert to PDF
    print("5. Convirtiendo a PDF...")
    pdf_path = convert_to_pdf(docx_path)
    if pdf_path:
        print(f"   PDF generado: {pdf_path}")
    else:
        print("   ⚠ Conversión a PDF falló, entregando .docx")
        pdf_path = docx_path

    total_ms = int((time.time() - start_time) * 1000)
    print(f"── Pipeline v2 completado en {total_ms}ms ──")

    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 pipeline.py '{\"assessment_id\":...}'")
        sys.exit(1)
    result = process_assessment(sys.argv[1])
    print(f"Resultado: {result}")
