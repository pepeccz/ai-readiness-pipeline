"""
AI Readiness Assessment - Recommendation Enricher
Genera recomendaciones inteligentes de herramientas, preguntas de profundización,
borrador de política de IA y guía DPA.

Usa una llamada LLM separada del enricher principal.
Carga tools_catalog.md como contexto para las recomendaciones.
Degradación graceful: si falla, devuelve rec sin cambios.
"""

import os
import json
from llm_client import call_llm, extract_json, ANTHROPIC_API_KEY

# --- Catalog loading ---
_CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools_catalog.md")
_tools_catalog: str | None = None


def _get_catalog() -> str:
    """Load tools catalog from disk. Cached after first read."""
    global _tools_catalog
    if _tools_catalog is None:
        with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
            _tools_catalog = f.read()
    return _tools_catalog


SYSTEM_PROMPT_RECO = """Eres un consultor senior de IA de Zanovix especializado en recomendar
herramientas y estrategias de implementación para PYMEs españolas.

Tu trabajo es analizar el perfil del cliente y generar:
1. Recomendaciones CONCRETAS de herramientas del catálogo proporcionado
2. Preguntas de profundización para áreas donde falta contexto
3. Un borrador de política de IA interna personalizada
4. Guía DPA para las herramientas recomendadas

REGLAS CRÍTICAS:
1. Solo recomienda herramientas que aparezcan en el CATÁLOGO proporcionado. No inventes herramientas.
2. Usa confidence "high" cuando los datos del formulario confirman directamente la necesidad.
   Usa "medium" cuando infieres la necesidad a partir del contexto.
   NUNCA incluyas recomendaciones con confidence baja — genera una pregunta de profundización en su lugar.
3. Las preguntas de profundización son SOLO para áreas donde NO puedes hacer una recomendación segura.
   Si ya recomendaste herramientas con confidence "high" para un área, NO generes preguntas para esa área.
4. La política de IA debe adaptarse al sector, tamaño y perfil de riesgo del cliente.
5. La guía DPA solo aplica a herramientas que procesan datos personales (requires_dpa: yes en el catálogo).
6. Idioma: español. Tono ejecutivo, directo.
7. Conecta SIEMPRE con los datos reales del formulario: proceso declarado, dolor, canal, sector."""

RECOMMENDATION_PROMPT = """Analiza el siguiente assessment y genera recomendaciones personalizadas.
Devuelve EXCLUSIVAMENTE un JSON válido sin texto adicional.

DATOS DEL ASSESSMENT:
{json_data}

CAMPOS A GENERAR:

"llm_tool_recommendations": array de objetos. Cada uno con:
  - "tool": nombre EXACTO del catálogo
  - "area": área de negocio (atención|marketing|ventas|rrhh|operaciones|finanzas|producto|transversal)
  - "problem_solved": problema específico que resuelve para ESTE cliente
  - "confidence": "high" o "medium" (nunca "low")
  - "integration_approach": 1-2 frases sobre cómo integrar
  - "estimated_cost": rango de coste del catálogo
  - "priority": 1 (inmediata), 2 (corto plazo), 3 (medio plazo)
  - "why_this_tool": por qué esta herramienta y no otra, específico al contexto del cliente
Incluye entre 3 y 8 recomendaciones. Ordena por prioridad.

"llm_followup_questions": array de objetos. SOLO para áreas con datos insuficientes.
  - "area": área con datos insuficientes
  - "question": pregunta específica para este cliente
  - "why_needed": qué información falta
  - "what_it_unlocks": qué recomendaciones se podrían hacer con la respuesta
Puede ser vacío [] si hay suficientes datos para todo.

"llm_ai_policy_draft": objeto con el borrador de política. Claves:
  - "scope": a quién aplica y qué sistemas cubre
  - "permitted_uses": array de strings — usos permitidos de IA en esta empresa
  - "prohibited_uses": array de strings — usos prohibidos
  - "data_handling": párrafo sobre tratamiento de datos con IA
  - "human_oversight": requisitos de supervisión humana
  - "incident_protocol": qué hacer si hay un incidente con IA
  - "training_requirements": formación necesaria para el personal
  - "review_cadence": cada cuánto se revisa la política (ej: "Semestral")
Personaliza según sector, herramientas recomendadas y nivel de riesgo.

"llm_dpa_guidance": array de objetos. Uno por herramienta que necesita DPA.
  - "tool": nombre de la herramienta
  - "provider": proveedor
  - "data_types_processed": array de tipos de datos que procesará para ESTE cliente
  - "key_clauses_needed": array de cláusulas DPA necesarias
  - "risk_level": "high" | "medium" | "low"
  - "action_required": siguiente paso concreto
Puede ser vacío [] si ninguna herramienta necesita DPA.

Devuelve el JSON completo. Sin texto fuera del JSON."""


