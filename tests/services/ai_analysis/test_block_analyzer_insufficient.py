"""
tests/services/ai_analysis/test_block_analyzer_insufficient.py — C.1 (TDD RED → GREEN)

Tests that BlockAnalyzer.analyze() short-circuits to status=insufficient_data
when a block has critical empty fields, WITHOUT calling the Anthropic SDK.

Fixture: Pepe Cabeza SL block-3-data payload with q3_2_quality={} and
q3_4_personal_data={} (both have critical_for_synthesis sub-fields).

REQ-06: A block with critical empty fields MUST NOT trigger LLM synthesis.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Fixture: Pepe Cabeza SL block-3-data with critical empty fields
# ---------------------------------------------------------------------------

PEPE_CABEZA_BLOCK3_PAYLOAD = {
    "q3_1_sources": ["crm", "email", "bbdd_propia"],
    "q3_2_quality": {},
    "q3_3_volume": {},
    "q3_4_personal_data": {},
}

BLOCK_ID = "block-3-data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_block_analysis(block_id: str, payload: dict) -> MagicMock:
    """Return a mock BlockAnalysis row with the given payload."""
    ba = MagicMock()
    ba.id = str(uuid.uuid4())
    ba.intake_session_id = str(uuid.uuid4())
    ba.block_id = block_id
    ba.payload = payload
    ba.status = "in_progress"
    ba.llm_output = None
    ba.llm_model_used = None
    ba.generated_at = None
    return ba


# ---------------------------------------------------------------------------
# C.1 tests
# ---------------------------------------------------------------------------


class TestBlockAnalyzerInsufficientData:
    """BlockAnalyzer must short-circuit when block has critical empty fields."""

    @pytest.mark.asyncio
    async def test_does_not_call_anthropic_sdk_when_insufficient(self, test_db: AsyncSession):
        """
        When block-3-data has q3_2_quality={} and q3_4_personal_data={},
        BlockAnalyzer must NOT make any call to anthropic.AsyncAnthropic.
        """
        from app.services.ai_analysis.block_analyzer import BlockAnalyzer

        ba = _make_block_analysis(BLOCK_ID, PEPE_CABEZA_BLOCK3_PAYLOAD)
        block_analysis_id = ba.id

        # Mock DB to return our fake BlockAnalysis
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ba

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        analyzer = BlockAnalyzer(mock_db)

        with patch("app.services.ai_analysis.block_analyzer.anthropic.AsyncAnthropic") as mock_anthropic_cls:
            await analyzer.analyze(block_analysis_id, BLOCK_ID)

        # Anthropic client must never be instantiated
        mock_anthropic_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_sets_status_insufficient_data_when_critical_fields_empty(self):
        """
        BlockAnalysis.status must be set to 'insufficient_data'
        (not 'ready' or 'failed') when critical fields are empty.
        """
        from app.services.ai_analysis.block_analyzer import BlockAnalyzer

        ba = _make_block_analysis(BLOCK_ID, PEPE_CABEZA_BLOCK3_PAYLOAD)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ba

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        analyzer = BlockAnalyzer(mock_db)

        with patch("app.services.ai_analysis.block_analyzer.anthropic.AsyncAnthropic"):
            await analyzer.analyze(ba.id, BLOCK_ID)

        assert ba.status == "insufficient_data", (
            f"Expected status='insufficient_data', got '{ba.status}'"
        )

    @pytest.mark.asyncio
    async def test_llm_output_contains_missing_fields_list(self):
        """
        llm_output must be {'missing_fields': [...]} listing which critical
        fields were empty — NOT any LLM-synthesized text.
        """
        from app.services.ai_analysis.block_analyzer import BlockAnalyzer

        ba = _make_block_analysis(BLOCK_ID, PEPE_CABEZA_BLOCK3_PAYLOAD)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ba

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        analyzer = BlockAnalyzer(mock_db)

        with patch("app.services.ai_analysis.block_analyzer.anthropic.AsyncAnthropic"):
            await analyzer.analyze(ba.id, BLOCK_ID)

        assert isinstance(ba.llm_output, dict), "llm_output must be a dict"
        assert "missing_fields" in ba.llm_output, (
            f"llm_output must contain 'missing_fields'. Got: {ba.llm_output}"
        )
        missing = ba.llm_output["missing_fields"]
        assert isinstance(missing, list), "'missing_fields' must be a list"
        assert len(missing) > 0, "At least one missing field must be reported"
        # q3_2_quality has critical sub-field q3_2_level → must appear
        assert any("q3_2" in f for f in missing), (
            f"Expected q3_2_quality critical field in missing. Got: {missing}"
        )

    @pytest.mark.asyncio
    async def test_returns_without_llm_cost_saves_and_commits(self):
        """
        BlockAnalyzer must commit the insufficient_data row (saving it to DB)
        without any LLM call.
        """
        from app.services.ai_analysis.block_analyzer import BlockAnalyzer

        ba = _make_block_analysis(BLOCK_ID, PEPE_CABEZA_BLOCK3_PAYLOAD)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ba

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        analyzer = BlockAnalyzer(mock_db)

        with patch("app.services.ai_analysis.block_analyzer.anthropic.AsyncAnthropic"):
            await analyzer.analyze(ba.id, BLOCK_ID)

        # DB commit must be called (row persisted)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_payload_block_proceeds_to_llm(self):
        """
        Regression: a block with critical fields populated must NOT be blocked
        by the guard — it should proceed to the LLM call path.
        """
        from app.services.ai_analysis.block_analyzer import BlockAnalyzer

        # q3_1_sources provided, q3_2_quality with sub-field q3_2_level provided
        full_payload = {
            "q3_1_sources": ["crm"],
            "q3_2_quality": {"q3_2_level": "buena"},
            "q3_3_volume": {"q3_3_size": "medio"},
            "q3_4_personal_data": {"q3_4_category": "ninguna"},
        }
        ba = _make_block_analysis(BLOCK_ID, full_payload)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ba

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        analyzer = BlockAnalyzer(mock_db)

        # The LLM call will fail (no real API key), but the point is the
        # Anthropic client IS instantiated — guard did not block it.
        with patch("app.services.ai_analysis.block_analyzer.anthropic.AsyncAnthropic") as mock_anthropic_cls:
            mock_client = AsyncMock()
            mock_anthropic_cls.return_value = mock_client
            # Make the create call raise so we stop after the guard passes
            mock_client.messages.create = AsyncMock(side_effect=RuntimeError("stop here"))
            await analyzer.analyze(ba.id, BLOCK_ID)

        # Anthropic client WAS instantiated (guard passed it through)
        mock_anthropic_cls.assert_called_once()
        # Status is 'failed' because the LLM call raised
        assert ba.status == "failed"
