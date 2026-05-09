"""
app/services/scoring/scorer.py

Block-level scoring — pure deterministic function.

score_block(payload, block_rubric) → BlockScore

Algorithm:
  For each Indicator in block_rubric.indicators:
    1. Resolve the answer value from payload (handling composite sub-fields).
    2. Look up the option score from indicator.option_scores.
    3. Accumulate: raw += option_score * indicator.weight
    4. Count answered indicators.
  normalized = raw / sum(max_score * weight for all indicators)
  normalized is clamped to [0, 1] to guard against YAML misconfiguration.

Free-text (textarea/text) sub-fields do NOT appear in BlockRubric.indicators;
they are handled by the guards layer only. This scorer is purely numeric.
"""

from __future__ import annotations

from app.services.scoring.rubric import BlockRubric, BlockScore


def score_block(payload: dict, block_rubric: BlockRubric) -> BlockScore:
    """
    Compute the numeric score for a single block.

    Parameters
    ----------
    payload : dict
        The block's submitted answer payload. Shape mirrors the block YAML:
        top-level keys are question IDs; composite questions contain nested dicts.
    block_rubric : BlockRubric
        The rubric definition including all scorable Indicator objects.

    Returns
    -------
    BlockScore
        raw: weighted sum of earned scores.
        normalized: raw / total_max_weighted, clamped to [0, 1].
        answered_count: number of indicators with a non-empty answer.
    """
    if not block_rubric.indicators:
        return BlockScore(raw=0.0, normalized=0.0, answered_count=0, block_id=block_rubric.block_id)

    raw_score = 0.0
    answered_count = 0
    total_max_weighted = sum(
        ind.max_score * ind.weight for ind in block_rubric.indicators
    )

    for indicator in block_rubric.indicators:
        value = _resolve_answer(payload, indicator)
        if value is None:
            # Unanswered indicator → contributes 0 to raw_score (already excluded)
            continue

        if isinstance(value, list):
            # multi_choice: sum scores for each selected option, cap at max_score
            option_score_sum = sum(
                indicator.option_scores.get(str(v), 0.0) for v in value
            )
            option_score = min(option_score_sum, indicator.max_score)
        else:
            option_score = indicator.option_scores.get(value, 0.0)

        raw_score += option_score * indicator.weight
        answered_count += 1

    if total_max_weighted == 0.0:
        normalized = 0.0
    else:
        normalized = raw_score / total_max_weighted
        # Clamp defensively — should not be needed with correct YAML
        normalized = max(0.0, min(1.0, normalized))

    return BlockScore(
        raw=raw_score,
        normalized=normalized,
        answered_count=answered_count,
        block_id=block_rubric.block_id,
    )


def _resolve_answer(payload: dict, indicator) -> "str | list | None":
    """
    Extract the answer value from the payload for the given indicator.

    For composite sub-fields, looks up payload[composite_parent][indicator.id].
    For top-level questions, looks up payload[indicator.id].

    Returns:
    - None if the answer is absent or empty (None, "", [], {}).
    - A list[str] if the value is a list (multi_choice answer).
    - A str for scalar answers (single_choice, text, etc.).

    Multi_choice handling: the caller (score_block) detects list return values
    and sums the scores of each selected option, capped at indicator.max_score.
    """
    if indicator.composite_parent:
        parent_value = payload.get(indicator.composite_parent)
        if not isinstance(parent_value, dict):
            return None
        value = parent_value.get(indicator.id)
    else:
        value = payload.get(indicator.id)

    if _is_empty(value):
        return None

    # Return lists as-is for multi_choice aggregation in score_block
    if isinstance(value, list):
        return value  # type: ignore[return-value]

    return str(value)


def _is_empty(value) -> bool:
    """Return True if value is considered absent/empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False
