# app/services/scoring
"""
AIR scoring engine — deterministic CMMI-based assessment scoring.

Entry points:
    from app.services.scoring.loader import load_registry, load_block_rubric
    from app.services.scoring.scorer import score_block
    from app.services.scoring.composite import composite_score, risk_profile
    from app.services.scoring.guards import is_block_synthesizable
    from app.services.scoring import score_session, SessionScoreResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular imports at module load time; only used for type hints.
    from app.models.intake_session import IntakeSession
    from app.services.scoring.rubric import Registry


@dataclass
class SessionScoreResult:
    """
    Full scoring result for an IntakeSession.

    per_block_scores: {block_id → BlockScore}; all scored blocks
    composite_normalized: weighted average of non-insufficient block scores [0, 1]
    composite_level: min CMMI level across non-insufficient blocks (0-4)
    risk_profile: "low" | "medium" | "high" | "critical"
    per_block_levels: {block_id → CMMI level int}; insufficient_data blocks = 0
    insufficient_blocks: list of block_ids in insufficient_data state
    rubric_version: version string used (from session.rubric_version)
    """

    per_block_scores: dict = field(default_factory=dict)
    composite_normalized: float = 0.0
    composite_level: int = 0
    risk_profile: str = "low"
    per_block_levels: dict = field(default_factory=dict)
    insufficient_blocks: list = field(default_factory=list)
    rubric_version: str = "v1"


def score_session(
    session: "IntakeSession",
    registry: "Registry | None" = None,
) -> SessionScoreResult:
    """
    Score an IntakeSession end-to-end.

    For each block_analysis row attached to the session:
    - If status == "ready" or "completed": score the block payload using
      load_block_rubric + score_block.
    - If status == "insufficient_data": mark as insufficient (BlockScore with
      status="insufficient_data", raw=0, normalized=0).

    Computes composite score (composite_normalized, composite_level via min),
    risk profile, and returns a SessionScoreResult.

    Parameters
    ----------
    session : IntakeSession
        SQLAlchemy model instance. Must have `block_analyses` relationship loaded
        (each with `block_id`, `status`, `payload` attrs).
    registry : Registry | None
        Pre-loaded Registry. If None, loads via load_registry(session.rubric_version).

    Returns
    -------
    SessionScoreResult
    """
    from app.services.scoring.loader import load_registry, load_block_rubric
    from app.services.scoring.scorer import score_block
    from app.services.scoring.composite import composite_score as _composite_score
    from app.services.scoring.composite import risk_profile as _risk_profile
    from app.services.scoring.rubric import BlockScore

    rubric_version = getattr(session, "rubric_version", "v1")

    if registry is None:
        registry = load_registry(rubric_version)

    per_block_scores: dict[str, BlockScore] = {}
    insufficient_blocks: list[str] = []

    for block_analysis in getattr(session, "block_analyses", []):
        block_id = block_analysis.block_id
        status = getattr(block_analysis, "status", "unknown")
        payload = getattr(block_analysis, "payload", {}) or {}

        if status == "insufficient_data":
            # Mark insufficient — level 0 for risk gates (conservative)
            per_block_scores[block_id] = BlockScore(
                raw=0.0,
                normalized=0.0,
                answered_count=0,
                block_id=block_id,
                status="insufficient_data",
            )
            insufficient_blocks.append(block_id)
        else:
            # Any other status with a payload → attempt scoring
            try:
                block_rubric = load_block_rubric(block_id)
                bs = score_block(payload, block_rubric)
                # scored blocks always have status="scored" (default)
                per_block_scores[block_id] = bs
            except FileNotFoundError:
                # Unknown block_id (e.g. deep block, triage) → skip silently
                continue

    if not per_block_scores:
        return SessionScoreResult(
            rubric_version=rubric_version,
        )

    composite_result = _composite_score(per_block_scores, registry)
    profile = _risk_profile(composite_result.per_block_levels, composite_result.composite_level)

    return SessionScoreResult(
        per_block_scores=per_block_scores,
        composite_normalized=composite_result.composite_normalized,
        composite_level=composite_result.composite_level,
        risk_profile=profile,
        per_block_levels=composite_result.per_block_levels,
        insufficient_blocks=insufficient_blocks,
        rubric_version=rubric_version,
    )
