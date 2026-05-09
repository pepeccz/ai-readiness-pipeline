"""
tests/services/scoring/test_guards.py

RED phase — A.11

Tests for is_block_synthesizable(block_yaml, payload) → (bool, list[str]).

The canonical regression fixture is Pepe Cabeza SL:
  block-3-data payload where q3_2_quality: {} (empty composite)
  → should return (False, ["q3_2_quality.q3_2_level"])

Also tests:
  - Fully populated payload returns (True, [])
  - _is_empty handles None, "", [], {}, missing key
"""

from __future__ import annotations

import pytest

from app.services.scoring.guards import is_block_synthesizable, _is_empty


# ---------------------------------------------------------------------------
# Fixtures — block YAML structures (minimal, sufficient for guard tests)
# ---------------------------------------------------------------------------

def make_block3_yaml() -> dict:
    """
    Minimal block-3-data YAML structure for guard tests.
    Canonical critical fields: q3_1_sources, q3_2_quality.q3_2_level
    """
    return {
        "id": "block-3-data",
        "questions": [
            {
                "id": "q3_1_sources",
                "type": "multi_choice",
                "critical_for_synthesis": True,
            },
            {
                "id": "q3_2_quality",
                "type": "composite",
                "sub_fields": [
                    {
                        "id": "q3_2_level",
                        "type": "single_choice",
                        "critical_for_synthesis": True,
                    },
                    {
                        "id": "q3_2_example",
                        "type": "text",
                        "critical_for_synthesis": False,
                    },
                ],
            },
            {
                "id": "q3_5_accessibility",
                "type": "single_choice",
                # NOT critical_for_synthesis — absence does not block synthesis
            },
        ],
    }


