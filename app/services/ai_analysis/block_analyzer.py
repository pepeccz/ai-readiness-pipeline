"""
app/services/ai_analysis/block_analyzer — Orchestrates LLM analysis per block.

`BlockAnalyzer.analyze(block_analysis_id, block_id)`:
  1. Load BlockAnalysis + payload from DB
  2. Build prompt with prompt_builder (cached system + schema)
  3. Call Anthropic SDK with correct model per BLOCK_LLM_MODEL
  4. Parse JSON output → validate with Pydantic output schema
  5. Apply 5-layer llm_filters
  6. Persist BlockAnalysis(status=ready, llm_output) + Suggestion rows (max 3)
  7. On LLM error → status=failed + structlog

Structured log events:
  block_analysis_started, block_analysis_ready, block_analysis_failed
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import anthropic
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.block_analysis import BlockAnalysis
from app.models.suggestion import Suggestion
from app.services.ai_analysis.llm_filters import apply_all_filters
from app.services.ai_analysis.output_schemas import BlockAnalysisOutput, get_output_schema
from app.services.ai_analysis.prompt_builder import PromptBuilder
from config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Model selection per block
# ---------------------------------------------------------------------------

BLOCK_LLM_MODEL: dict[str, str] = {
    "block-1-strategic": "claude-sonnet-4-6",
    "block-2-process-critical-full": "claude-sonnet-4-6",
    "block-2-process-critical-reduced": "claude-haiku-4-5",
    "block-2-process-critical-cross-area": "claude-sonnet-4-6",
    "block-3-data": "claude-haiku-4-5",
    "block-4-talent": "claude-sonnet-4-6",
    "block-5-infrastructure": "claude-haiku-4-5",
    "block-6-compliance": "claude-sonnet-4-6",
    "block-7-governance": "claude-haiku-4-5",
}

DEFAULT_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1500
LLM_TIMEOUT = 15.0  # seconds


def _get_block_schema_for_id(block_id: str) -> dict:
    """Load block schema from YAML or return minimal dict."""
    try:
        from app.services.questionnaire import schema_loader
        try:
            schema_loader.get_schema_version()
        except RuntimeError:
            schema_loader.load_all()
        root = schema_loader.get_root_schema()
        blocks = root.get("blocks", []) or []
        for block in blocks:
            if isinstance(block, dict) and block.get("id") == block_id:
                return block
    except Exception:
        pass
    # Fallback minimal schema
    return {"id": block_id, "title": block_id, "questions": []}


class BlockAnalyzer:
    """Orchestrates LLM block analysis."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.prompt_builder = PromptBuilder()

    async def analyze(self, block_analysis_id: str, block_id: str) -> None:
        """
        Run LLM analysis for a block and persist results.

        Updates BlockAnalysis.status to "ready" or "failed".
        """
        start_ts = time.monotonic()

        logger.info("block_analysis_started", block_analysis_id=block_analysis_id, block_id=block_id)

        # Load BlockAnalysis
        stmt = select(BlockAnalysis).where(BlockAnalysis.id == block_analysis_id)
        result = await self.db.execute(stmt)
        ba = result.scalar_one_or_none()
        if ba is None:
            logger.error("block_analysis_not_found", block_analysis_id=block_analysis_id)
            return

        try:
            # Build prompt
            block_schema = _get_block_schema_for_id(block_id)
            messages = self.prompt_builder.build(
                block_schema=block_schema,
                payload=ba.payload or {},
                prev_analyses=[],
            )

            # Select model
            model = BLOCK_LLM_MODEL.get(block_id, DEFAULT_MODEL)

            # Call Anthropic SDK
            client = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key.get_secret_value()
            )

            response = await client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=messages,
            )

            raw_text = response.content[0].text

            # Parse JSON output
            llm_data = json.loads(raw_text)

            # Validate with Pydantic schema
            output_schema_class = get_output_schema(block_id)
            validated: BlockAnalysisOutput = output_schema_class(**llm_data)

            # Extract follow_ups for filtering
            follow_ups_raw = [
                {
                    "text": fu.text,
                    "rationale": fu.rationale,
                    "priority": fu.priority,
                    "confidence": fu.confidence,
                }
                for fu in validated.follow_ups
            ]

            # Apply 5-layer filters
            context = {
                "block_schema": block_schema,
                "prev_suggestions": [],
            }
            filtered_follow_ups = apply_all_filters(follow_ups_raw, context=context)

            # Persist BlockAnalysis
            ba.llm_output = {
                "synthesis": validated.synthesis,
                "contradictions": [c.model_dump() for c in validated.contradictions],
                "follow_ups": [
                    {"text": fu.text, "rationale": fu.rationale, "priority": fu.priority, "confidence": fu.confidence}
                    for fu in validated.follow_ups
                ],
                "preliminary_hypothesis": validated.preliminary_hypothesis,
                "block_specific_outputs": validated.block_specific_outputs,
            }
            ba.llm_model_used = model
            ba.status = "ready"
            ba.generated_at = datetime.now(tz=timezone.utc)

            await self.db.flush()

            # Persist Suggestions (filtered, max 3)
            for fu in filtered_follow_ups:
                suggestion = Suggestion(
                    block_analysis_id=ba.id,
                    type="follow_up",
                    text=fu["text"],
                    rationale=fu.get("rationale", ""),
                    confidence=fu["confidence"],
                    priority=fu.get("priority", "med"),
                    consultant_action="pending",
                )
                self.db.add(suggestion)

            await self.db.commit()

            latency_ms = int((time.monotonic() - start_ts) * 1000)
            logger.info(
                "block_analyzed",
                lead_id=ba.intake_session_id,  # session_id used as proxy here
                block_id=block_id,
                llm_model=model,
                latency_ms=latency_ms,
                suggestions_count=len(filtered_follow_ups),
            )

        except Exception as exc:
            logger.error(
                "block_analysis_failed",
                block_analysis_id=block_analysis_id,
                block_id=block_id,
                error=str(exc),
                exc_info=True,
            )
            ba.status = "failed"
            ba.error_message = str(exc)[:1000]
            await self.db.commit()
