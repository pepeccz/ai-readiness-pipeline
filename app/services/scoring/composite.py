"""
app/services/scoring/composite.py

Composite scoring logic for the AIR assessment.

Functions:
    level_from_normalized(score, thresholds) → int (0-4 CMMI level)
    composite_level_min(per_block_levels) → int
    composite_score(block_scores, registry) → CompositeResult
    risk_profile(block_levels, composite_level) → str

Design:
    - Composite CMMI level = min of per-block levels (blocks with status=scored only)
    - insufficient_data blocks are excluded from composite_normalized calculation
      but appear in per_block_levels with level=0 (worst-case conservative for risk gates)
    - composite_normalized = weighted average of non-insufficient block_normalized values
    - average_normalized = same as composite_normalized (identical when all blocks scored,
      stored separately for narrative use: "you average X but ceiling is Y")
    - Risk profile is 100% deterministic from per-block CMMI levels (no LLM)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompositeResult:
    """
    Full composite scoring result.

    composite_normalized: weighted average of non-insufficient block scores [0, 1]
    composite_level: min CMMI level across non-insufficient blocks (0-4)
    per_block_levels: {block_id → CMMI level int}; insufficient_data blocks have level=0
    average_normalized: same as composite_normalized (informational, for narrative)
    """

    composite_normalized: float
    composite_level: int
    per_block_levels: dict[str, int]
    average_normalized: float


# ---------------------------------------------------------------------------
# CMMI level derivation
# ---------------------------------------------------------------------------

# CMMI level integer → threshold bounds order (for fallback)
_CMMI_LEVEL_ORDER = [
    ("optimizado", 4),
    ("avanzado", 3),
    ("establecido", 2),
    ("emergente", 1),
    ("inicial", 0),
]


def level_from_normalized(
    score: float,
    thresholds: dict[str, dict[str, Any]],
) -> int:
    """
    Map a normalized score [0, 1] to a CMMI integer level (0-4).

    Parameters
    ----------
    score : float
        Normalized block score in [0, 1].
    thresholds : dict
        CMMI thresholds from Registry.cmmi_thresholds (min, max, level per level name).

    Returns
    -------
    int
        CMMI level 0-4.
    """
    # Iterate levels from highest to lowest; return the first that contains score
    for level_name, level_int in _CMMI_LEVEL_ORDER:
        bounds = thresholds.get(level_name, {})
        min_val = float(bounds.get("min", 0.0))
        max_val = float(bounds.get("max", 0.0))
        if min_val <= score < max_val:
            return level_int

    # Edge case: score exactly at 1.0 (optimizado.max is 1.01, should match)
    # Defensive: if nothing matched, check explicit level fields
    for level_name, bounds in thresholds.items():
        level_int = int(bounds.get("level", 0))
        min_val = float(bounds.get("min", 0.0))
        max_val = float(bounds.get("max", 0.0))
        if min_val <= score < max_val:
            return level_int

    # Final fallback: score must be 0 → Inicial
    return 0


def composite_level_min(per_block_levels: dict[str, int]) -> int:
    """
    Return the minimum CMMI level across all blocks in per_block_levels.

    Parameters
    ----------
    per_block_levels : dict[str, int]
        Maps block_id → CMMI level integer.

    Returns
    -------
    int
        Minimum level (0 if any block is at 0, or if dict is empty).
    """
    if not per_block_levels:
        return 0
    return min(per_block_levels.values())


def composite_score(
    block_scores: dict[str, "BlockScore"],  # noqa: F821 — forward ref
    registry: "Registry",  # noqa: F821 — forward ref
) -> CompositeResult:
    """
    Compute the full composite scoring result.

    Parameters
    ----------
    block_scores : dict[str, BlockScore]
        Maps block_id → BlockScore. Must include all blocks in the session.
    registry : Registry
        The loaded rubric registry (block_weights + cmmi_thresholds).

    Returns
    -------
    CompositeResult
    """
    # Import here to avoid circular dependency issues at module load time
    from app.services.scoring.rubric import BlockScore  # noqa: F401

    thresholds = registry.cmmi_thresholds
    block_weights = registry.block_weights

    # Compute per-block CMMI levels.
    # insufficient_data blocks get level=0 (conservative worst-case for risk gates)
    per_block_levels: dict[str, int] = {}
    for block_id, bs in block_scores.items():
        if bs.status == "insufficient_data":
            per_block_levels[block_id] = 0
        else:
            per_block_levels[block_id] = level_from_normalized(bs.normalized, thresholds)

    # Compute composite_normalized = weighted average over non-insufficient blocks
    weighted_sum = 0.0
    total_weight = 0.0
    for block_id, bs in block_scores.items():
        if bs.status == "insufficient_data":
            continue
        weight = float(block_weights.get(block_id, 1.0))
        weighted_sum += bs.normalized * weight
        total_weight += weight

    if total_weight == 0.0:
        composite_normalized = 0.0
    else:
        composite_normalized = weighted_sum / total_weight
        composite_normalized = max(0.0, min(1.0, composite_normalized))

    # Composite CMMI level = min of per-block levels among non-insufficient blocks
    non_insufficient_levels = {
        bid: lvl
        for bid, lvl in per_block_levels.items()
        if block_scores.get(bid) and block_scores[bid].status != "insufficient_data"
    }
    if non_insufficient_levels:
        c_level = composite_level_min(non_insufficient_levels)
    else:
        c_level = 0

    return CompositeResult(
        composite_normalized=composite_normalized,
        composite_level=c_level,
        per_block_levels=per_block_levels,
        average_normalized=composite_normalized,
    )


# ---------------------------------------------------------------------------
# Risk profile — deterministic gates
# ---------------------------------------------------------------------------

def risk_profile(
    block_levels: dict[str, int],
    composite_level: int,
) -> str:
    """
    Derive a risk profile from per-block CMMI levels.

    Evaluation order: critical → high → medium → low

    Rules (from design ADR-4):
      critical : compliance <= 1 AND governance <= 1
      high     : compliance <= 1 OR governance <= 1 OR data <= 0
      medium   : composite_level <= 1
      low      : otherwise

    insufficient_data blocks are passed in with level=0 (worst-case),
    which automatically triggers the appropriate gate.

    Parameters
    ----------
    block_levels : dict[str, int]
        Per-block CMMI levels. Must include compliance, governance, data keys.
        Missing blocks default to 4 (best-case — don't penalize absent blocks
        beyond what's already 0 from insufficient_data handling upstream).
    composite_level : int
        Composite CMMI level (min of non-insufficient blocks).

    Returns
    -------
    str
        One of: "critical", "high", "medium", "low"
    """
    compliance = block_levels.get("block-6-compliance", 4)
    governance = block_levels.get("block-7-governance", 4)
    data = block_levels.get("block-3-data", 4)

    if compliance <= 1 and governance <= 1:
        return "critical"
    if compliance <= 1 or governance <= 1 or data <= 0:
        return "high"
    if composite_level <= 1:
        return "medium"
    return "low"
