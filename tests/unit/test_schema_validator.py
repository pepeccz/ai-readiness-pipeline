"""
tests/unit/test_schema_validator.py — RED tests for schema_validator (T1.5)

Covers:
  - dup IDs abort (RuntimeError)
  - missing policy_file abort (RuntimeError)
  - score negative abort (RuntimeError)
"""

from __future__ import annotations

import pytest


def _base_schema() -> dict:
    return {
        "schema_version": "1.0",
        "locale": "es_ES",
        "triage": {
            "id": "triage",
            "layer": "triage",
            "title": "TRIAGE",
            "questions": [
                {
                    "id": "triage.q.sector",
                    "layer": "triage",
                    "type": "single_choice",
                    "required": True,
                    "label": "Sector",
                    "options": [
                        {"value": "tecnologia", "label": "Tecnología", "score": 18},
                    ],
                }
            ],
            "scoring": {
                "buckets": [
                    {"name": "auto_accept", "min": 85, "max": 136},
                ]
            },
            "override_rules": [],
        },
        "core": {"blocks_order": [], "block_2_variants": {}, "area_overlays": {}},
        "deep": {},
        "override_rules": [],
    }


class TestSchemaValidatorDupIds:
    def test_dup_question_ids_raises(self):
        from app.services.questionnaire.schema_validator import validate_schema

        schema = _base_schema()
        # Add a duplicate
        schema["triage"]["questions"].append({
            "id": "triage.q.sector",  # duplicate!
            "layer": "triage",
            "type": "single_choice",
            "required": False,
            "label": "Sector 2",
            "options": [{"value": "otro", "label": "Otro", "score": 0}],
        })

        with pytest.raises(RuntimeError, match="Duplicate"):
            validate_schema(schema)


class TestSchemaValidatorMissingPolicyFile:
    def test_consent_with_missing_policy_file_raises(self, tmp_path):
        from app.services.questionnaire.schema_validator import validate_schema

        schema = _base_schema()
        schema["triage"]["questions"].append({
            "id": "triage.q.privacy",
            "layer": "triage",
            "type": "consent",
            "required": True,
            "label": "Acepto",
            "policy_version": "v1.0-2026-05",
            "policy_file": "consents/privacy-nonexistent.md",
        })

        with pytest.raises(RuntimeError, match="policy_file"):
            validate_schema(schema, schema_dir=tmp_path)


class TestSchemaValidatorNegativeScore:
    def test_negative_score_raises(self):
        from app.services.questionnaire.schema_validator import validate_schema

        schema = _base_schema()
        schema["triage"]["questions"][0]["options"][0]["score"] = -1

        with pytest.raises(RuntimeError, match="score"):
            validate_schema(schema)
