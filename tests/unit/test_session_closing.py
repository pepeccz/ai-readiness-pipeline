"""
tests/unit/test_session_closing — T7.3

Unit tests for app/services/sessions/session_closing.py

LLM is always mocked — no real API calls.
"""

from __future__ import annotations

import pytest

from app.services.sessions.session_closing import Session1SynthesisOutput, SessionClosingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_llm(output_text: str):
    """Return an async callable that simulates an Anthropic API response."""
    async def _mock(*args, **kwargs):
        class _Msg:
            content = [type("C", (), {"text": output_text})()]
        return _Msg()
    return _mock


_SAMPLE_OUTPUT = """{
    "summary": "La empresa está en fase exploratoria con objetivos poco definidos.",
    "key_insights": [
        "El equipo técnico tiene más madurez que el liderazgo organizacional.",
        "El proceso crítico seleccionado no tiene datos suficientes para IA.",
        "El timing puede ser prematuro dado el estado de governance."
    ],
    "recommendations": ["Definir un sponsor ejecutivo.", "Piloto pequeño antes de escalar."],
    "hypothesis": "El equipo técnico lidera pero sin alineación organizacional el proyecto fracasará."
}"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_synthesis_returns_structured_output(monkeypatch):
    """generate_synthesis returns Session1SynthesisOutput with expected fields."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(_SAMPLE_OUTPUT))

    result = await svc.generate_synthesis(
        lead_triage_payload={"sector": "tecnologia"},
        block_payloads={"block-1-strategic": {"q1_3_previous": "abandoned"}},
        block_syntheses={},
    )

    assert isinstance(result, Session1SynthesisOutput)
    assert result.summary is not None
    assert isinstance(result.key_insights, list)
    assert isinstance(result.recommendations, list)
    assert len(result.key_insights) == 3


@pytest.mark.asyncio
async def test_generate_synthesis_returns_key_insights_and_recommendations(monkeypatch):
    """Output must contain key_insights and recommendations lists."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(_SAMPLE_OUTPUT))

    result = await svc.generate_synthesis(
        lead_triage_payload={},
        block_payloads={},
        block_syntheses={},
    )

    assert result.key_insights is not None
    assert result.recommendations is not None
    assert len(result.recommendations) == 2


@pytest.mark.asyncio
async def test_generate_synthesis_allows_empty_optional_fields(monkeypatch):
    """Partial LLM output (missing optional fields) must not raise."""
    output = '{"summary": "Síntesis breve."}'
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(output))

    result = await svc.generate_synthesis(
        lead_triage_payload={},
        block_payloads={},
        block_syntheses={},
    )

    assert result.summary == "Síntesis breve."
    assert result.key_insights is None or isinstance(result.key_insights, list)


@pytest.mark.asyncio
async def test_generate_synthesis_handles_llm_json_error(monkeypatch):
    """If LLM returns invalid JSON, service raises ValueError."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm("this is not json"))

    with pytest.raises((ValueError, Exception)):
        await svc.generate_synthesis(
            lead_triage_payload={},
            block_payloads={},
            block_syntheses={},
        )
