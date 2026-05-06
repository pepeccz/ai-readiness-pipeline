"""
tests/services/test_session_closing_service.py — TA.6

Tests that _run_synthesis (via SessionClosingService) writes session1_synthesis
on success and leaves it None on exception.

We test the service logic in isolation by calling generate_synthesis() directly
and verifying the shape of the result, then checking the route's BG task
behaviour via mocking in the integration layer.
"""

from __future__ import annotations

import pytest

from app.services.sessions.session_closing import SessionClosingService


_SUCCESS_OUTPUT = """{
    "global_synthesis": "La empresa está en fase exploratoria.",
    "preliminary_hypotheses": ["H1", "H2", "H3"],
    "activated_branches": ["governance_previo_ia"]
}"""


def _make_mock_llm(output_text: str):
    async def _mock(*args, **kwargs):
        class _Msg:
            content = [type("C", (), {"text": output_text})()]
        return _Msg()
    return _mock


def _make_fail_llm():
    async def _fail(*args, **kwargs):
        raise RuntimeError("LLM timed out")
    return _fail


@pytest.mark.asyncio
async def test_generate_synthesis_returns_required_fields(monkeypatch):
    """On success, generate_synthesis returns dict with expected top-level keys."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(_SUCCESS_OUTPUT))

    result = await svc.generate_synthesis(
        lead_triage_payload={"sector": "tecnologia"},
        block_payloads={"block-1-strategic": {"q1": "yes"}},
        block_syntheses={},
    )

    assert "global_synthesis" in result
    assert "preliminary_hypotheses" in result
    assert "activated_branches" in result


@pytest.mark.asyncio
async def test_generate_synthesis_handles_code_fenced_response(monkeypatch):
    """A-3: extract_json strips code fences; synthesis parses correctly."""
    fenced = f"```json\n{_SUCCESS_OUTPUT}\n```"
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(fenced))

    result = await svc.generate_synthesis(
        lead_triage_payload={"sector": "tecnologia"},
        block_payloads={"block-1-strategic": {"q1": "yes"}},
        block_syntheses={},
    )

    assert result["global_synthesis"] == "La empresa está en fase exploratoria."


@pytest.mark.asyncio
async def test_generate_synthesis_raises_value_error_on_invalid_json(monkeypatch):
    """A-3: malformed LLM response raises ValueError (not JSONDecodeError)."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm("totally not JSON lol"))

    with pytest.raises(ValueError, match="invalid JSON"):
        await svc.generate_synthesis(
            lead_triage_payload={},
            block_payloads={},
            block_syntheses={},
        )


@pytest.mark.asyncio
async def test_generate_synthesis_logs_raw_on_invalid_json(monkeypatch):
    """A-3: raw LLM payload logged at ERROR level when extraction fails."""
    import structlog.testing

    bad_raw = "not parseable at all!!!"
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_mock_llm(bad_raw))

    with structlog.testing.capture_logs() as captured:
        with pytest.raises(ValueError):
            await svc.generate_synthesis(
                lead_triage_payload={},
                block_payloads={},
                block_syntheses={},
            )

    error_events = [e for e in captured if e.get("log_level") == "error"]
    raw_logged = any(bad_raw in str(e.get("raw_llm_output", "")) for e in error_events)
    assert raw_logged, f"Expected raw in log. Got: {error_events}"


@pytest.mark.asyncio
async def test_generate_synthesis_raises_on_llm_exception(monkeypatch):
    """On LLM exception, generate_synthesis propagates the exception."""
    svc = SessionClosingService()
    monkeypatch.setattr(svc, "_call_llm", _make_fail_llm())

    with pytest.raises(Exception):
        await svc.generate_synthesis(
            lead_triage_payload={},
            block_payloads={},
            block_syntheses={},
        )
