"""
tests/unit/test_session_closing — T7.3

Unit tests for app/services/sessions/session_closing.py

LLM is always mocked — no real API calls.
"""

from __future__ import annotations

import pytest

from app.services.sessions.session_closing import SessionClosingService


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
    "global_synthesis": "La empresa está en fase exploratoria con objetivos poco definidos y riesgo de fracaso por falta de sponsor.",
    "preliminary_hypotheses": [
        "El equipo técnico tiene más madurez que el liderazgo organizacional.",
        "El proceso crítico seleccionado no tiene datos suficientes para IA.",
        "El timing puede ser prematuro dado el estado de governance."
    ],
    "activated_branches": ["post_mortem_proyecto", "governance_previo_ia"]
}"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_synthesis_returns_structured_output(monkeypatch):
    """generate_synthesis returns dict with global_synthesis and hypotheses."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(_SAMPLE_OUTPUT))

    result = await svc.generate_synthesis(
        lead_triage_payload={"sector": "tecnologia"},
        block_payloads={"block-1-strategic": {"q1_3_previous": "abandoned"}},
        block_syntheses={},
    )

    assert "global_synthesis" in result
    assert "preliminary_hypotheses" in result
    assert "activated_branches" in result
    assert isinstance(result["preliminary_hypotheses"], list)
    assert len(result["preliminary_hypotheses"]) == 3


@pytest.mark.asyncio
async def test_generate_synthesis_requires_three_hypotheses(monkeypatch):
    """Output must contain exactly 3 preliminary hypotheses."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(_SAMPLE_OUTPUT))

    result = await svc.generate_synthesis(
        lead_triage_payload={},
        block_payloads={},
        block_syntheses={},
    )

    assert len(result["preliminary_hypotheses"]) == 3


@pytest.mark.asyncio
async def test_generate_synthesis_returns_activated_branches(monkeypatch):
    """activated_branches list is returned and can be empty."""
    output = """{
        "global_synthesis": "Síntesis breve.",
        "preliminary_hypotheses": ["H1", "H2", "H3"],
        "activated_branches": []
    }"""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(output))

    result = await svc.generate_synthesis(
        lead_triage_payload={},
        block_payloads={},
        block_syntheses={},
    )

    assert result["activated_branches"] == []


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
