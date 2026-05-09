"""
app/services/scoring/loader.py

Loads and validates the AIR scoring rubric registry from YAML.

The registry lives at schemas/rubric/{version}/registry.yaml.
Versioning is done at the directory level; the `version` parameter selects the
directory (e.g. "v1" → schemas/rubric/v1/registry.yaml).

Also provides load_block_rubric(block_id) → BlockRubric which reads the block
questionnaire YAML from schemas/questionnaire-v2/core/<block_id>.yaml and
builds a BlockRubric containing Indicator objects for every scorable sub-field.

Usage:
    registry = load_registry("v1")
    block_rubric = load_block_rubric("block-4-talent")
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from app.services.scoring.rubric import BlockRubric, Indicator, Registry

# Project root derived from this file's location:
# app/services/scoring/loader.py → parents[3] = project root
_PROJECT_ROOT = Path(__file__).parents[3]
_RUBRIC_BASE = _PROJECT_ROOT / "schemas" / "rubric"
_BLOCK_YAML_DIR = _PROJECT_ROOT / "schemas" / "questionnaire-v2" / "core"


def _validate_registry(data: dict[str, Any], version: str) -> None:
    """Raise ValueError if the registry YAML is missing required keys."""
    required_keys = {"block_weights", "cmmi_thresholds", "risk_gates", "schema_version"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(
            f"Malformed registry for version '{version}': missing keys {missing}"
        )

    # cmmi_thresholds must have exactly the 5 named levels
    required_levels = {"inicial", "emergente", "establecido", "avanzado", "optimizado"}
    actual_levels = set(data["cmmi_thresholds"].keys())
    if actual_levels != required_levels:
        raise ValueError(
            f"cmmi_thresholds must have exactly {required_levels}, got {actual_levels}"
        )

    # Each level must have min/max
    for level, bounds in data["cmmi_thresholds"].items():
        if "min" not in bounds or "max" not in bounds:
            raise ValueError(
                f"cmmi_thresholds['{level}'] missing 'min' or 'max': {bounds}"
            )


@functools.lru_cache(maxsize=8)
def load_registry(version: str) -> Registry:
    """
    Load and return the rubric Registry for the given version string.

    Parameters
    ----------
    version : str
        Version directory name, e.g. "v1".

    Returns
    -------
    Registry
        Validated, immutable Registry dataclass.

    Raises
    ------
    FileNotFoundError
        If the registry YAML file does not exist for the given version.
    ValueError
        If the registry YAML is malformed (missing required keys).
    """
    registry_path = _RUBRIC_BASE / version / "registry.yaml"
    if not registry_path.exists():
        raise FileNotFoundError(
            f"No rubric registry found for version '{version}' "
            f"(expected: {registry_path})"
        )

    with registry_path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)

    _validate_registry(data, version)

    return Registry(
        block_weights=data["block_weights"],
        cmmi_thresholds=data["cmmi_thresholds"],
        risk_gates=data["risk_gates"],
        schema_version=int(data["schema_version"]),
    )


# ---------------------------------------------------------------------------
# Block YAML → BlockRubric loader (WARNING-02 fix)
# ---------------------------------------------------------------------------

def _extract_option_scores(options: list[dict]) -> dict[str, float]:
    """
    Build a {option_value → score} dict from a YAML options list.

    Only options with a 'score' key are included. Options without 'score'
    are intentionally excluded (they have no numeric contribution).
    """
    result: dict[str, float] = {}
    for opt in options or []:
        if "score" in opt and "value" in opt:
            result[str(opt["value"])] = float(opt["score"])
    return result


def _max_score_from_options(options: list[dict]) -> float:
    """
    Return the maximum score value across all options.
    For multi_choice, the max is the sum of all positive option scores
    (since any combination can be selected). We store it as the sum of
    all positive-score options to allow proper cap enforcement at score time.
    For single_choice, it's just the max option score.

    We use the sum of all positive scores for multi_choice because the
    scorer caps the raw contribution at max_score anyway.
    """
    scores = [float(opt["score"]) for opt in (options or []) if "score" in opt]
    if not scores:
        return 0.0
    return max(scores)


def _max_score_multi_choice(options: list[dict]) -> float:
    """
    For multi_choice: max_score = sum of all positive option scores.
    This reflects the theoretical maximum a respondent could earn by
    selecting all positively-scored options.
    """
    return sum(
        float(opt["score"])
        for opt in (options or [])
        if "score" in opt and float(opt["score"]) > 0
    )


def _indicators_from_question(
    question: dict[str, Any],
    composite_parent: str | None = None,
) -> list[Indicator]:
    """
    Recursively extract Indicator objects from a question dict.

    Rules:
    - composite questions: recurse into sub_fields; parent itself is not an Indicator
    - single_choice / multi_choice with score: on options → produces one Indicator
    - text / textarea → no Indicator (free-text has no numeric score)
    - weight: on question is carried onto the Indicator (default 1.0)
    """
    indicators: list[Indicator] = []
    q_type = question.get("type", "")
    q_id = question.get("id", "")
    options = question.get("options", [])

    if q_type == "composite":
        # Recurse into sub_fields; this question node is the composite parent
        parent_id = q_id if composite_parent is None else composite_parent
        for sub_field in question.get("sub_fields", []):
            # Nested composites (e.g. q5_2_vendor_1 inside q5_2_vendors):
            # treat the outermost composite as the parent for payload lookup
            sub_indicators = _indicators_from_question(sub_field, composite_parent=parent_id)
            indicators.extend(sub_indicators)
        return indicators

    # For scored leaf questions (single_choice, multi_choice with score:)
    scored_options = [opt for opt in options if "score" in opt]
    if not scored_options:
        # No scored options → skip (text/textarea/unscored fields)
        return indicators

    option_scores = _extract_option_scores(options)
    weight = float(question.get("weight", 1.0))

    # max_score differs between single_choice and multi_choice
    if q_type == "multi_choice":
        max_score = _max_score_multi_choice(options)
    else:
        max_score = _max_score_from_options(options)

    # Explicit YAML override for max_score (rubric tuning).
    # Use case: multi_choice indicators where the auto-derived sum-of-positives
    # ceiling is unrealistically high for typical respondents (e.g. q4_1_profiles
    # in a small company can only realistically tick 1-2 profiles, not all 6).
    if "max_score" in question:
        max_score = float(question["max_score"])

    indicators.append(
        Indicator(
            id=q_id,
            weight=weight,
            max_score=max_score,
            option_scores=option_scores,
            composite_parent=composite_parent,
        )
    )
    return indicators


# Mapping from canonical block_id (as used in registry.yaml + session logic)
# to the actual YAML filename (without .yaml extension).
# Only entries that differ from the canonical id are needed.
_BLOCK_ID_TO_YAML_NAME: dict[str, str] = {
    "block-2-process-critical": "block-2-process-critical-full",
}


@functools.lru_cache(maxsize=32)
def load_block_rubric(block_id: str) -> BlockRubric:
    """
    Load a BlockRubric from the questionnaire YAML for the given block_id.

    Reads schemas/questionnaire-v2/core/<block_id>.yaml (or the mapped name
    for blocks whose YAML filename differs from the canonical block_id) and
    walks all questions (including composite sub_fields recursively). For each
    question with options that carry a 'score:' attribute, one Indicator
    is produced.

    Multi_choice indicators: max_score = sum of all positive option scores.
    Single_choice indicators: max_score = maximum option score.
    Composite questions: excluded from scoring; their sub_fields become Indicators
    with composite_parent set to the composite question id.

    Parameters
    ----------
    block_id : str
        Canonical block identifier, e.g. "block-4-talent" or "block-2-process-critical".

    Returns
    -------
    BlockRubric
        Ready to feed into score_block().

    Raises
    ------
    FileNotFoundError
        If no YAML file is found for the given block_id.
    """
    yaml_name = _BLOCK_ID_TO_YAML_NAME.get(block_id, block_id)
    yaml_path = _BLOCK_YAML_DIR / f"{yaml_name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"No block YAML found for '{block_id}' (expected: {yaml_path})"
        )

    with yaml_path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)

    questions = data.get("questions", [])
    indicators: list[Indicator] = []
    for question in questions:
        indicators.extend(_indicators_from_question(question, composite_parent=None))

    return BlockRubric(block_id=block_id, indicators=indicators)
