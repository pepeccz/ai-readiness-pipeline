"""
app/services/sessions/session_closing — Generates session 1 synthesis via LLM.

SessionClosingService.generate_synthesis():
  - Receives lead triage payload, block payloads, and block syntheses
  - Calls LLM (Sonnet) to produce structured synthesis via Session1SynthesisOutput schema
  - Returns Session1SynthesisOutput Pydantic model (all fields Optional for resilience)

The LLM call is abstracted via _call_llm() for easy test mocking.

Changes (pdf-export-and-editor):
  - Session1SynthesisOutput extracted to synthesis_schema.py
  - _SYSTEM_PROMPT now includes Zanovix catalog (loaded at import)
  - max_tokens bumped 1500 → 3000
"""

from __future__ import annotations

import json
import textwrap
from typing import Optional

import structlog

from app.services.ai_analysis.json_extractor import JsonExtractionError, extract_json
# Re-exported for backward compatibility with existing imports
from app.services.sessions.synthesis_schema import Session1SynthesisOutput  # noqa: F401
from app.services.synthesis.catalog import get_catalog

logger = structlog.get_logger(__name__)


def _build_system_prompt() -> str:
    """Build the system prompt, injecting the Zanovix services catalog."""
    catalog = get_catalog()

    catalog_lines = []
    for svc in catalog:
        catalog_lines.append(f"  - {svc.key}: {svc.nombre}")
        catalog_lines.append(f"    {svc.descripcion.strip()}")
        if svc.nota_priorizacion:
            catalog_lines.append(f"    Nota: {svc.nota_priorizacion}")

    catalog_block = "\n".join(catalog_lines)

    return textwrap.dedent(f"""
        Eres un consultor senior de IA con 15 años de experiencia ayudando empresas a adoptar IA.
        Tu tarea es analizar las respuestas de un cliente a un cuestionario de madurez IA y
        producir una síntesis estratégica de la sesión 1.

        ## Servicios Zanovix disponibles

        Los siguientes son los servicios que Zanovix puede recomendar al cliente.
        Cuando una recomendación se alinee con uno de estos servicios, usa su clave en el campo
        related_service. Valores válidos: diagnostico_profundo, desarrollo_acompanamiento,
        formacion_personalizada. Usa null cuando ningún servicio aplique.
        Prefiere formacion_personalizada cuando aplique (mejor relación coste/impacto).

{catalog_block}

        ## Reglas de output

        - summary: resumen ejecutivo entre 600 y 1000 caracteres.
        - key_insights: lista de 3 a 5 insights clave, cada uno una oración concisa.
        - recommendations: lista de 2 a 4 recomendaciones accionables, en orden de prioridad.
          Cada recomendación tiene: text (string), impact (alto/medio/bajo o null),
          effort (alto/medio/bajo o null), related_service (clave del servicio Zanovix o null).
        - roadmap: objeto con claves d30, d60, d90. Cada una es una lista de strings.
        - next_steps: lista de 2 a 4 próximos pasos concretos.
        - hypothesis: hipótesis principal del consultor sobre el caso, en primera persona.
        - No especules más allá de los datos disponibles.
        - Responde SOLO con JSON válido, sin texto adicional.

        Output schema (JSON):
        {{
          "summary": "string (600-1000 chars)",
          "key_insights": ["insight 1", "insight 2", "insight 3"],
          "recommendations": [
            {{
              "text": "recomendación",
              "impact": "alto|medio|bajo|null",
              "effort": "alto|medio|bajo|null",
              "related_service": "clave_servicio|null"
            }}
          ],
          "roadmap": {{"d30": ["..."], "d60": ["..."], "d90": ["..."]}},
          "next_steps": ["paso 1", "paso 2"],
          "hypothesis": "hipótesis del consultor"
        }}
    """).strip()


# Loaded once at module import — fail-fast if catalog is missing or malformed
_SYSTEM_PROMPT = _build_system_prompt()


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

        # Parse into typed output — lazy coercion handles legacy string recommendations
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
            "Analiza toda la información y produce la síntesis global de sesión 1 "
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
            max_tokens=3000,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
