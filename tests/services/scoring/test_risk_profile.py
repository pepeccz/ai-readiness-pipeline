"""
tests/services/scoring/test_risk_profile.py

RED phase — A.9

Tests for risk_profile(block_levels, composite_level) → str.

All four outcomes must be covered. Also tests the insufficient_data edge case
where the compliance block is treated as level 0 (conservative default).
"""

from __future__ import annotations

import pytest

from app.services.scoring.composite import risk_profile


# ---------------------------------------------------------------------------
# Helper to build a "safe" set of block levels (all at level 4 = Optimizado)
# then override specific blocks.
# ---------------------------------------------------------------------------

def all_high_levels(**overrides: int) -> dict[str, int]:
    """Return block levels dict where all blocks are at level 4, with overrides."""
    base = {
        "block-1-strategic": 4,
        "block-2-process-critical": 4,
        "block-3-data": 4,
        "block-4-talent": 4,
        "block-5-infrastructure": 4,
        "block-6-compliance": 4,
        "block-7-governance": 4,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Critical: compliance <= 1 AND governance <= 1
# ---------------------------------------------------------------------------

class TestRiskProfileCritical:
    def test_both_compliance_and_governance_at_level_0(self):
        """compliance=0 AND governance=0 → critical."""
        levels = all_high_levels(**{
            "block-6-compliance": 0,
            "block-7-governance": 0,
        })
        assert risk_profile(levels, composite_level=0) == "critical"

    def test_both_compliance_and_governance_at_level_1(self):
        """compliance=1 AND governance=1 → critical."""
        levels = all_high_levels(**{
            "block-6-compliance": 1,
            "block-7-governance": 1,
        })
        assert risk_profile(levels, composite_level=1) == "critical"

    def test_compliance_0_governance_1(self):
        """compliance=0, governance=1 → critical (both <= 1)."""
        levels = all_high_levels(**{
            "block-6-compliance": 0,
            "block-7-governance": 1,
        })
        assert risk_profile(levels, composite_level=0) == "critical"

    def test_insufficient_data_compliance_defaults_to_0_critical(self):
        """
        If compliance is marked insufficient_data (level=0) and governance=0
        → critical gate triggers.
        This test simulates the upstream behaviour (blocks dict already has level=0).
        """
        levels = all_high_levels(**{
            "block-6-compliance": 0,  # insufficient_data → level 0 upstream
            "block-7-governance": 0,
        })
        assert risk_profile(levels, composite_level=0) == "critical"


# ---------------------------------------------------------------------------
# High: compliance <= 1 OR governance <= 1 OR data level <= 0
# (but NOT both compliance and governance <= 1 — that's critical)
# ---------------------------------------------------------------------------

class TestRiskProfileHigh:
    def test_only_compliance_at_level_1(self):
        """compliance=1, governance=2, data=2 → high (compliance <= 1, governance > 1)."""
        levels = all_high_levels(**{
            "block-6-compliance": 1,
            "block-7-governance": 2,
            "block-3-data": 2,
        })
        assert risk_profile(levels, composite_level=2) == "high"

    def test_only_governance_at_level_1(self):
        """governance=1, compliance=2, data=2 → high."""
        levels = all_high_levels(**{
            "block-6-compliance": 2,
            "block-7-governance": 1,
            "block-3-data": 2,
        })
        assert risk_profile(levels, composite_level=2) == "high"

    def test_data_at_level_0(self):
        """data=0, compliance=2, governance=2 → high."""
        levels = all_high_levels(**{
            "block-6-compliance": 2,
            "block-7-governance": 2,
            "block-3-data": 0,
        })
        assert risk_profile(levels, composite_level=2) == "high"

    def test_compliance_at_level_0_but_governance_at_2(self):
        """compliance=0, governance=2 → high (not critical since governance > 1)."""
        levels = all_high_levels(**{
            "block-6-compliance": 0,
            "block-7-governance": 2,
        })
        assert risk_profile(levels, composite_level=0) == "high"

    def test_insufficient_data_compliance_high(self):
        """compliance=0 (from insufficient_data), governance=2 → high."""
        levels = all_high_levels(**{
            "block-6-compliance": 0,
            "block-7-governance": 2,
            "block-3-data": 2,
        })
        assert risk_profile(levels, composite_level=2) == "high"


# ---------------------------------------------------------------------------
# Medium: composite_level <= 1 (but no critical/high gate triggered)
# ---------------------------------------------------------------------------

class TestRiskProfileMedium:
    def test_composite_level_0_no_compliance_governance_issue(self):
        """All compliance/governance/data ok, composite_level=0 → medium."""
        levels = all_high_levels(**{
            "block-6-compliance": 2,
            "block-7-governance": 2,
            "block-3-data": 2,
        })
        assert risk_profile(levels, composite_level=0) == "medium"

    def test_composite_level_1_no_issue(self):
        """composite_level=1, no compliance/governance/data issue → medium."""
        levels = all_high_levels(**{
            "block-6-compliance": 2,
            "block-7-governance": 2,
            "block-3-data": 2,
        })
        assert risk_profile(levels, composite_level=1) == "medium"


# ---------------------------------------------------------------------------
# Low: all gates clear
# ---------------------------------------------------------------------------

class TestRiskProfileLow:
    def test_all_blocks_established_composite_2(self):
        """All blocks at level 2 (Establecido), composite=2 → low."""
        levels = all_high_levels(**{
            "block-6-compliance": 2,
            "block-7-governance": 2,
            "block-3-data": 2,
        })
        assert risk_profile(levels, composite_level=2) == "low"

    def test_all_blocks_optimizado(self):
        """All blocks at level 4, composite=4 → low."""
        levels = all_high_levels()
        assert risk_profile(levels, composite_level=4) == "low"

    def test_compliance_2_governance_2_composite_3(self):
        """composite=3, compliance=2, governance=2 → low."""
        levels = all_high_levels(**{
            "block-6-compliance": 2,
            "block-7-governance": 2,
        })
        assert risk_profile(levels, composite_level=3) == "low"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestRiskProfileDeterminism:
    def test_same_inputs_same_output(self):
        """Same block_levels + composite_level always returns same risk profile."""
        levels = all_high_levels(**{
            "block-6-compliance": 1,
            "block-7-governance": 2,
        })
        result1 = risk_profile(levels, composite_level=2)
        result2 = risk_profile(levels, composite_level=2)
        assert result1 == result2

    def test_all_outcomes_are_valid_strings(self):
        """risk_profile always returns one of the four valid outcomes."""
        valid = {"critical", "high", "medium", "low"}
        cases = [
            (all_high_levels(**{"block-6-compliance": 0, "block-7-governance": 0}), 0),
            (all_high_levels(**{"block-6-compliance": 1, "block-7-governance": 2}), 2),
            (all_high_levels(**{"block-6-compliance": 2, "block-7-governance": 2}), 1),
            (all_high_levels(), 4),
        ]
        for levels, cl in cases:
            assert risk_profile(levels, cl) in valid
