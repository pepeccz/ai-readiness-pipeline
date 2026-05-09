"""
app/services/scoring/rubric.py

Typed dataclasses for the AIR scoring rubric system.

All types are pure data — no DB access, no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CMMIBounds:
    """Min/max normalized score bounds for a CMMI level."""

    min: float
    max: float

    def contains(self, score: float) -> bool:
        return self.min <= score < self.max


@dataclass(frozen=True)
class Indicator:
    """
    A single scorable indicator within a block question.

    id: question id (or sub-field id within a composite question)
    weight: multiplier applied to the option score (default 1.0)
    max_score: maximum possible option score for this indicator
    option_scores: maps option value (str) → numeric score (int/float)
    composite_parent: if set, this indicator is a sub-field of the named
        composite question. The payload lookup is payload[composite_parent][id].
    """

    id: str
    weight: float = 1.0
    max_score: float = 0.0
    option_scores: dict[str, float] = field(default_factory=dict)
    composite_parent: str | None = None


@dataclass(frozen=True)
class BlockRubric:
    """
    Rubric data for a single block.

    block_id: canonical block id (e.g. "block-1-strategic")
    indicators: list of Indicator objects for each scorable question/sub-field
    """

    block_id: str
    indicators: list[Indicator] = field(default_factory=list)


@dataclass(frozen=True)
class BlockScore:
    """
    Scoring result for a single block.

    raw: weighted sum of option_score * indicator_weight for answered indicators
    normalized: raw / total_max_weighted (always in [0, 1])
    answered_count: number of indicators that had a non-empty answer
    block_id: the block this score belongs to
    status: "scored" or "insufficient_data" (set by guards layer, not scorer)
    """

    raw: float
    normalized: float
    answered_count: int
    block_id: str = ""
    status: str = "scored"


@dataclass(frozen=True)
class Registry:
    """
    Central registry loaded from schemas/rubric/v1/registry.yaml.

    block_weights: maps block_id → float weight for composite calculation
    cmmi_thresholds: maps level_name → {"min": float, "max": float}
    risk_gates: deterministic rules for risk profile derivation
    schema_version: integer version of the registry schema
    """

    block_weights: dict[str, float]
    cmmi_thresholds: dict[str, dict[str, float]]
    risk_gates: dict[str, Any]
    schema_version: int
