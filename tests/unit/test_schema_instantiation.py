"""
tests/unit/test_schema_instantiation.py — T5.1 (TDD RED)

Tests for CORE schema instantiation and area-based personalization.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


SCHEMA_DIR = Path(__file__).parents[2] / "schemas" / "questionnaire-v2" / "core"


class TestCoreBlocksExist:
    """All 7 core block files must exist and be valid YAML."""

    @pytest.mark.parametrize("filename", [
        "block-1-strategic.yaml",
        "block-2-process-critical-full.yaml",
        "block-2-process-critical-reduced.yaml",
        "block-2-process-critical-cross-area.yaml",
        "block-3-data.yaml",
        "block-4-talent.yaml",
        "block-5-infrastructure.yaml",
        "block-6-compliance.yaml",
        "block-7-governance.yaml",
        "_index.yaml",
    ])
    def test_file_exists(self, filename: str):
        path = SCHEMA_DIR / filename
        assert path.exists(), f"Missing block file: {path}"

    @pytest.mark.parametrize("filename", [
        "block-1-strategic.yaml",
        "block-2-process-critical-full.yaml",
        "block-2-process-critical-reduced.yaml",
        "block-2-process-critical-cross-area.yaml",
        "block-3-data.yaml",
        "block-4-talent.yaml",
        "block-5-infrastructure.yaml",
        "block-6-compliance.yaml",
        "block-7-governance.yaml",
    ])
    def test_block_has_required_fields(self, filename: str):
        path = SCHEMA_DIR / filename
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "id" in data, f"Missing 'id' in {filename}"
        assert "layer" in data, f"Missing 'layer' in {filename}"
        assert data["layer"] == "core", f"Expected layer=core in {filename}"
        assert "questions" in data, f"Missing 'questions' in {filename}"
        assert isinstance(data["questions"], list), f"'questions' must be a list in {filename}"
        assert len(data["questions"]) > 0, f"'questions' must not be empty in {filename}"

    def test_block1_has_correct_question_ids(self):
        path = SCHEMA_DIR / "block-1-strategic.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        question_ids = [q["id"] for q in data["questions"]]
        assert "q1_1_objective" in question_ids
        assert "q1_2_sponsor" in question_ids
        assert "q1_3_previous" in question_ids
        assert "q1_4_appetite" in question_ids

    def test_block2_full_has_5_plus_questions(self):
        path = SCHEMA_DIR / "block-2-process-critical-full.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["questions"]) >= 5

    def test_block2_reduced_has_3_questions(self):
        path = SCHEMA_DIR / "block-2-process-critical-reduced.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Reduced: Q2.1 + Q2.2 + Q2.4
        assert len(data["questions"]) == 3

    def test_block2_cross_area_has_area_selector(self):
        path = SCHEMA_DIR / "block-2-process-critical-cross-area.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        question_ids = [q["id"] for q in data["questions"]]
        # Must have areas_involved question
        assert "areas_involved" in question_ids

    def test_index_has_blocks_order(self):
        path = SCHEMA_DIR / "_index.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "area_selector" in data, "Index must have area_selector section"
        assert "blocks_order" in data, "Index must have blocks_order"
        assert isinstance(data["blocks_order"], list)
        assert len(data["blocks_order"]) == 7


class TestAreaSelectorStructure:
    """Area selector questions must match spec."""

    def test_area_selector_has_primary_area(self):
        path = SCHEMA_DIR / "_index.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        questions = data["area_selector"]["questions"]
        ids = [q["id"] for q in questions]
        assert "primary_area" in ids

    def test_primary_area_has_required_options(self):
        path = SCHEMA_DIR / "_index.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        questions = data["area_selector"]["questions"]
        primary = next(q for q in questions if q["id"] == "primary_area")
        assert primary["required"] is True
        option_values = [o["value"] for o in primary["options"]]
        for expected in ["attention", "marketing", "sales", "operations", "finance", "hr", "product"]:
            assert expected in option_values, f"Missing area option: {expected}"
        assert "cross_area_communication" in option_values

    def test_secondary_area_has_show_if(self):
        path = SCHEMA_DIR / "_index.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        questions = data["area_selector"]["questions"]
        ids = [q["id"] for q in questions]
        if "secondary_area" in ids:
            secondary = next(q for q in questions if q["id"] == "secondary_area")
            assert "show_if" in secondary

    def test_areas_involved_show_if_cross_area(self):
        path = SCHEMA_DIR / "_index.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        questions = data["area_selector"]["questions"]
        ids = [q["id"] for q in questions]
        if "areas_involved" in ids:
            q = next(q for q in questions if q["id"] == "areas_involved")
            assert "show_if" in q


class TestBlockDeepTriggers:
    """Key blocks must have deep_triggers defined."""

    def test_block1_has_deep_triggers(self):
        path = SCHEMA_DIR / "block-1-strategic.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "deep_triggers" in data
        assert len(data["deep_triggers"]) > 0

    def test_block2_has_closing_analysis(self):
        path = SCHEMA_DIR / "block-2-process-critical-full.yaml"
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "closing_analysis" in data
