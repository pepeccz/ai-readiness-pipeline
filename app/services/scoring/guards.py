"""
app/services/scoring/guards.py

Empty-input guard for AIR block synthesis.

Functions:
    is_block_synthesizable(block_yaml, payload) → (bool, list[str])
    list_missing_critical_fields(block_yaml, payload) → list[str]
    _is_empty(value) → bool

Purpose:
    Before calling the LLM for block synthesis, BlockAnalyzer calls
    is_block_synthesizable. If the block has unfilled critical fields,
    the analyzer short-circuits to status=insufficient_data without any
    LLM call.

Critical field authoring:
    Block YAML questions or sub_fields marked with critical_for_synthesis: true
    will be checked. Free-text fields (textarea/text) may be critical for
    synthesis even though they don't contribute a score.

Defensive rules:
    - A composite question whose ALL sub_fields are empty triggers insufficient_data
      regardless of critical_for_synthesis flags (no data = no synthesis).
    - Missing key in payload is treated same as empty value.
    - Types None, "", [], {} are all considered empty.
"""

from __future__ import annotations

from typing import Any


def _is_empty(value: Any) -> bool:
    """
    Return True if value is considered absent/empty for synthesis purposes.

    Empty conditions:
      - None
      - Empty string (including whitespace-only)
      - Empty list []
      - Empty dict {}
      - Missing key (caller handles this by passing None)

    Non-empty:
      - Integer 0 (a valid score)
      - Boolean False (a valid answer)
      - Non-empty string, list, or dict
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def is_block_synthesizable(
    block_yaml: dict,
    payload: dict,
) -> tuple[bool, list[str]]:
    """
    Determine whether a block has sufficient data for LLM synthesis.

    Parameters
    ----------
    block_yaml : dict
        The parsed block YAML (containing a "questions" list).
    payload : dict
        The submitted payload for this block.

    Returns
    -------
    tuple[bool, list[str]]
        (True, []) if the block can be synthesized.
        (False, [list of missing field paths]) if synthesis should be skipped.

    Field path format:
        Top-level critical field: "question_id"
        Composite sub-field: "composite_question_id.sub_field_id"
    """
    missing = list_missing_critical_fields(block_yaml, payload)
    return (len(missing) == 0, missing)


def list_missing_critical_fields(
    block_yaml: dict,
    payload: dict,
) -> list[str]:
    """
    Return a list of missing critical field paths in the given payload.

    Checks:
    1. Top-level questions with critical_for_synthesis: true → missing if payload[q.id] is empty
    2. Composite questions: each sub_field with critical_for_synthesis: true → missing if
       payload[q.id][sf.id] is empty or if the parent composite value itself is empty/null.
    3. Defensive: composite question whose ALL sub_fields are empty/missing → add parent path.

    Parameters
    ----------
    block_yaml : dict
        The parsed block YAML.
    payload : dict
        The submitted payload for this block.

    Returns
    -------
    list[str]
        List of missing critical field paths (dot-notation for composite sub-fields).
    """
    missing: list[str] = []
    questions = block_yaml.get("questions", [])

    for question in questions:
        q_id: str = question["id"]
        q_type: str = question.get("type", "")

        if q_type == "composite":
            parent_value = payload.get(q_id)

            # Defensive: if the entire composite block is empty (None or {})
            # check for any critical sub-fields inside
            sub_fields = question.get("sub_fields", [])

            if _is_empty(parent_value):
                # If any sub-field is critical, all are considered missing
                for sf in sub_fields:
                    if sf.get("critical_for_synthesis"):
                        missing.append(f"{q_id}.{sf['id']}")
            else:
                # parent_value is a non-empty dict — check each critical sub-field
                if not isinstance(parent_value, dict):
                    parent_value = {}

                for sf in sub_fields:
                    if sf.get("critical_for_synthesis"):
                        sf_id = sf["id"]
                        sf_value = parent_value.get(sf_id)
                        if _is_empty(sf_value):
                            missing.append(f"{q_id}.{sf_id}")

        else:
            # Top-level question (single_choice, multi_choice, text, textarea, etc.)
            if question.get("critical_for_synthesis"):
                value = payload.get(q_id)
                if _is_empty(value):
                    missing.append(q_id)

    return missing
