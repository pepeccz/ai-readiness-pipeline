"""
app/services/deep/trigger_detector — Detects activated DEEP branches from CORE answers.

Reads deep_branches arrays attached to individual option values in YAML block schemas.
For each block payload, inspects which options were selected and returns the union of
all deep_branches declared on those options.

This is a pure, stateless class — no DB, no LLM, no side effects.
"""

from __future__ import annotations

from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Schema path
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).parents[3] / "schemas" / "questionnaire-v2" / "core"


def _load_block_yaml(block_id: str) -> dict | None:
    """Load raw YAML for a block. Returns None if file not found."""
    path = _SCHEMA_DIR / f"{block_id}.yaml"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _collect_deep_branches_from_schema(schema: dict, payload: dict) -> set[str]:
    """
    Walk all questions in schema, checking selected option values against payload.

    For each question that has options with deep_branches, if the payload contains
    that option value (as a direct value or within a list), add those branches.
    """
    branches: set[str] = set()
    questions = schema.get("questions", [])
    _walk_questions(questions, payload, branches)
    return branches


def _walk_questions(questions: list, payload: dict, branches: set[str]) -> None:
    """Recursively walk questions (including composite sub_fields)."""
    for q in questions:
        if not isinstance(q, dict):
            continue

        qid = q.get("id")
        q_type = q.get("type", "")

        if q_type == "composite":
            sub_fields = q.get("sub_fields", [])
            _walk_questions(sub_fields, payload, branches)
            continue

        options = q.get("options", [])
        if not options or qid is None:
            continue

        selected = payload.get(qid)
        if selected is None:
            continue

        # Normalize to list for multi_choice
        if isinstance(selected, list):
            selected_values = set(selected)
        else:
            selected_values = {selected}

        for option in options:
            if not isinstance(option, dict):
                continue
            opt_value = option.get("value")
            opt_branches = option.get("deep_branches", [])
            if opt_value in selected_values and opt_branches:
                branches.update(opt_branches)


class TriggerDetector:
    """Detect DEEP branches activated by CORE block answers."""

    @staticmethod
    def detect_from_block_payload(block_id: str, payload: dict) -> set[str]:
        """
        Return set of deep branch IDs triggered by the given block payload.

        Returns empty set if block YAML not found or payload has no triggering answers.
        """
        schema = _load_block_yaml(block_id)
        if schema is None:
            return set()
        return _collect_deep_branches_from_schema(schema, payload)

    @staticmethod
    def detect_from_all_blocks(block_payloads: dict[str, dict]) -> set[str]:
        """
        Return union of all deep branch IDs triggered across multiple blocks.

        Args:
            block_payloads: {block_id: payload_dict} mapping.
        """
        all_branches: set[str] = set()
        for block_id, payload in block_payloads.items():
            all_branches |= TriggerDetector.detect_from_block_payload(block_id, payload)
        return all_branches
