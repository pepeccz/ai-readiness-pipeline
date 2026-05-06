"""
tests/integration/test_block_analyzer.py — T6.5

Integration tests for app/services/ai_analysis/block_analyzer.py:
  - Mock Anthropic SDK returns valid JSON → persists BlockAnalysis(status=ready) + Suggestion[]
  - LLM failure → status=failed
  - Correct model selected per block from BLOCK_LLM_MODEL map
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.block_analysis import BlockAnalysis
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.suggestion import Suggestion
from app.services.ai_analysis.block_analyzer import BlockAnalyzer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_LLM_RESPONSE = json.dumps({
    "synthesis": "La empresa tiene experiencia inicial con IA pero sin estructura de gobierno.",
    "contradictions": [
        {"text": "Mencionan urgencia alta pero no hay sponsor definido", "severity": "high"}
    ],
    "follow_ups": [
        {
            "text": "¿Quién tiene autoridad presupuestaria para aprobar el piloto de IA?",
            "rationale": "No hay sponsor claro identificado en las respuestas",
            "priority": "high",
            "confidence": 0.85,
        },
        {
            "text": "¿En qué plazo se espera ver resultados concretos del proyecto de IA?",
            "rationale": "El apetito de riesgo es difuso sin timeline definido",
            "priority": "med",
            "confidence": 0.78,
        },
    ],
    "preliminary_hypothesis": "La empresa está lista para un piloto acotado si se define sponsor.",
    "block_specific_outputs": {},
})


async def _make_lead_and_session(db) -> tuple[Lead, IntakeSession, BlockAnalysis]:
    """Create Lead → IntakeSession → BlockAnalysis(status=submitted) for tests."""
    lead = Lead(
        full_name="Test User",
        email="test@test.com",
        company_name="TestCorp",
        sector="tecnologia",
        company_size="26_100",
        respondent_role="ceo_fundador",
        ai_maturity="exploracion",
        ai_goals=["eficiencia"],
        urgency="alta",
        commitment="agendar",
        triage_payload={},
        triage_score=80,
        triage_bucket="auto_accept",
        status="accepted",
    )
    db.add(lead)
    await db.flush()

    session = IntakeSession(
        lead_id=lead.id,
        primary_area="ventas",
        state="in_progress",
        blocks_completed=[],
    )
    db.add(session)
    await db.flush()

    block_analysis = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={"q1": "Mejorar eficiencia operativa", "q2": "Director TI"},
        status="pending_analysis",
    )
    db.add(block_analysis)
    await db.flush()
    await db.commit()

    return lead, session, block_analysis


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBlockAnalyzerSuccess:
    """T6.5 — mock SDK returns valid JSON → status=ready + suggestions persisted."""

    async def test_analyze_sets_status_ready(self, test_db):
        lead, session, ba = await _make_lead_and_session(test_db)

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=VALID_LLM_RESPONSE)]

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_message)

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(
                block_analysis_id=ba.id,
                block_id="block-1-strategic",
            )

        await test_db.refresh(ba)
        assert ba.status == "ready"

    async def test_analyze_persists_suggestions(self, test_db):
        lead, session, ba = await _make_lead_and_session(test_db)

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=VALID_LLM_RESPONSE)]

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_message)

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(
                block_analysis_id=ba.id,
                block_id="block-1-strategic",
            )

        stmt = select(Suggestion).where(Suggestion.block_analysis_id == ba.id)
        result = await test_db.execute(stmt)
        suggestions = result.scalars().all()
        assert len(suggestions) >= 1
        assert len(suggestions) <= 3  # max 3 per spec


class TestBlockAnalyzerFailure:
    """T6.5 — LLM failure → status=failed."""

    async def test_llm_exception_sets_status_failed(self, test_db):
        lead, session, ba = await _make_lead_and_session(test_db)

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                side_effect=Exception("LLM API error")
            )

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(
                block_analysis_id=ba.id,
                block_id="block-1-strategic",
            )

        await test_db.refresh(ba)
        assert ba.status == "failed"
        assert ba.error_message is not None


class TestBlockAnalyzerJsonExtraction:
    """A-2 — extract_json adopted; malformed LLM JSON → status=failed, raw logged."""

    async def test_code_fenced_json_parses_correctly(self, test_db):
        """extract_json can handle code-fenced responses; status=ready."""
        lead, session, ba = await _make_lead_and_session(test_db)
        fenced = f"```json\n{VALID_LLM_RESPONSE}\n```"

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=fenced)]

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_message)

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(block_analysis_id=ba.id, block_id="block-1-strategic")

        await test_db.refresh(ba)
        assert ba.status == "ready"

    async def test_malformed_llm_json_sets_status_ready(self, test_db):
        """REQ-2: when LLM returns unparseable text, status=ready (not failed) — partial output preserved."""
        lead, session, ba = await _make_lead_and_session(test_db)

        raw_text = "I'm sorry, I cannot produce JSON today."
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=raw_text)]

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_message)

            analyzer = BlockAnalyzer(db=test_db)
            # Must NOT raise — must degrade gracefully
            await analyzer.analyze(block_analysis_id=ba.id, block_id="block-1-strategic")

        await test_db.refresh(ba)
        assert ba.status == "ready"
        assert ba.llm_output is not None
        assert "raw" in ba.llm_output

    async def test_malformed_llm_json_logs_raw_payload(self, test_db):
        """REQ-2: raw LLM payload is logged at WARNING level on extraction failure."""
        import structlog.testing

        lead, session, ba = await _make_lead_and_session(test_db)
        bad_raw = "No JSON here, only sadness."

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=bad_raw)]

        with structlog.testing.capture_logs() as captured:
            with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.AsyncAnthropic.return_value = mock_client
                mock_client.messages.create = AsyncMock(return_value=mock_message)

                analyzer = BlockAnalyzer(db=test_db)
                await analyzer.analyze(block_analysis_id=ba.id, block_id="block-1-strategic")

        warning_events = [e for e in captured if e.get("log_level") in ("warning", "warn")]
        raw_logged = any(
            bad_raw in str(e.get("raw_text", ""))
            for e in warning_events
        )
        assert raw_logged, f"Expected raw payload in warning log. Got: {captured}"


class TestBlockAnalyzerModelSelection:
    """T6.5 — correct model selected per BLOCK_LLM_MODEL map."""

    async def test_strategic_block_uses_sonnet(self, test_db):
        from app.services.ai_analysis.block_analyzer import BLOCK_LLM_MODEL
        model = BLOCK_LLM_MODEL.get("block-1-strategic", "")
        assert "sonnet" in model.lower()

    async def test_data_block_uses_haiku(self, test_db):
        from app.services.ai_analysis.block_analyzer import BLOCK_LLM_MODEL
        model = BLOCK_LLM_MODEL.get("block-3-data", "")
        assert "haiku" in model.lower()

    async def test_compliance_block_uses_sonnet(self, test_db):
        from app.services.ai_analysis.block_analyzer import BLOCK_LLM_MODEL
        model = BLOCK_LLM_MODEL.get("block-6-compliance", "")
        assert "sonnet" in model.lower()
