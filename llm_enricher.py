"""
AI Readiness Assessment - LLM Enricher (v3 — Anthropic SDK)
Genera TODOS los campos del informe en una sola llamada LLM.
Incluye tanto campos de texto simple como todos los campos estructurados
(inventory, scoring_answers, risk_findings, opportunity_matrix,
economic_estimate, roadmap_structured, dependencies, next_step).

Usa Anthropic SDK directamente con prompt caching para el system prompt.
"""

import json
from llm_client import call_llm, extract_json

SYSTEM_PROMPT = """Eres un consultor senior de IA especializado en PYMEs españolas, trabajando para Zanovix.
Tu trabajo es generar el contenido completo de un informe AI Readiness Assessment profesional.

PRINCIPIOS NO NEGOCIABLES:
1. Distingue siempre entre CONFIRMADO / INDICIO / RECOMENDABLE en los hallazgos legales.
2. Precisión legal: chatbot sin aviso de IA → AI Act art. 50. Sin DPA → RGPD art. 28. EIPD → RGPD arts. 9 y 35. NUNCA llamar "alto riesgo" a un chatbot comercial genérico.
3. ROI siempre calculado: proceso_personas × proceso_horas (por persona) × semanas × coste_hora × % automatizable. proceso_horas es POR PERSONA, no total del equipo.
4. Inversión coherente: usa UN SOLO rango de inversión en todo el documento. El que pongas en llm_economic_estimate es el que debe aparecer también en llm_final_recommendation. Sin contradicciones.
5. Budget declarado: "Inversión estimada implementación" debe estar DENTRO del budget declarado por el cliente. No recortes el techo.
6. No menciones deal_fit_score ni deal_fit_level — son datos internos de Zanovix.
7. Tono: directo, ejecutivo, sin relleno. El lector es un gerente o CEO de PYME.
8. Idioma: español. No uses anglicismos innecesarios."""

FULL_REPORT_PROMPT = """Genera el contenido completo del informe para este assessment.
Devuelve EXCLUSIVAMENTE un JSON válido sin texto adicional fuera del JSON.

DATOS DEL ASSESSMENT:
{json_data}

CAMPOS A GENERAR (devuelve TODOS, en este orden):

=== TEXTOS SIMPLES ===

"llm_executive_summary": 3-4 frases. Estado actual, score de madurez y riesgo contextualizado, riesgo principal en lenguaje de negocio, siguiente paso concreto. No uses "discovery call" como cierre — termina en una decisión ejecutiva.

"llm_current_state": 3-5 frases. Cómo usa la IA hoy, qué herramientas, qué proceso tiene el mayor peso operativo, qué falta en términos de gobierno y compliance. Menciona sistemas_existentes si los hay.

"llm_opportunities": 3-4 frases. Cuantifica el ROI: proceso_personas × proceso_horas (POR PERSONA) × 50 semanas × coste_hora (12-15€) × % automatizable (40-60%). Conecta con el dolor declarado (proceso_falla) y el objetivo (proceso_resultado_esperado).

"llm_final_recommendation": 1-2 frases. Recomendación ejecutiva con tecnología concreta, inversión (MISMA cifra que en llm_economic_estimate) y plazo. Termina en acción, no en llamada.

"llm_final_narrative": 2-3 frases. Cierre humano. Por qué Zanovix es el socio adecuado.
IMPORTANTE: NO inventes experiencia previa con el sector del cliente ni afirmes haber trabajado con empresas similares si no hay datos que lo confirmen. Habla de capacidades reales: implementación de asistentes WhatsApp, compliance RGPD/AI Act, automatización para PYMEs. Conecta con el perfil específico del cliente (canal, proceso, riesgo identificado).

"llm_tools_list": string. Lista de herramientas declaradas separadas por coma.

"llm_next_step_proposal": 2-3 frases. Sesión de discovery de 90 min, qué se definiría (arquitectura técnica, plan compliance, FAQs), cómo contactar (hola@zanovix.com). Si who_decides != respondent_name_role, mencionar que es clave incluir a la persona decisora.

=== CAMPOS ESTRUCTURADOS ===

"llm_scoring_answers": objeto con texto descriptivo de la respuesta del cliente para cada criterio.
IMPORTANTE: los números los calcula el sistema — tú solo pones el texto que explica QUÉ respondió el cliente.
Claves exactas: pts_tools, pts_automation, pts_area_usage, pts_governance, pts_goal_clarity, pts_data_risk, pts_ai_personal_data, pts_dpa, pts_dpia, pts_automated_decisions, pts_sector, pts_incident.
Para pts_dpia: describe lo que realmente contestó el cliente (ej: "No han realizado EIPD ni conocen el concepto"), independientemente de la puntuación calculada.

"llm_inventory_table": array de arrays [herramienta, uso_declarado, canal, datos_que_toca, avisa_de_ia].
Una fila por herramienta/sistema. Canal: "Interno" para uso interno, "WhatsApp/Web/Email" para cliente-facing.
avisa_de_ia: "Sí", "No", "N/A (interno)".

"llm_risk_findings_structured": array de objetos con campos level, title, body, marco, impacto.
- level: "CONFIRMADO" si la respuesta lo dice explícitamente, "INDICIO" si hay indicios pero falta confirmación, "RECOMENDABLE" si es buena práctica sin evidencia de incumplimiento.
- marco: referencia legal exacta (ej: "RGPD art. 28 — Encargado del tratamiento").
- impacto: consecuencia concreta si no se actúa.
Ordenar: CONFIRMADO primero, luego INDICIO, luego RECOMENDABLE.

"llm_opportunity_matrix": array de arrays [iniciativa, impacto, complejidad, riesgo_si_no_actuas, prioridad].
4-6 filas. Prioridad: "1 - Inmediata", "2 - Corto plazo", "3 - Medio plazo". Ordenar por prioridad ascendente.

"llm_economic_estimate": objeto/dict con el cálculo económico. REGLAS:
- Calcula correctamente: proceso_personas (nº personas) × proceso_horas (horas/semana/persona) × 50 semanas × coste_hora × % automatizable.
- "Inversión estimada implementación": DEBE estar dentro del budget declarado (campo budget).
- Esta cifra de inversión DEBE SER IDÉNTICA a la que uses en llm_final_recommendation.
- Incluye siempre una fila "Nota" con supuestos explícitos.

"llm_roadmap_structured": array de 3 objetos {"label": "30 días", "objetivo": "...", "acciones": [...], "responsable": "..."}.
- Acciones concretas y específicas para este cliente (no genéricas).
- Si hay proceso_urgencia (ej: temporada alta), el roadmap debe estar diseñado para que el sistema esté operativo antes de esa fecha.
- Responsable: "Zanovix (X) / Cliente (Y)".

"llm_dependencies": array de 5-7 strings. Dependencias y límites reales para este cliente específico.
Incluir siempre al final: "Este informe no constituye asesoramiento jurídico formal. Las referencias normativas son orientativas."

Devuelve el JSON completo. Sin texto fuera del JSON."""