def make_block1_yaml() -> dict:
    """
    Minimal block-1-strategic YAML structure for guard tests.
    Critical fields: q1_1_outcome, q1_1_metric (sub-fields), q1_2_sponsor
    """
    return {
        "id": "block-1-strategic",
        "questions": [
            {
                "id": "q1_1_objective",
                "type": "composite",
                "sub_fields": [
                    {
                        "id": "q1_1_outcome",
                        "type": "textarea",
                        "critical_for_synthesis": True,
                    },
                    {
                        "id": "q1_1_metric",
                        "type": "text",
                        "critical_for_synthesis": True,
                    },
                    {
                        "id": "q1_1_timeframe",
                        "type": "single_choice",
                        # NOT critical for synthesis
                    },
                ],
            },
            {
                "id": "q1_2_sponsor",
                "type": "single_choice",
                "critical_for_synthesis": True,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tests: Pepe Cabeza SL canonical regression fixture
# ---------------------------------------------------------------------------

class TestPepeCabezaCanonicalFixture:
    def test_empty_q3_2_quality_returns_not_synthesizable(self):
        """
        Pepe Cabeza SL fixture: q3_2_quality: {} (empty composite dict)
        → (False, ["q3_2_quality.q3_2_level"])
        """
        block_yaml = make_block3_yaml()
        payload = {
            "q3_1_sources": ["erp", "bbdd_propia"],
            "q3_2_quality": {},  # <-- Canonical empty composite (Pepe Cabeza SL case)
            "q3_5_accessibility": "api_directo",
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is False
        assert "q3_2_quality.q3_2_level" in missing

    def test_empty_q3_2_quality_missing_list_has_correct_format(self):
        """Missing field format is 'parent_id.sub_field_id'."""
        block_yaml = make_block3_yaml()
        payload = {
            "q3_1_sources": ["erp"],
            "q3_2_quality": {},
        }
        _, missing = is_block_synthesizable(block_yaml, payload)
        # Format must be 'composite_id.subfield_id'
        for field_path in missing:
            assert "." in field_path, f"Expected dot-notation, got: {field_path}"

    def test_null_q3_2_quality_is_also_not_synthesizable(self):
        """q3_2_quality: null also triggers insufficient_data."""
        block_yaml = make_block3_yaml()
        payload = {
            "q3_1_sources": ["erp"],
            "q3_2_quality": None,
        }
        synthesizable, _ = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is False

    def test_q3_2_quality_with_valid_level_is_synthesizable(self):
        """When q3_2_quality.q3_2_level is present → synthesizable (assuming sources also present)."""
        block_yaml = make_block3_yaml()
        payload = {
            "q3_1_sources": ["erp"],
            "q3_2_quality": {
                "q3_2_level": "buena",
                "q3_2_example": "",  # empty optional field is ok
            },
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is True
        assert missing == []


# ---------------------------------------------------------------------------
# Tests: Fully populated payloads
# ---------------------------------------------------------------------------

class TestFullyPopulatedPayload:
    def test_full_block3_payload_is_synthesizable(self):
        """All critical fields present → (True, [])."""
        block_yaml = make_block3_yaml()
        payload = {
            "q3_1_sources": ["erp", "crm"],
            "q3_2_quality": {
                "q3_2_level": "excelente",
                "q3_2_example": "No hay problemas significativos",
            },
            "q3_5_accessibility": "api_directo",
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is True
        assert missing == []

    def test_full_block1_payload_is_synthesizable(self):
        """Block-1 fully populated → (True, [])."""
        block_yaml = make_block1_yaml()
        payload = {
            "q1_1_objective": {
                "q1_1_outcome": "Reducir tiempo de respuesta al cliente un 40%",
                "q1_1_metric": "Tiempo medio en CRM",
                "q1_1_timeframe": "12m",
            },
            "q1_2_sponsor": "ceo_total",
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is True
        assert missing == []


# ---------------------------------------------------------------------------
# Tests: Various missing critical fields
# ---------------------------------------------------------------------------

class TestMissingCriticalFields:
    def test_missing_top_level_critical_field(self):
        """q1_2_sponsor absent → (False, ['q1_2_sponsor'])."""
        block_yaml = make_block1_yaml()
        payload = {
            "q1_1_objective": {
                "q1_1_outcome": "Reducir costes",
                "q1_1_metric": "EUR / operación",
                "q1_1_timeframe": "6m",
            },
            # q1_2_sponsor absent
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is False
        assert "q1_2_sponsor" in missing

    def test_missing_composite_sub_field(self):
        """q1_1_outcome absent in composite → (False, ['q1_1_objective.q1_1_outcome'])."""
        block_yaml = make_block1_yaml()
        payload = {
            "q1_1_objective": {
                # q1_1_outcome missing
                "q1_1_metric": "Tiempo medio en CRM",
                "q1_1_timeframe": "12m",
            },
            "q1_2_sponsor": "ceo_total",
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is False
        assert "q1_1_objective.q1_1_outcome" in missing

    def test_multiple_missing_critical_fields(self):
        """Multiple missing critical fields all appear in missing list."""
        block_yaml = make_block3_yaml()
        payload = {
            # q3_1_sources absent (critical)
            "q3_2_quality": {},  # q3_2_level absent (critical)
        }
        synthesizable, missing = is_block_synthesizable(block_yaml, payload)
        assert synthesizable is False
        assert len(missing) >= 2


# ---------------------------------------------------------------------------
# Tests: _is_empty helper
# ---------------------------------------------------------------------------

class TestIsEmpty:
    def test_none_is_empty(self):
        assert _is_empty(None) is True

    def test_empty_string_is_empty(self):
        assert _is_empty("") is True

    def test_whitespace_string_is_empty(self):
        assert _is_empty("   ") is True

    def test_empty_list_is_empty(self):
        assert _is_empty([]) is True

    def test_empty_dict_is_empty(self):
        assert _is_empty({}) is True

    def test_zero_is_not_empty(self):
        assert _is_empty(0) is False

    def test_false_is_not_empty(self):
        assert _is_empty(False) is False

    def test_nonempty_string_is_not_empty(self):
        assert _is_empty("hello") is False

    def test_nonempty_list_is_not_empty(self):
        assert _is_empty(["a"]) is False

    def test_nonempty_dict_is_not_empty(self):
        assert _is_empty({"key": "value"}) is False
