"""
app/services/ai_analysis/prompt_builder — Construye prompts con prompt caching.

`build(block_schema, payload, prev_analyses)` retorna la lista `messages` para
la Anthropic SDK con cache_control=ephemeral en system + schema (estables) y
sin cache_control en el user response (variable).

`_scrub_pii(value)` reemplaza nombre/email/teléfono en strings y dicts.
"""

from __future__ import annotations

import json
import re

SYSTEM_PROMPT = """Eres un consultor senior de transformación digital e inteligencia artificial.
Tu rol es analizar las respuestas de un cuestionario de madurez IA de una empresa y generar:

1. Una SÍNTESIS concisa (200-500 caracteres) del estado actual del bloque evaluado
2. CONTRADICCIONES detectadas entre respuestas (con severidad: low/med/high)
3. PREGUNTAS DE SEGUIMIENTO que el consultor debería explorar (con confianza 0-1 y prioridad high/med/low)
4. HIPÓTESIS PRELIMINAR (solo para bloque estratégico)
5. OUTPUTS ESPECÍFICOS del bloque (según el schema proporcionado)

REGLAS DURAS:
- Responde SIEMPRE en JSON válido siguiendo exactamente el schema indicado
- No incluyas información personal identificable en tus respuestas
- Confidence 0-1: usa valores reales basados en evidencia de las respuestas
- Sé específico y accionable, no genérico
- Máximo 3 follow_ups por bloque
- Foco en lo que el consultor necesita saber para avanzar"""

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"\+?\d{1,3}[\s.\-]?"          # optional country code (e.g., +34)
    r"(?:\(?\d{1,4}\)?[\s.\-]?)?"  # optional area code
    r"\d{2,4}[\s.\-]?\d{2,4}"      # main number segments
    r"(?:[\s.\-]?\d{2,4})?"        # optional trailing segment
)


def _scrub_pii(value: str | dict | list) -> str | dict | list:
    """
    Replace PII (email, phone) in text values with safe placeholders.

    Handles str, dict (values recursively), list (items recursively).
    """
    if isinstance(value, str):
        result = _EMAIL_RE.sub("[EMAIL]", value)
        result = _PHONE_RE.sub("[TEL]", result)
        return result
    if isinstance(value, dict):
        return {k: _scrub_pii(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_pii(item) for item in value]
    return value


class PromptBuilder:
    """Builds Anthropic SDK messages list with prompt caching."""

    def build(
        self,
        block_schema: dict,
        payload: dict,
        prev_analyses: list[dict],
    ) -> list[dict]:
        """
        Build messages list for Anthropic SDK.

        Returns:
            [{"role": "user", "content": [
                {text: system_prompt, cache_control: ephemeral},   # cached
                {text: schema_text,  cache_control: ephemeral},   # cached
                {text: responses},                                 # NOT cached
            ]}]
        """
        schema_text = self._format_schema(block_schema)
        responses_text = self._format_responses(payload, prev_analyses)

        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": schema_text,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": responses_text,
                    },
                ],
            }
        ]

    def _format_schema(self, block_schema: dict) -> str:
        block_id = block_schema.get("id", "unknown")
        title = block_schema.get("title", "")
        questions = block_schema.get("questions", [])

        lines = [
            f"# SCHEMA DEL BLOQUE: {block_id}",
            f"## Título: {title}",
            "",
            "## Preguntas del bloque:",
        ]
        for q in questions:
            lines.append(f"- [{q.get('id', '')}] {q.get('label', '')}")

        lines += [
            "",
            "## Output JSON esperado:",
            json.dumps({
                "synthesis": "string (200-500 chars)",
                "contradictions": [{"text": "string", "severity": "low|med|high"}],
                "follow_ups": [{"text": "string", "rationale": "string", "priority": "high|med|low", "confidence": "float 0-1"}],
                "preliminary_hypothesis": "string | null",
                "block_specific_outputs": {},
            }, ensure_ascii=False, indent=2),
        ]

        return "\n".join(lines)

    def _format_responses(self, payload: dict, prev_analyses: list[dict]) -> str:
        clean_payload = _scrub_pii(payload)

        lines = ["# RESPUESTAS DEL CLIENTE", ""]
        lines.append("## Bloque actual:")
        lines.append(json.dumps(clean_payload, ensure_ascii=False, indent=2))

        if prev_analyses:
            lines += ["", "## Síntesis de bloques previos (contexto):"]
            for analysis in prev_analyses:
                block_id = analysis.get("block_id", "unknown")
                synthesis = analysis.get("synthesis", "")
                lines.append(f"- **{block_id}**: {synthesis}")

        lines += ["", "Genera el JSON de análisis siguiendo exactamente el schema indicado."]
        return "\n".join(lines)
