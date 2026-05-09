"""
tests/services/scoring/test_loader.py

RED phase — A.1 (registry loading) + B.6 (all 7 blocks in registry + load_block_rubric)

Tests that `load_registry("v1")` returns a typed Registry object with the
expected fields. Also tests error handling for missing/malformed versions.

B.6 additions:
- Verify all 7 block weights are present in v1 registry (explicit per-block)
- Verify load_block_rubric resolves all 7 canonical block IDs correctly
- Verify no indicator in any block has empty option_scores (WARNING-02 closed)
"""

from __future__ import annotations

import pytest

from app.services.scoring.loader import load_registry, load_block_rubric
from app.services.scoring.rubric import Registry, BlockRubric


class TestLoadRegistry:
    def test_load_v1_returns_registry(self):
        """load_registry('v1') returns a Registry instance."""
        registry = load_registry("v1")
        assert isinstance(registry, Registry)

    def test_registry_has_block_weights(self):
        """Registry.block_weights is a non-empty dict."""
        registry = load_registry("v1")
        assert isinstance(registry.block_weights, dict)
        assert len(registry.block_weights) > 0

    def test_registry_has_cmmi_thresholds(self):
        """Registry.cmmi_thresholds has exactly 5 named levels."""
        registry = load_registry("v1")
        assert isinstance(registry.cmmi_thresholds, dict)
        expected_levels = {"inicial", "emergente", "establecido", "avanzado", "optimizado"}
        assert set(registry.cmmi_thresholds.keys()) == expected_levels

    def test_registry_has_risk_gates(self):
        """Registry.risk_gates is present and non-empty."""
        registry = load_registry("v1")
        assert isinstance(registry.risk_gates, dict)
        assert len(registry.risk_gates) > 0

    def test_registry_has_schema_version(self):
        """Registry.schema_version equals 1."""
        registry = load_registry("v1")
        assert registry.schema_version == 1

    def test_nonexistent_version_raises_file_not_found(self):
        """Loading a non-existent version raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_registry("v99")

    def test_cmmi_thresholds_have_min_max(self):
        """Each CMMI threshold entry has min and max keys."""
        registry = load_registry("v1")
        for level_name, bounds in registry.cmmi_thresholds.items():
            assert "min" in bounds, f"Missing 'min' in {level_name}"
            assert "max" in bounds, f"Missing 'max' in {level_name}"

    def test_cmmi_thresholds_cover_full_range(self):
        """CMMI thresholds start at 0.0 and end at 1.0+ (optimizado.max >= 1.0)."""
        registry = load_registry("v1")
        assert registry.cmmi_thresholds["inicial"]["min"] == 0.0
        assert registry.cmmi_thresholds["optimizado"]["max"] >= 1.0

    def test_all_seven_blocks_have_weights(self):
        """All 7 core block IDs appear in block_weights."""
        registry = load_registry("v1")
        expected_blocks = {
            "block-1-strategic",
            "block-2-process-critical",
            "block-3-data",
            "block-4-talent",
            "block-5-infrastructure",
            "block-6-compliance",
            "block-7-governance",
        }
        assert expected_blocks.issubset(set(registry.block_weights.keys()))


# ---------------------------------------------------------------------------
# B.6 RED — All 7 block weights explicit + load_block_rubric for all 7 blocks
# ---------------------------------------------------------------------------


class TestAllSevenBlockWeightsExplicit:
    """Verify each block weight is a positive float in the v1 registry."""

    def test_block1_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-1-strategic"] > 0.0

    def test_block2_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-2-process-critical"] > 0.0

    def test_block3_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-3-data"] > 0.0

    def test_block4_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-4-talent"] > 0.0

    def test_block5_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-5-infrastructure"] > 0.0

    def test_block6_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-6-compliance"] > 0.0

    def test_block7_weight_is_positive(self):
        registry = load_registry("v1")
        assert registry.block_weights["block-7-governance"] > 0.0

    def test_registry_has_exactly_seven_blocks(self):
        """v1 registry covers exactly 7 blocks (no more, no less)."""
        registry = load_registry("v1")
        expected = {
            "block-1-strategic",
            "block-2-process-critical",
            "block-3-data",
            "block-4-talent",
            "block-5-infrastructure",
            "block-6-compliance",
            "block-7-governance",
        }
        assert set(registry.block_weights.keys()) == expected


class TestLoadBlockRubricAllSevenBlocks:
    """
    Verify load_block_rubric resolves all 7 canonical block IDs and
    returns a BlockRubric with at least one indicator with non-empty option_scores.
    This closes WARNING-02: YAML → BlockRubric wiring is confirmed working.
    """

    _CANONICAL_BLOCK_IDS = [
        "block-1-strategic",
        "block-2-process-critical",
        "block-3-data",
        "block-4-talent",
        "block-5-infrastructure",
        "block-6-compliance",
        "block-7-governance",
    ]

    def test_all_blocks_resolve_to_block_rubric(self):
        """load_block_rubric succeeds for all 7 canonical block IDs."""
        for block_id in self._CANONICAL_BLOCK_IDS:
            rubric = load_block_rubric(block_id)
            assert isinstance(rubric, BlockRubric), f"{block_id} did not return BlockRubric"

    def test_all_blocks_have_at_least_one_indicator(self):
        """Each block rubric has at least 1 scorable indicator."""
        for block_id in self._CANONICAL_BLOCK_IDS:
            rubric = load_block_rubric(block_id)
            assert len(rubric.indicators) >= 1, (
                f"{block_id} has no indicators (WARNING-02 would not be closed)"
            )

    def test_all_block_indicators_have_option_scores(self):
        """Every indicator in every block has non-empty option_scores (WARNING-02 closed)."""
        for block_id in self._CANONICAL_BLOCK_IDS:
            rubric = load_block_rubric(block_id)
            for ind in rubric.indicators:
                assert ind.option_scores, (
                    f"{block_id}.{ind.id} has empty option_scores — WARNING-02 not closed"
                )

    def test_all_blocks_max_score_positive(self):
        """Every indicator has max_score > 0 (YAML score: values are present)."""
        for block_id in self._CANONICAL_BLOCK_IDS:
            rubric = load_block_rubric(block_id)
            for ind in rubric.indicators:
                assert ind.max_score > 0.0, (
                    f"{block_id}.{ind.id} has max_score=0 — scoring would always yield 0"
                )

    def test_load_block_rubric_nonexistent_raises_file_not_found(self):
        """load_block_rubric raises FileNotFoundError for unknown block_id."""
        with pytest.raises(FileNotFoundError):
            load_block_rubric("block-99-nonexistent")


class TestMaxScoreOverride:
    """YAML max_score: attribute overrides auto-derived ceiling.

    Rationale: q4_1_profiles auto-max = 12 (sum of 6 positive options).
    A 1-2 profile selection in a small team would yield ~0.17-0.33 normalized,
    placing the indicator at CMMI level 0-1 even when the team has the right
    foundational profiles. Override max_score=6 makes 2-profile selection
    (e.g. dev+analyst = 4) yield 0.67 → CMMI level 3.
    """

    def test_q4_1_profiles_max_score_overridden_to_six(self):
        """block-4 q4_1_profiles has explicit max_score=6 (not auto-derived 12)."""
        rubric = load_block_rubric("block-4-talent")
        profiles_indicator = next(
            (ind for ind in rubric.indicators if ind.id == "q4_1_profiles"),
            None,
        )
        assert profiles_indicator is not None, "q4_1_profiles indicator missing"
        assert profiles_indicator.max_score == 6.0, (
            f"Expected max_score=6 (YAML override), got {profiles_indicator.max_score}"
        )

    def test_indicators_without_override_use_auto_derived_max(self):
        """Indicators without explicit max_score: still use auto-derivation."""
        rubric = load_block_rubric("block-3-data")
        sources_indicator = next(
            (ind for ind in rubric.indicators if ind.id == "q3_1_sources"),
            None,
        )
        # q3_1_sources is multi_choice with no override → max = sum of positives
        assert sources_indicator is not None
        assert sources_indicator.max_score > 0
