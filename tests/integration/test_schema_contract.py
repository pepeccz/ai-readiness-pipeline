"""
tests/integration/test_schema_contract.py — TD.1

Schema contract validation: assert no question.id ends in `_other_text` (reserved suffix).

All YAML schemas under schemas/questionnaire-v2/ are loaded and validated at module import time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


def _load_all_schemas() -> list[dict[str, Any]]:
    """Load all YAML files from schemas/questionnaire-v2/ recursively."""
    schemas_dir = Path(__file__).parent.parent.parent / "schemas" / "questionnaire-v2"
    schemas = []
    for yaml_file in schemas_dir.rglob("*.yaml"):
        with open(yaml_file) as f:
            schema = yaml.safe_load(f)
            if schema:
                schemas.append((str(yaml_file.relative_to(schemas_dir)), schema))
    return schemas


def _collect_all_question_ids(schema: dict[str, Any], file_path: str) -> list[tuple[str, str]]:
    """
    Recursively collect all question IDs from a schema.
    Returns list of (question_id, file_path) tuples.
    """
    question_ids = []

    def _walk(obj: Any, path: str = ""):
        if isinstance(obj, dict):
            # Check for 'questions' key (top-level or nested)
            if "questions" in obj:
                for question in obj["questions"]:
                    if isinstance(question, dict) and "id" in question:
                        question_ids.append((question["id"], file_path))
                    # Check sub_fields for composite questions
                    if isinstance(question, dict) and "sub_fields" in question:
                        for sub_field in question["sub_fields"]:
                            if isinstance(sub_field, dict) and "id" in sub_field:
                                question_ids.append((sub_field["id"], file_path))
            # Recursively walk other keys
            for key, value in obj.items():
                if key != "questions":
                    _walk(value, path)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, path)

    _walk(schema)
    return question_ids


class TestSchemaContract:
    """Validate schema contracts and conventions."""

    @pytest.fixture(scope="class")
    def all_schemas(self) -> list[tuple[str, dict[str, Any]]]:
        """Load all schemas once per test class."""
        return _load_all_schemas()

    @pytest.fixture(scope="class")
    def all_question_ids(self, all_schemas) -> list[tuple[str, str]]:
        """Collect all question IDs from all schemas."""
        all_ids = []
        for file_path, schema in all_schemas:
            question_ids = _collect_all_question_ids(schema, file_path)
            all_ids.extend(question_ids)
        return all_ids

    def test_no_question_id_ends_with_other_text_suffix(self, all_question_ids):
        """
        REQ-7: No question ID MAY end in '_other_text'.

        This suffix is reserved for companion keys to 'Otro' free-text values.
        Using it on a question ID would cause collision and payload corruption.

        Failure lists all violating question IDs with their source file.
        """
        violations = [
            (qid, file_path)
            for qid, file_path in all_question_ids
            if qid.endswith("_other_text")
        ]

        if violations:
            msg = "Found question IDs ending in reserved suffix '_other_text':\n"
            for qid, file_path in violations:
                msg += f"  {qid} in {file_path}\n"
            pytest.fail(msg)

        # Always pass if no violations
        assert len([qid for qid, _ in all_question_ids if qid.endswith("_other_text")]) == 0