def enrich_assessment(rec: dict) -> dict:
    """
    Genera TODOS los campos LLM del informe en una sola llamada.
    Devuelve el record enriquecido.
    Intenta primero con modelo primario, hace fallback a haiku si falla.
    """
    # Excluir campos voluminosos que no aportan contexto al LLM
    rec_for_llm = {
        k: v
        for k, v in rec.items()
        if k
        not in (
            "llm_input_json",
            "llm_maturity_breakdown",
            "llm_risk_breakdown",
            "_notion_page_id",
            "employee_range",
        )
    }

    json_data_str = json.dumps(rec_for_llm, ensure_ascii=False, indent=2)
    prompt = FULL_REPORT_PROMPT.replace("{json_data}", json_data_str)

    # System prompt with cache_control for prompt caching
    system_blocks = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    raw = call_llm(
        system_blocks=system_blocks,
        user_content=prompt,
        temperature=0.3,
        max_tokens=8000,
        max_tokens_fallback=6000,
    )

    llm_fields = extract_json(raw)

    # Validar campos críticos mínimos
    required = [
        "llm_executive_summary",
        "llm_opportunities",
        "llm_final_recommendation",
        "llm_scoring_answers",
        "llm_risk_findings_structured",
        "llm_economic_estimate",
        "llm_roadmap_structured",
    ]
    missing = [f for f in required if f not in llm_fields]
    if missing:
        print(f"   [enricher] ⚠ Campos faltantes: {missing}")

    # Derivar alias de texto plano desde versiones estructuradas
    if "llm_roadmap_30_60_90" not in llm_fields:
        roadmap = llm_fields.get("llm_roadmap_structured", [])
        if roadmap:
            parts = []
            for phase in roadmap:
                label = phase.get("label", "")
                objetivo = phase.get("objetivo", "")
                acciones = phase.get("acciones", [])
                text = f"{label}: {objetivo}. " + " ".join(acciones[:2])
                parts.append(text)
            llm_fields["llm_roadmap_30_60_90"] = "\n".join(parts)

    if "llm_risk_findings" not in llm_fields:
        findings = llm_fields.get("llm_risk_findings_structured", [])
        if findings:
            parts = [
                f"[{f.get('level', '?')}] {f.get('title', '')}: {f.get('body', '')[:150]}"
                for f in findings[:3]
            ]
            llm_fields["llm_risk_findings"] = " | ".join(parts)

    # Normalizar llm_economic_estimate
    econ = llm_fields.get("llm_economic_estimate")
    if isinstance(econ, dict) and "concepto" in econ and "valor" in econ:
        keys = econ["concepto"]
        values = econ["valor"]
        if isinstance(keys, list) and isinstance(values, list):
            llm_fields["llm_economic_estimate"] = {k: v for k, v in zip(keys, values)}

    enriched = {**rec, **llm_fields}
    return enriched


if __name__ == "__main__":
    import sys

    rec = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = enrich_assessment(rec)
    print(json.dumps(result, ensure_ascii=False, indent=2))
