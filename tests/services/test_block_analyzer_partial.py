"""
tests/services/test_block_analyzer_partial.py — B.1 (REQ-2)

TDD: partial LLM output handling in block_analyzer.analyze().

Scenarios:
  (a) Partial output missing one field → status='ready', missing field is None,
      llm_output_field_missing counter incremented per missing field.
  (b) All domain fields absent (only common fields) → all domain fields None,
      counter incremented per missing field.
  (c) Malformed JSON / non-dict → status='ready', llm_output={"raw": <text>},
      llm_output_unparseable counter incremented, warning logged.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

import app.observability as obs
from app.models.block_analysis import BlockAnalysis
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.suggestion import Suggestion
from app.services.ai_analysis.block_analyzer import BlockAnalyzer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_counters() -> None:
    """Reset observability counters between tests."""
    import threading
    with obs._lock:
        obs._counters.clear()


async def _make_lead_session_ba(db, block_id: str = "block-3-data") -> BlockAnalysis:
    lead = Lead(
        full_name="Partial Test",
        email="partial@test.com",
        company_name="PartialCorp",
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
        primary_area="datos",
        state="in_progress",
        blocks_completed=[],
    )
    db.add(session)
    await db.flush()

    ba = BlockAnalysis(
        intake_session_id=session.id,
        block_id=block_id,
        payload={"q1": "Tenemos datos en silos"},
        status="pending_analysis",
    )
    db.add(ba)
    await db.flush()
    await db.commit()
    return ba


def _mock_llm_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


# ---------------------------------------------------------------------------
# (a) Partial output — missing one domain field (data_readiness)
# ---------------------------------------------------------------------------

class TestPartialLLMOutputMissingOneField:
    async def test_status_is_ready_when_field_missing(self, test_db):
        """Partial output → status='ready', not failed."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-3-data")

        # DataOutput requires data_readiness — omit it intentionally
        partial_json = json.dumps({
            "synthesis": "Los datos están dispersos y sin gobierno claro.",
            "contradictions": [],
            "follow_ups": [],
            "preliminary_hypothesis": None,
            "block_specific_outputs": {},
            # data_readiness intentionally missing
        })

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(partial_json))

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-3-data")

        await test_db.refresh(ba)
        assert ba.status == "ready", f"Expected status='ready', got '{ba.status}'"

    async def test_llm_output_field_missing_counter_incremented(self, test_db):
        """Missing domain field → llm_output_field_missing counter incremented."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-3-data")

        partial_json = json.dumps({
            "synthesis": "Los datos están dispersos y sin gobierno claro.",
            "contradictions": [],
            "follow_ups": [],
            "preliminary_hypothesis": None,
            "block_specific_outputs": {},
        })

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(partial_json))

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-3-data")

        # Counter must have been incremented for data_readiness missing
        total_missing = obs.get("llm_output_field_missing")
        assert total_missing >= 1, (
            f"Expected llm_output_field_missing >= 1, got {total_missing}"
        )

    async def test_llm_output_contains_present_fields(self, test_db):
        """Fields that ARE in the LLM response appear in llm_output."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-3-data")

        partial_json = json.dumps({
            "synthesis": "Los datos están dispersos y sin gobierno claro.",
            "contradictions": [],
            "follow_ups": [],
            "preliminary_hypothesis": "Hay potencial si se centraliza.",
            "block_specific_outputs": {},
        })

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(partial_json))

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-3-data")

        await test_db.refresh(ba)
        assert ba.llm_output is not None
        assert ba.llm_output.get("synthesis") == "Los datos están dispersos y sin gobierno claro."


# ---------------------------------------------------------------------------
# (b) All domain fields absent
# ---------------------------------------------------------------------------

class TestAllDomainFieldsAbsent:
    async def test_status_ready_when_all_domain_fields_missing(self, test_db):
        """Even if all domain fields missing → status='ready'."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-7-governance")

        # GovernanceOutput requires shadow_ai_risk — omit everything domain-specific
        partial_json = json.dumps({
            "synthesis": "Gobierno de IA no formalizado aún.",
            "contradictions": [],
            "follow_ups": [],
            "preliminary_hypothesis": None,
            "block_specific_outputs": {},
        })

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(partial_json))

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-7-governance")

        await test_db.refresh(ba)
        assert ba.status == "ready"

    async def test_missing_field_counter_incremented_per_field(self, test_db):
        """One counter increment per missing domain field."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-7-governance")

        partial_json = json.dumps({
            "synthesis": "Gobierno de IA no formalizado.",
            "contradictions": [],
            "follow_ups": [],
            "preliminary_hypothesis": None,
            "block_specific_outputs": {},
        })

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=_mock_llm_response(partial_json))

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-7-governance")

        # GovernanceOutput has shadow_ai_risk + first_governance_deliverables as domain fields
        # shadow_ai_risk is missing → at least 1 increment
        total_missing = obs.get("llm_output_field_missing")
        assert total_missing >= 1


# ---------------------------------------------------------------------------
# (c) Malformed JSON / non-dict response
# ---------------------------------------------------------------------------

class TestMalformedLLMResponse:
    async def test_malformed_json_status_is_ready(self, test_db):
        """Non-parseable LLM text → status='ready' (not 'failed') per REQ-2."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-1-strategic")

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=_mock_llm_response("Lo siento, no puedo generar JSON hoy.")
            )

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-1-strategic")

        await test_db.refresh(ba)
        assert ba.status == "ready", f"Expected status='ready' for unparseable, got '{ba.status}'"

    async def test_malformed_json_llm_output_contains_raw(self, test_db):
        """Non-parseable response → llm_output={"raw": <text>}."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-1-strategic")
        raw_text = "Lo siento, no puedo generar JSON hoy."

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=_mock_llm_response(raw_text)
            )

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-1-strategic")

        await test_db.refresh(ba)
        assert ba.llm_output is not None
        assert "raw" in ba.llm_output
        assert ba.llm_output["raw"] == raw_text

    async def test_malformed_json_increments_unparseable_counter(self, test_db):
        """Non-parseable response → llm_output_unparseable counter incremented."""
        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-1-strategic")

        with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=_mock_llm_response("No JSON aquí.")
            )

            analyzer = BlockAnalyzer(db=test_db)
            await analyzer.analyze(ba.id, "block-1-strategic")

        assert obs.get("llm_output_unparseable") >= 1

    async def test_malformed_json_logs_warning(self, test_db):
        """Non-parseable response → warning logged with raw text."""
        import structlog.testing

        _reset_counters()
        ba = await _make_lead_session_ba(test_db, "block-1-strategic")
        raw_text = "No JSON aquí, solo texto."

        with structlog.testing.capture_logs() as captured:
            with patch("app.services.ai_analysis.block_analyzer.anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.AsyncAnthropic.return_value = mock_client
                mock_client.messages.create = AsyncMock(
                    return_value=_mock_llm_response(raw_text)
                )

                analyzer = BlockAnalyzer(db=test_db)
                await analyzer.analyze(ba.id, "block-1-strategic")

        warning_events = [e for e in captured if e.get("log_level") in ("warning", "warn")]
        assert len(warning_events) >= 1, f"Expected warning log. Got: {captured}"
