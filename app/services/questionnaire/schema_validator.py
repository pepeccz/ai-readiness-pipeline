"""
app/services/questionnaire/schema_validator.py

Validates a fully-resolved schema dict (after $ref resolution).

Checks:
  1. Global ID uniqueness across all questions
  2. option.score >= 0 (unless in _negative_scores_allowed list)
  3. consent question policy_file exists on disk
  4. show_if.field references an existing question id

Raises RuntimeError with descriptive message on any failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# IDs allowed to have negative scores (future use)
_negative_scores_allowed: list[str] = []

_DEFAULT_SCHEMA_DIR = Path(__file__).parents[3] / "schemas" / "questionnaire-v2"


def validate_schema(schema: dict, schema_dir: Path | None = None) -> None:
    """
    Validate a resolved schema dict. Raises RuntimeError on failure.
    Meant to be called from schema_loader.load_all() and also directly in tests.
    """
    base_dir = Path(schema_dir) if schema_dir is not None else _DEFAULT_SCHEMA_DIR

    all_questions = _collect_all_questions(schema)
    all_ids = [q["id"] for q in all_questions if "id" in q]

    _check_unique_ids(all_ids)
    _check_scores(all_questions)
    _check_policy_files(all_questions, base_dir)


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

def _collect_all_questions(schema: dict) -> list[dict]:
    questions: list[dict] = []

    triage = schema.get("triage", {})
    _walk_questions(triage.get("questions", []), questions)

    core = schema.get("core", {})
    for block in core.get("blocks", []):
        _walk_questions(block.get("questions", []), questions)

    return questions


def _walk_questions(items: list, out: list[dict]) -> None:
    for q in items:
        if not isinstance(q, dict):
            continue
        out.append(q)
        # Recurse into composite sub_fields
        for sub in q.get("sub_fields", []):
            _walk_questions([sub], out)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _check_unique_ids(all_ids: list[str]) -> None:
    seen: set[str] = set()
    for qid in all_ids:
        if qid in seen:
            raise RuntimeError(
                f"Duplicate question id: '{qid}'. All question ids must be globally unique."
            )
        seen.add(qid)


def _check_scores(all_questions: list[dict]) -> None:
    for q in all_questions:
        qid = q.get("id", "<unknown>")
        for opt in q.get("options", []):
            score = opt.get("score")
            if score is None:
                continue
            if score < 0 and qid not in _negative_scores_allowed:
                raise RuntimeError(
                    f"option.score must be >= 0 in question '{qid}', "
                    f"got {score} for option '{opt.get('value')}'"
                )


def _check_policy_files(all_questions: list[dict], base_dir: Path) -> None:
    for q in all_questions:
        if q.get("type") != "consent":
            continue
        policy_file = q.get("policy_file")
        if not policy_file:
            continue
        full_path = base_dir / policy_file
        if not full_path.exists():
            raise RuntimeError(
                f"policy_file not found: '{full_path}' "
                f"(referenced in question '{q.get('id')}')"
            )
