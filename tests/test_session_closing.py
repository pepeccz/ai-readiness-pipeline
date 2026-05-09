"""
tests/test_session_closing.py — Unit tests for SessionClosingService.

Covers:
  B.4 — system prompt contains catalog
  B.5 — run_session1_synthesis maps new schema shape
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── B.4 ────────────────────────────────────────────────────────────────────

def test_system_prompt_contains_catalog():
    """_SYSTEM_PROMPT must include all 3 service nombres and related_service rule."""
    from app.services.sessions import session_closing

    prompt = session_closing._SYSTEM_PROMPT

    # All 3 service nombres must appear
    assert "Diagnóstico Profundo de Procesos" in prompt
    assert "Desarrollo y Acompañamiento de Implementación" in prompt
    assert "Formación Personalizada en IA" in prompt

    # related_service selection rule
    assert "related_service" in prompt

    # REQ-17: Sales-bias preference rule must be absent
    assert "Prefiere formacion_personalizada" not in prompt, (
        "Sales-bias preference rule must be removed from system prompt (REQ-17)."
    )


def test_max_tokens_is_3000():
    """LLM call must use max_tokens=3000."""
    import inspect
    from app.services.sessions import session_closing

    source = inspect.getsource(session_closing.SessionClosingService._call_llm)
    assert "3000" in source, "max_tokens must be bumped to 3000"


# ─── B.5 ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_session1_synthesis_maps_new_shape():
    """generate_synthesis returns Session1SynthesisOutput from new-shape LLM JSON."""
    from app.services.sessions.session_closing import SessionClosingService
    from app.services.sessions.synthesis_schema import Session1SynthesisOutput

    new_shape_json = """{
        "summary": "Empresa con potencial IA.",
        "key_insights": ["Insight 1", "Insight 2"],
        "recommendations": [
            {
                "text": "Implementar automatización",
                "impact": "alto",
                "effort": "medio",
                "related_service": "desarrollo_acompanamiento"
            }
        ],
        "roadmap": {
            "d30": ["Diagnóstico"],
            "d60": ["Piloto"],
            "d90": ["Escalar"]
        },
        "next_steps": ["Segunda sesión"],
        "hypothesis": "El cliente está listo."
    }"""

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=new_shape_json)]

    service = SessionClosingService()

    with patch.object(service, "_call_llm", new=AsyncMock(return_value=mock_message)):
        result = await service.generate_synthesis(
            lead_triage_payload={"empresa": "Test Corp"},
            block_payloads={},
            block_syntheses={},
        )

    assert isinstance(result, Session1SynthesisOutput)
    assert result.summary == "Empresa con potencial IA."
    assert len(result.key_insights) == 2
    assert len(result.recommendations) == 1
    assert result.recommendations[0].related_service == "desarrollo_acompanamiento"
    assert result.hypothesis == "El cliente está listo."
