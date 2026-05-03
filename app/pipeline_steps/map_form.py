"""
app/pipeline_steps/map_form — Form-payload → internal rec dict.

Extracted from pipeline.py `map_form_to_rec`. This is now the single source
of truth for how the public form payload is translated into the internal rec
format consumed by the LLM enricher, scoring engine, and report generator.

The legacy `pipeline.py` imports from here so behaviour is identical across
both paths (public form + admin re-runs).
"""

import uuid

import structlog

logger = structlog.get_logger(__name__)


def map_form_to_rec(payload: dict) -> dict:
    """Transform a web form payload into the internal rec format.

    The rec dict is the canonical internal representation consumed by every
    pipeline step (enrich_llm, enrich_recommendations, score, generate_pdf).

    Args:
        payload: Raw form submission dict (keys match the React wizard fields).

    Returns:
        rec: Internal rec dict ready for the enrichment + scoring steps.
             Includes a fresh `assessment_id` (AIR-XXXXXXXX) on every call.

    Notes:
        - List fields (ai_tools_used, software_used, …) are joined as
          comma-separated strings to match what the scoring engine expects.
        - Bool fields (has_chatbot, has_automations, …) are converted to
          "Sí" / "No" strings.
        - area_* legacy fields are defaulted to "" (0 pts_area_usage in Sprint 1).
    """
    rec: dict = {}

    # ── Identity ─────────────────────────────────────────────────────────────
    rec["assessment_id"] = "AIR-" + str(uuid.uuid4())[:8].upper()
    rec["company_name"] = payload.get("company_name", payload.get("contact_name", "Empresa"))
    rec["respondent_name_role"] = payload.get("contact_name", "")
    if payload.get("contact_role"):
        rec["respondent_name_role"] += f" — {payload['contact_role']}"
    rec["sector"] = payload.get("sector", "")
    rec["employee_range"] = payload.get("employee_range", "")
    rec["revenue_range"] = payload.get("revenue_range", "")
    rec["who_decides"] = payload.get("tech_decision_maker", "")

    # ── Tools and automation ──────────────────────────────────────────────────
    ai_tools = payload.get("ai_tools_used", [])
    rec["tools_used"] = ", ".join(ai_tools) if ai_tools else ""
    rec["chatbot"] = "Sí" if payload.get("has_chatbot") else "No"
    rec["chatbot_desc"] = payload.get("chatbot_desc", "")
    rec["custom_ai"] = "No"
    rec["custom_ai_desc"] = ""
    rec["auto_system"] = "Sí" if payload.get("has_automations") else "No"

    # ── Software stack ────────────────────────────────────────────────────────
    software = payload.get("software_used", [])
    rec["sistemas_existentes"] = ", ".join(software) if software else ""

    # ── Customer service ─────────────────────────────────────────────────────
    channels = payload.get("contact_channels", [])
    rec["contact_channels"] = ", ".join(channels) if channels else ""
    rec["daily_queries"] = payload.get("daily_queries", "")
    rec["support_team_desc"] = payload.get("support_team_desc", "")
    rec["top_repetitive_queries"] = payload.get("top_repetitive_queries", "")
    rec["avg_resolution_time"] = payload.get("avg_resolution_time", "")

    # ── Marketing and sales ───────────────────────────────────────────────────
    content_gen = payload.get("content_generation", [])
    rec["content_generation"] = ", ".join(content_gen) if content_gen else ""
    lead_acq = payload.get("lead_acquisition", [])
    rec["lead_acquisition"] = ", ".join(lead_acq) if lead_acq else ""
    rec["has_lead_tracking"] = "Sí" if payload.get("has_lead_tracking") else "No"
    rec["lead_tracking_desc"] = payload.get("lead_tracking_desc", "")
    rec["monthly_marketing_budget"] = payload.get("monthly_marketing_budget", "")

    # ── Operations — process to improve ──────────────────────────────────────
    rec["process_to_improve"] = payload.get("most_time_consuming_process", "")
    rec["proceso_nombre"] = payload.get("most_time_consuming_process", "")
    rec["proceso_personas"] = payload.get("process_people_count", "")
    rec["proceso_horas"] = payload.get("process_hours_per_week", "")
    data_channels = payload.get("data_entry_channels", [])
    rec["proceso_dato_input"] = ", ".join(data_channels) if data_channels else ""
    pain_points = payload.get("process_pain_points", [])
    rec["proceso_falla"] = ", ".join(pain_points) if pain_points else ""
    rec["proceso_resultado_esperado"] = ""

    # ── Finance ──────────────────────────────────────────────────────────────
    rec["invoicing_method"] = payload.get("invoicing_method", "")
    rec["admin_hours_per_week"] = payload.get("admin_hours_per_week", "")

    # ── HR ────────────────────────────────────────────────────────────────────
    rec["is_hiring"] = "Sí" if payload.get("is_hiring") else "No"
    rec["hiring_desc"] = payload.get("hiring_desc", "")
    rec["hr_management_method"] = payload.get("hr_management_method", "")
    rec["hr_hours_per_week"] = payload.get("hr_hours_per_week", "")

    # ── Compliance ───────────────────────────────────────────────────────────
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

    # ── Budget and priority ───────────────────────────────────────────────────
    rec["budget"] = payload.get("investment_budget", "")
    rec["proceso_urgencia"] = payload.get("urgency", "")
    rec["additional_context"] = payload.get("additional_notes", "")
    rec["main_pain"] = payload.get("most_time_consuming_process", "")
    rec["goals_12m"] = ""
    rec["hours_lost"] = ""
    rec["priority"] = "Alta" if "ahora" in payload.get("urgency", "").lower() else "Media"

    # ── Legacy area fields (Sprint 1: 0 pts_area_usage) ──────────────────────
    for area in [
        "area_atencion",
        "area_marketing",
        "area_ventas",
        "area_rrhh",
        "area_operaciones",
        "area_finanzas",
        "area_producto",
    ]:
        rec[area] = ""

    logger.debug(
        "map_form_to_rec_done",
        assessment_id=rec["assessment_id"],
        company=rec["company_name"],
    )
    return rec
