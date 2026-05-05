"""
tests/unit/test_schema_loader.py — RED tests for schema_loader (T1.1)

Covers:
  1. Load valid YAML without error
  2. Detect duplicate question IDs (raises ValidationError)
  3. Detect missing $ref file (raises FileNotFoundError or RuntimeError)
  4. Detect invalid option.score (negative where not allowed)
  5. Schema object cached after first load (same object, no file re-read)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers — build minimal in-memory YAML dicts
# ---------------------------------------------------------------------------

def _minimal_root(schema_version: str = "1.0") -> dict:
    return {
        "schema_version": schema_version,
        "locale": "es_ES",
        "triage": {
            "id": "triage",
            "layer": "triage",
            "title": "Diagnóstico inicial",
            "questions": [
                {
                    "id": "triage.q.sector",
                    "layer": "triage",
                    "type": "single_choice",
                    "required": True,
                    "label": "Sector",
                    "options": [
                        {"value": "tecnologia", "label": "Tecnología", "score": 18},
                        {"value": "salud", "label": "Salud", "score": 15},
                    ],
                }
            ],
            "scoring": {
                "buckets": [
                    {"name": "auto_accept", "min": 85, "max": 136},
                    {"name": "review", "min": 55, "max": 84},
                    {"name": "cold_warm", "min": 45, "max": 54},
                    {"name": "cold_cool", "min": 30, "max": 44},
                    {"name": "reject_soft", "min": 0, "max": 29},
                ]
            },
            "override_rules": [],
        },
        "core": {
            "blocks_order": [],
            "block_2_variants": {},
            "area_overlays": {},
        },
        "deep": {},
        "override_rules": [],
    }


def _dup_id_root() -> dict:
    root = _minimal_root()
    # Add a second question with the same id
    root["triage"]["questions"].append({
        "id": "triage.q.sector",  # duplicate!
        "layer": "triage",
        "type": "single_choice",
        "required": False,
        "label": "Sector duplicado",
        "options": [{"value": "otro", "label": "Otro", "score": 0}],
    })
    return root


def _negative_score_root() -> dict:
    root = _minimal_root()
    root["triage"]["questions"][0]["options"][0]["score"] = -5
    return root


# ---------------------------------------------------------------------------
# T1.1.1 — Load valid YAML without error
# ---------------------------------------------------------------------------

class TestSchemaLoaderLoad:
    def test_load_valid_schema_returns_root_schema(self, tmp_path: Path):
        from app.services.questionnaire import schema_loader

        root_yaml = tmp_path / "_root.yaml"
        root_yaml.write_text(yaml.dump(_minimal_root()), encoding="utf-8")

        # Reset singleton so we get fresh load
        schema_loader._reset_cache()

        result = schema_loader.load_all(schema_dir=tmp_path)

        assert result is not None
        assert result["schema_version"] == "1.0"

    def test_load_valid_schema_no_exception(self, tmp_path: Path):
        from app.services.questionnaire import schema_loader

        root_yaml = tmp_path / "_root.yaml"
        root_yaml.write_text(yaml.dump(_minimal_root()), encoding="utf-8")
        schema_loader._reset_cache()

        # Should not raise
        schema_loader.load_all(schema_dir=tmp_path)


# ---------------------------------------------------------------------------
# T1.1.2 — Detect duplicate question IDs
# ---------------------------------------------------------------------------

class TestSchemaLoaderDuplicateIds:
    def test_duplicate_question_id_raises(self, tmp_path: Path):
        from app.services.questionnaire import schema_loader

        root_yaml = tmp_path / "_root.yaml"
        root_yaml.write_text(yaml.dump(_dup_id_root()), encoding="utf-8")
        schema_loader._reset_cache()

        with pytest.raises((ValueError, RuntimeError)):
            schema_loader.load_all(schema_dir=tmp_path)


# ---------------------------------------------------------------------------
# T1.1.3 — Detect missing $ref file
# ---------------------------------------------------------------------------

class TestSchemaLoaderMissingRef:
    def test_missing_ref_file_raises(self, tmp_path: Path):
        from app.services.questionnaire import schema_loader

        root_data = _minimal_root()
        # Inject a $ref pointing to a nonexistent file
        root_data["triage"]["questions"].append(
            {"$ref": "./nonexistent_block.yaml#/questions/0"}
        )
        root_yaml = tmp_path / "_root.yaml"
        root_yaml.write_text(yaml.dump(root_data), encoding="utf-8")
        schema_loader._reset_cache()

        with pytest.raises((FileNotFoundError, RuntimeError, ValueError)):
            schema_loader.load_all(schema_dir=tmp_path)


# ---------------------------------------------------------------------------
# T1.1.4 — Detect invalid option.score (negative)
# ---------------------------------------------------------------------------

class TestSchemaLoaderNegativeScore:
    def test_negative_score_raises(self, tmp_path: Path):
        from app.services.questionnaire import schema_loader

        root_yaml = tmp_path / "_root.yaml"
        root_yaml.write_text(yaml.dump(_negative_score_root()), encoding="utf-8")
        schema_loader._reset_cache()

        with pytest.raises((ValueError, RuntimeError)):
            schema_loader.load_all(schema_dir=tmp_path)


# ---------------------------------------------------------------------------
# T1.1.5 — Schema cached after first load (same object, no file re-read)
# ---------------------------------------------------------------------------

class TestSchemaLoaderCache:
    def test_second_call_returns_same_object(self, tmp_path: Path):
        from app.services.questionnaire import schema_loader

        root_yaml = tmp_path / "_root.yaml"
        root_yaml.write_text(yaml.dump(_minimal_root()), encoding="utf-8")
        schema_loader._reset_cache()

        first = schema_loader.load_all(schema_dir=tmp_path)

        # Overwrite YAML — should still return cached result
        root_yaml.write_text(yaml.dump(_minimal_root(schema_version="9.9")), encoding="utf-8")

        second = schema_loader.load_all(schema_dir=tmp_path)

        assert first is second
        assert second["schema_version"] == "1.0"  # cached, not 9.9
