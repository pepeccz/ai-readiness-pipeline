"""
app/services/sessions/session_closing — Generates session 1 synthesis via LLM.

SessionClosingService.generate_synthesis():
  - Receives lead triage payload, block payloads, and block syntheses
  - Calls LLM (Sonnet) to produce structured synthesis: summary, key_insights,
    recommendations, hypothesis
  - Returns Session1SynthesisOutput Pydantic model (all fields Optional for resilience)

The LLM call is abstracted via _call_llm() for easy test mocking.
"""

from __future__ import annotations

import json
import textwrap
from typing import Optional

import structlog
from pydantic import BaseModel

from app.services.ai_analysis.json_extractor import JsonExtractionError, extract_json

logger = structlog.get_logger(__name__)


class Session1SynthesisOutput(BaseModel):
    """
    Structured output from the session 1 synthesis LLM call.

    All fields are Optional so partial LLM output doesn't cause a full failure.
    The schema deliberately omits legacy keys (preliminary_hypotheses, global_synthesis).
    """

    summary: Optional[str] = None
    key_insights: Optional[list[str]] = None
    recommendations: Optional[list[str]] = None
    hypothesis: Optional[str] = None


_SYSTEM_PROMPT = textwrap.dedent("""
    Sos un consultor senior de IA con 15 años de experiencia ayudando empresas a adoptar IA.
    Tu tarea es analizar las respuestas de un cliente a un cuestionario de madurez IA y
    producir una síntesis estratégica de la sesión 1.

    Reglas:
    - summary: resumen ejecutivo entre 600 y 1000 caracteres.
    - key_insights: lista de 3 a 5 insights clave, cada uno una oración concisa.
    - recommendations: lista de 2 a 4 recomendaciones accionables, en orden de prioridad.
    - hypothesis: hipótesis principal del consultor sobre el caso, en primera persona.
    - No especules más allá de los datos disponibles.
    - Respondé SOLO con JSON válido, sin texto adicional.

    Output schema (JSON):
    {
      "summary": "string (600-1000 chars)",
      "key_insights": ["insight 1", "insight 2", "insight 3"],
      "recommendations": ["recomendación 1", "recomendación 2"],
      "hypothesis": "hipótesis principal del consultor"
    }
""").strip()


class SessionClosingService:
    """Service for generating session 1 closing synthesis."""

    async def generate_synthesis(
        self,
        lead_triage_payload: dict,
        block_payloads: dict[str, dict],
        block_syntheses: dict[str, str],
    ) -> Session1SynthesisOutput:
        """
        Generate session 1 synthesis via LLM.

        Args:
            lead_triage_payload: Raw TRIAGE answers (PII scrubbed before sending).
            block_payloads: {block_id: payload} for submitted CORE blocks.
            block_syntheses: {block_id: synthesis_text} from completed BlockAnalysis rows.

        Returns:
            Session1SynthesisOutput with summary, key_insights, recommendations, hypothesis.

        Raises:
            ValueError: If LLM returns invalid JSON.
        """
        user_message = self._build_user_message(
            lead_triage_payload, block_payloads, block_syntheses
        )

        logger.info("session_closing_synthesis_started", blocks=list(block_payloads.keys()))

        response = await self._call_llm(_SYSTEM_PROMPT, user_message)
        raw_text = response.content[0].text.strip()

        try:
            data = extract_json(raw_text)
        except JsonExtractionError as exc:
            logger.error(
                "session_closing_llm_invalid_json",
                error=str(exc),
                raw_llm_output=raw_text,
            )
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        # Parse into typed output — all fields are Optional so partial output is safe
        output = Session1SynthesisOutput.model_validate(data)

        logger.info(
            "session_closing_synthesis_completed",
            has_insights=output.key_insights is not None,
        )

        return output

    def _build_user_message(
        self,
        lead_triage_payload: dict,
        block_payloads: dict[str, dict],
        block_syntheses: dict[str, str],
    ) -> str:
        """Build the user message for the LLM call."""
        parts = []

        if lead_triage_payload:
            parts.append("## TRIAGE respuestas del cliente")
            parts.append(json.dumps(lead_triage_payload, ensure_ascii=False, indent=2))

        if block_payloads:
            parts.append("\n## Respuestas por bloque CORE")
            for block_id, payload in block_payloads.items():
                parts.append(f"\n### {block_id}")
                parts.append(json.dumps(payload, ensure_ascii=False, indent=2))

        if block_syntheses:
            parts.append("\n## Síntesis por bloque (análisis IA)")
            for block_id, synthesis in block_syntheses.items():
                parts.append(f"\n### {block_id}")
                parts.append(synthesis)

        parts.append("\n## Tu tarea")
        parts.append(
            "Analizá toda la información y producí la síntesis global de sesión 1 "
            "según el schema JSON especificado en el sistema."
        )

        return "\n".join(parts)

    async def _call_llm(self, system_prompt: str, user_message: str):
        """
        Make the actual LLM call. Extracted for easy mocking in tests.

        Returns an Anthropic Message object.
        """
        from app.services.llm.client_factory import get_anthropic_client

        client = get_anthropic_client()
        return await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
