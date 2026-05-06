"""
app/services/sessions/session_closing — Generates session 1 synthesis via LLM.

SessionClosingService.generate_synthesis():
  - Receives lead triage payload, block payloads, and block syntheses
  - Calls LLM (Sonnet) to produce global synthesis + 3 preliminary hypotheses
  - Returns structured dict with global_synthesis, preliminary_hypotheses, activated_branches

The LLM call is abstracted via _call_llm() for easy test mocking.
"""

from __future__ import annotations

import json
import textwrap

import structlog

from app.services.ai_analysis.json_extractor import JsonExtractionError, extract_json

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = textwrap.dedent("""
    Sos un consultor senior de IA con 15 años de experiencia ayudando empresas a adoptar IA.
    Tu tarea es analizar las respuestas de un cliente a un cuestionario de madurez IA y
    producir una síntesis global estratégica de la sesión 1.

    Reglas:
    - La síntesis global debe tener entre 600 y 1000 caracteres.
    - Las hipótesis preliminares son 3, numeradas, en primera persona del consultor.
    - Los branches activados son strings exactamente como aparecen en el campo activated_branches.
    - No especules más allá de los datos disponibles.
    - Respondé SOLO con JSON válido, sin texto adicional.

    Output schema (JSON):
    {
      "global_synthesis": "string (600-1000 chars)",
      "preliminary_hypotheses": ["hypothesis 1", "hypothesis 2", "hypothesis 3"],
      "activated_branches": ["branch_id_1", ...]
    }
""").strip()


class SessionClosingService:
    """Service for generating session 1 closing synthesis."""

    async def generate_synthesis(
        self,
        lead_triage_payload: dict,
        block_payloads: dict[str, dict],
        block_syntheses: dict[str, str],
    ) -> dict:
        """
        Generate global synthesis + 3 hypotheses + activated branches via LLM.

        Args:
            lead_triage_payload: Raw TRIAGE answers (PII scrubbed before sending).
            block_payloads: {block_id: payload} for submitted CORE blocks.
            block_syntheses: {block_id: synthesis_text} from completed BlockAnalysis rows.

        Returns:
            Dict with keys: global_synthesis, preliminary_hypotheses, activated_branches.

        Raises:
            ValueError: If LLM returns invalid JSON or missing required fields.
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

        # Validate required fields
        required = {"global_synthesis", "preliminary_hypotheses", "activated_branches"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"LLM output missing required fields: {missing}")

        if not isinstance(data["preliminary_hypotheses"], list):
            raise ValueError("preliminary_hypotheses must be a list")

        logger.info(
            "session_closing_synthesis_completed",
            activated_branches=data.get("activated_branches", []),
        )

        return data

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
        import anthropic
        from config import settings

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
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