def enrich_recommendations(rec: dict) -> dict:
    """
    Generate 4 recommendation fields via LLM.
    Returns rec dict with new llm_* fields added.
    On failure, returns rec with empty defaults (never raises).
    """
    empty_defaults = {
        "llm_tool_recommendations": [],
        "llm_followup_questions": [],
        "llm_ai_policy_draft": {},
        "llm_dpa_guidance": [],
    }

    # Check if recommendations already present
    existing_recs = rec.get("llm_tool_recommendations", [])
    if isinstance(existing_recs, list) and len(existing_recs) > 0:
        print("   [recommender] Recomendaciones ya presentes, omitiendo")
        return rec

    if not ANTHROPIC_API_KEY:
        print("   [recommender] ANTHROPIC_API_KEY no configurada, omitiendo")
        return {**rec, **empty_defaults}

    try:
        # Load catalog
        catalog = _get_catalog()

        # Filter rec for LLM input — keep only relevant fields
        keys_to_keep = {
            "company_name", "sector", "employee_range", "budget",
            "tools_used", "chatbot", "chatbot_desc", "custom_ai", "custom_ai_desc",
            "auto_system", "sistemas_existentes", "who_decides",
            "politica_ia", "formacion_ia", "ai_act",
            "dpa", "dpia", "datos_personales_ia", "automated_decisions",
            "maturity_score", "maturity_level", "risk_score", "risk_level",
        }
        rec_for_llm = {}
        for k, v in rec.items():
            if k in keys_to_keep:
                rec_for_llm[k] = v
            elif k.startswith("area_") or k.startswith("proceso_") or k.startswith("pts_"):
                rec_for_llm[k] = v

        json_data_str = json.dumps(rec_for_llm, ensure_ascii=False, indent=2)
        prompt = RECOMMENDATION_PROMPT.replace("{json_data}", json_data_str)

        # System blocks with caching — role prompt + catalog both cached
        system_blocks = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT_RECO,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": f"CATÁLOGO DE HERRAMIENTAS:\n{catalog}",
                "cache_control": {"type": "ephemeral"},
            },
        ]

        raw = call_llm(
            system_blocks=system_blocks,
            user_content=prompt,
            temperature=0.2,
            max_tokens=6000,
            max_tokens_fallback=4000,
        )

        llm_fields = extract_json(raw)

        # Map response keys to llm_* prefixed keys
        result = {**rec}
        result["llm_tool_recommendations"] = llm_fields.get(
            "llm_tool_recommendations", llm_fields.get("tool_recommendations", [])
        )
        result["llm_followup_questions"] = llm_fields.get(
            "llm_followup_questions", llm_fields.get("followup_questions", [])
        )
        result["llm_ai_policy_draft"] = llm_fields.get(
            "llm_ai_policy_draft", llm_fields.get("ai_policy_draft", {})
        )
        result["llm_dpa_guidance"] = llm_fields.get(
            "llm_dpa_guidance", llm_fields.get("dpa_guidance", [])
        )

        # Validate tool recommendations exist in catalog
        if result["llm_tool_recommendations"]:
            validated = []
            for tool_rec in result["llm_tool_recommendations"]:
                tool_name = tool_rec.get("tool", "")
                if tool_name.lower() in catalog.lower():
                    validated.append(tool_rec)
                else:
                    print(
                        f"   [recommender] ⚠ Herramienta no encontrada en catálogo: {tool_name}"
                    )
            result["llm_tool_recommendations"] = validated

        return result

    except Exception as e:
        print(f"   [recommender] Error: {e}, devolviendo rec sin campos de recomendación")
        return {**rec, **empty_defaults}


if __name__ == "__main__":
    import sys

    rec = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = enrich_recommendations(rec)
    for key in ["llm_tool_recommendations", "llm_followup_questions", "llm_ai_policy_draft", "llm_dpa_guidance"]:
        print(f"\n{key}:")
        print(json.dumps(result.get(key, "NOT SET"), ensure_ascii=False, indent=2))
