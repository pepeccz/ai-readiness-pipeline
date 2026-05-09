"""
tests/services/scoring/test_scorer_per_block.py

RED phase — A.4 (blocks 1-3) + B.2 (blocks 4-7)

Tests for score_block(payload, block_rubric) → BlockScore.

Fixtures use realistic block data based on a Pepe Cabeza SL-style session.
The critical property tested is determinism and correct indicator scoring.

PR2 additions (B.2):
- Fixtures and tests for blocks 4-7 using load_block_rubric (WARNING-02 fix)
- Multi-choice aggregation tests (WARNING-03 fix)
"""

from __future__ import annotations

import pytest

from app.services.scoring.scorer import score_block
from app.services.scoring.rubric import BlockRubric, Indicator, BlockScore
from app.services.scoring.loader import load_block_rubric


# ---------------------------------------------------------------------------
# Fixtures — minimal block-1-strategic rubric for testing
# ---------------------------------------------------------------------------

def make_block1_rubric() -> BlockRubric:
    """
    Minimal block-1-strategic rubric with 3 scorable indicators:
      - q1_2_sponsor: max_score=3, weight=1.0
      - q1_3_previous: max_score=3, weight=1.0
      - q1_1_timeframe: max_score=3, weight=1.0  (sub-field of composite)
    """
    return BlockRubric(
        block_id="block-1-strategic",
        indicators=[
            Indicator(id="q1_2_sponsor", weight=1.0, max_score=3.0),
            Indicator(id="q1_3_previous", weight=1.0, max_score=3.0),
            Indicator(id="q1_1_timeframe", weight=1.0, max_score=3.0),
        ],
    )


def make_full_block1_payload() -> dict:
    """
    Fully-populated block-1 payload. All indicators answered.
    q1_2_sponsor=ceo_total → score 3
    q1_3_previous=exitoso_produccion → score 3
    q1_1_timeframe (composite sub-field): value=12m → score 2
    """
    return {
        "q1_2_sponsor": "ceo_total",
        "q1_3_previous": "exitoso_produccion",
        "q1_1_objective": {
            "q1_1_outcome": "Reducir tiempo de respuesta al cliente un 40% en 6 meses",
            "q1_1_metric": "Tiempo medio de respuesta en CRM",
            "q1_1_timeframe": "12m",
        },
    }


def make_partial_block1_payload() -> dict:
    """
    Partial block-1 payload — q1_3_previous is absent.
    Expected: q1_3_previous contributes 0.
    """
    return {
        "q1_2_sponsor": "ceo_total",
        "q1_1_objective": {
            "q1_1_outcome": "Reducir tiempo de respuesta",
            "q1_1_metric": "Tiempo medio",
            "q1_1_timeframe": "12m",
        },
        # q1_3_previous absent
    }


# ---------------------------------------------------------------------------
# BlockRubric with inline option scores
# ---------------------------------------------------------------------------

def make_block1_rubric_with_options() -> BlockRubric:
    """
    BlockRubric where each Indicator also carries the option→score mapping
    used to look up the actual score for the chosen value.
    """
    return BlockRubric(
        block_id="block-1-strategic",
        indicators=[
            Indicator(
                id="q1_2_sponsor",
                weight=1.0,
                max_score=3.0,
                option_scores={
                    "ceo_total": 3,
                    "ceo_valida": 2,
                    "director_cto": 2,
                    "comite": 1,
                    "sin_sponsor": 0,
                },
            ),
            Indicator(
                id="q1_3_previous",
                weight=1.0,
                max_score=3.0,
                option_scores={
                    "first_time": 1,
                    "exitoso_produccion": 3,
                    "piloto_activo": 2,
                    "abandoned": 0,
                    "failed_production": 0,
                },
            ),
            Indicator(
                id="q1_1_timeframe",
                weight=1.0,
                max_score=3.0,
                option_scores={
                    "3m": 3,
                    "6m": 2,
                    "12m": 2,
                    "24m_plus": 1,
                },
                composite_parent="q1_1_objective",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScoreBlockFullPayload:
    def test_returns_block_score(self):
        """score_block returns a BlockScore instance."""
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        result = score_block(payload, rubric)
        assert isinstance(result, BlockScore)

    def test_raw_score_is_numeric(self):
        """BlockScore.raw is a non-negative float."""
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        result = score_block(payload, rubric)
        assert isinstance(result.raw, (int, float))
        assert result.raw >= 0

    def test_normalized_is_between_0_and_1(self):
        """BlockScore.normalized is in [0, 1]."""
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        result = score_block(payload, rubric)
        assert 0.0 <= result.normalized <= 1.0

    def test_full_payload_answered_count(self):
        """All 3 indicators answered → answered_count == 3."""
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        result = score_block(payload, rubric)
        assert result.answered_count == 3

    def test_correct_raw_score_full_payload(self):
        """
        Full payload: q1_2_sponsor=ceo_total(3) + q1_3_previous=exitoso_produccion(3)
        + q1_1_timeframe=12m(2) = 8. Raw = sum(score * weight) = 8.
        """
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        result = score_block(payload, rubric)
        # 3*1.0 + 3*1.0 + 2*1.0 = 8
        assert result.raw == pytest.approx(8.0)

    def test_correct_normalized_full_payload(self):
        """
        Full payload normalized = 8 / (3+3+3) = 8/9 ≈ 0.889.
        """
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        result = score_block(payload, rubric)
        assert result.normalized == pytest.approx(8.0 / 9.0, rel=1e-4)

    def test_deterministic_same_payload_same_result(self):
        """Calling score_block twice with same payload returns identical result."""
        rubric = make_block1_rubric_with_options()
        payload = make_full_block1_payload()
        r1 = score_block(payload, rubric)
        r2 = score_block(payload, rubric)
        assert r1.raw == r2.raw
        assert r1.normalized == r2.normalized
        assert r1.answered_count == r2.answered_count


class TestScoreBlockPartialPayload:
    def test_absent_indicator_scores_zero(self):
        """Absent indicator (q1_3_previous) contributes 0 to raw score."""
        rubric = make_block1_rubric_with_options()
        payload = make_partial_block1_payload()
        result = score_block(payload, rubric)
        # q1_2_sponsor=ceo_total(3) + q1_3_previous=absent(0) + q1_1_timeframe=12m(2)
        assert result.raw == pytest.approx(5.0)

    def test_partial_payload_answered_count(self):
        """Only 2 indicators answered (q1_3_previous absent)."""
        rubric = make_block1_rubric_with_options()
        payload = make_partial_block1_payload()
        result = score_block(payload, rubric)
        assert result.answered_count == 2

    def test_partial_normalized_uses_total_max(self):
        """
        Normalization uses total max (sum of all max_score * weight),
        not just answered indicators. raw=5, max=9 → normalized ≈ 0.556.
        """
        rubric = make_block1_rubric_with_options()
        payload = make_partial_block1_payload()
        result = score_block(payload, rubric)
        assert result.normalized == pytest.approx(5.0 / 9.0, rel=1e-4)


class TestScoreBlockEmptyPayload:
    def test_empty_payload_raw_zero(self):
        """Empty payload → raw score is 0."""
        rubric = make_block1_rubric_with_options()
        result = score_block({}, rubric)
        assert result.raw == pytest.approx(0.0)

    def test_empty_payload_normalized_zero(self):
        """Empty payload → normalized score is 0.0."""
        rubric = make_block1_rubric_with_options()
        result = score_block({}, rubric)
        assert result.normalized == pytest.approx(0.0)

    def test_empty_payload_answered_count_zero(self):
        """Empty payload → answered_count is 0."""
        rubric = make_block1_rubric_with_options()
        result = score_block({}, rubric)
        assert result.answered_count == 0


# ---------------------------------------------------------------------------
# B.2 RED — blocks 4-7 via load_block_rubric (WARNING-02 fix)
# ---------------------------------------------------------------------------


class TestLoadBlockRubricBlock4:
    """Tests that block-4-talent YAML loads into a usable BlockRubric."""

    def test_load_block4_returns_block_rubric(self):
        """load_block_rubric('block-4-talent') returns a BlockRubric."""
        rubric = load_block_rubric("block-4-talent")
        assert isinstance(rubric, BlockRubric)

    def test_block4_has_indicators(self):
        """block-4-talent rubric has at least 4 scorable indicators."""
        rubric = load_block_rubric("block-4-talent")
        assert len(rubric.indicators) >= 4

    def test_block4_indicators_have_option_scores(self):
        """Each indicator in block-4 has a non-empty option_scores dict."""
        rubric = load_block_rubric("block-4-talent")
        for ind in rubric.indicators:
            assert isinstance(ind.option_scores, dict), f"{ind.id} has no option_scores"
            assert len(ind.option_scores) > 0, f"{ind.id} has empty option_scores"

    def test_block4_score_full_payload(self):
        """Score a full block-4 payload — result should be in [0, 1]."""
        rubric = load_block_rubric("block-4-talent")
        payload = {
            "q4_1_team": {
                "q4_1_profiles": ["data_engineer_ml", "data_scientist"],
            },
            "q4_2_experience": {
                "q4_2_level": "integracion_apis",
            },
            "q4_3_training": {
                "q4_3_plan": "presupuestado",
                "q4_3_disposition": "motivado",
            },
            "q4_4_change_capacity": {
                "q4_4_history": "exitosos",
            },
        }
        result = score_block(payload, rubric)
        assert isinstance(result, BlockScore)
        assert 0.0 <= result.normalized <= 1.0
        assert result.raw > 0.0

    def test_block4_deterministic(self):
        """Calling score_block twice with same block-4 payload returns identical result."""
        rubric = load_block_rubric("block-4-talent")
        payload = {
            "q4_2_experience": {"q4_2_level": "prompts_elaborados"},
            "q4_3_training": {"q4_3_plan": "hablado_no_formal", "q4_3_disposition": "mixto"},
        }
        r1 = score_block(payload, rubric)
        r2 = score_block(payload, rubric)
        assert r1.raw == r2.raw
        assert r1.normalized == r2.normalized


class TestLoadBlockRubricBlock5:
    """Tests that block-5-infrastructure YAML loads into a usable BlockRubric."""

    def test_load_block5_returns_block_rubric(self):
        """load_block_rubric('block-5-infrastructure') returns a BlockRubric."""
        rubric = load_block_rubric("block-5-infrastructure")
        assert isinstance(rubric, BlockRubric)

    def test_block5_has_indicators(self):
        """block-5 rubric has at least 3 scorable indicators."""
        rubric = load_block_rubric("block-5-infrastructure")
        assert len(rubric.indicators) >= 3

    def test_block5_score_full_payload(self):
        """Score a full block-5 payload — result should be in [0, 1]."""
        rubric = load_block_rubric("block-5-infrastructure")
        payload = {
            "q5_1_infra": {
                "q5_1_model": "100_cloud",
            },
            "q5_3_deploy": {
                "q5_3_frequency": "mensual",
                "q5_3_time_new_tool": "semanas",
            },
            "q5_4_lockin": {
                "q5_4_level": "bajo",
            },
        }
        result = score_block(payload, rubric)
        assert isinstance(result, BlockScore)
        assert 0.0 <= result.normalized <= 1.0
        assert result.raw > 0.0


class TestLoadBlockRubricBlock6:
    """Tests that block-6-compliance YAML loads into a usable BlockRubric."""

    def test_load_block6_returns_block_rubric(self):
        """load_block_rubric('block-6-compliance') returns a BlockRubric."""
        rubric = load_block_rubric("block-6-compliance")
        assert isinstance(rubric, BlockRubric)

    def test_block6_has_indicators(self):
        """block-6 rubric has at least 4 scorable indicators."""
        rubric = load_block_rubric("block-6-compliance")
        assert len(rubric.indicators) >= 4

    def test_block6_score_full_payload(self):
        """Score a full block-6 payload — result should be in [0, 1]."""
        rubric = load_block_rubric("block-6-compliance")
        payload = {
            "q6_1_dpia": {
                "q6_1_dpia_status": "hecha_documentada",
                "q6_1_base_juridica": "consentimiento_doc",
            },
            "q6_2_automated_decisions": {
                "q6_2_status": "ninguna",
            },
            "q6_3_ai_act_category": {
                "q6_3_category": "minimo",
            },
            "q6_4_arco": "procedimiento_doc",
            "q6_5_incidents": {
                "q6_5_status": "ninguno_24m",
            },
        }
        result = score_block(payload, rubric)
        assert isinstance(result, BlockScore)
        assert 0.0 <= result.normalized <= 1.0
        assert result.raw > 0.0

    def test_block6_low_compliance_low_score(self):
        """A block-6 payload with all bad options should produce normalized < 0.4."""
        rubric = load_block_rubric("block-6-compliance")
        payload = {
            "q6_1_dpia": {
                "q6_1_dpia_status": "no_hecha_no_sabe",
                "q6_1_base_juridica": "no_claro",
            },
            "q6_2_automated_decisions": {
                "q6_2_status": "no_claro",
            },
            "q6_3_ai_act_category": {
                "q6_3_category": "no_lo_se",
            },
            "q6_4_arco": "no_pensado",
            "q6_5_incidents": {
                "q6_5_status": "no_forma_saber",
            },
        }
        result = score_block(payload, rubric)
        assert result.normalized < 0.4


class TestLoadBlockRubricBlock7:
    """Tests that block-7-governance YAML loads into a usable BlockRubric."""

    def test_load_block7_returns_block_rubric(self):
        """load_block_rubric('block-7-governance') returns a BlockRubric."""
        rubric = load_block_rubric("block-7-governance")
        assert isinstance(rubric, BlockRubric)

    def test_block7_has_indicators(self):
        """block-7 rubric has at least 3 scorable indicators."""
        rubric = load_block_rubric("block-7-governance")
        assert len(rubric.indicators) >= 3

    def test_block7_score_full_payload(self):
        """Score a full block-7 payload — result should be in [0, 1]."""
        rubric = load_block_rubric("block-7-governance")
        payload = {
            "q7_1_approval": {
                "q7_1_process": "comite_formal",
            },
            "q7_2_genai_policy": {
                "q7_2_policy_status": "firmada",
            },
            "q7_3_transparency": "siempre",
            "q7_4_error_plan": {
                "q7_4_plan_status": "documentado",
            },
        }
        result = score_block(payload, rubric)
        assert isinstance(result, BlockScore)
        assert 0.0 <= result.normalized <= 1.0
        assert result.raw > 0.0


# ---------------------------------------------------------------------------
# B.2 RED — multi_choice aggregation (WARNING-03 fix)
# Test that multi_choice answers are scored as sum of selected options
# capped at the indicator max_score.
# ---------------------------------------------------------------------------


class TestMultiChoiceScoring:
    """Tests for multi_choice aggregation in score_block (WARNING-03 fix).

    The scorer must iterate each selected option and sum their scores,
    capped at the indicator's max_score.
    """

    def _make_multi_choice_rubric(self, max_score: float = 5.0) -> BlockRubric:
        """Minimal rubric with one multi_choice indicator (q3_1_sources in block-3)."""
        return BlockRubric(
            block_id="block-3-data",
            indicators=[
                Indicator(
                    id="q3_1_sources",
                    weight=1.0,
                    max_score=max_score,
                    option_scores={
                        "erp": 3,
                        "crm": 3,
                        "hojas": 1,
                        "email": 1,
                        "docs": 1,
                        "bbdd_propia": 3,
                        "apis": 2,
                        "conocimiento_cabezas": 0,
                        "no_datos": 0,
                    },
                ),
            ],
        )

    def test_single_option_multi_choice_scores_correctly(self):
        """A single-option multi_choice list scores the single option."""
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": ["erp"]}
        result = score_block(payload, rubric)
        # erp = 3, cap = 5 → raw = 3
        assert result.raw == pytest.approx(3.0)

    def test_two_options_multi_choice_sums_scores(self):
        """Two selected options are summed (erp=3 + crm=3 = 6, capped at 5)."""
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": ["erp", "crm"]}
        result = score_block(payload, rubric)
        # erp=3 + crm=3 = 6, capped at max_score=5
        assert result.raw == pytest.approx(5.0)

    def test_three_options_capped_at_max(self):
        """Three options: erp=3 + crm=3 + bbdd_propia=3 = 9, capped at 5."""
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": ["erp", "crm", "bbdd_propia"]}
        result = score_block(payload, rubric)
        assert result.raw == pytest.approx(5.0)

    def test_multi_choice_empty_list_scores_zero(self):
        """Empty list for multi_choice scores 0 (no selection)."""
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": []}
        result = score_block(payload, rubric)
        assert result.raw == pytest.approx(0.0)
        assert result.answered_count == 0

    def test_multi_choice_old_stringify_behavior_would_fail(self):
        """
        Regression: the OLD code did str(["erp", "crm"]) = "['erp', 'crm']" which
        is never in option_scores → returned 0.0. This test documents the OLD wrong
        behavior was 0.0 for multi-element selections, and the new behavior is > 0.
        """
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": ["erp", "crm"]}
        result = score_block(payload, rubric)
        # New behavior: sum of selected = 5.0 (capped), NOT 0.0 (old stringify)
        assert result.raw > 0.0

    def test_multi_choice_no_cap_below_max(self):
        """Sum below max_score is not capped — email(1) + hojas(1) = 2, max=5 → raw=2."""
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": ["email", "hojas"]}
        result = score_block(payload, rubric)
        assert result.raw == pytest.approx(2.0)

    def test_multi_choice_single_string_still_scores(self):
        """A scalar string answer (not a list) is still handled correctly."""
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": "erp"}
        result = score_block(payload, rubric)
        # scalar string: single option lookup
        assert result.raw == pytest.approx(3.0)

    def test_multi_choice_pepe_cabeza_fixture(self):
        """
        Pepe Cabeza SL fixture: q3_1_sources = ["crm", "email", "bbdd_propia"]
        crm=3 + email=1 + bbdd_propia=3 = 7, capped at 5. Raw = 5.0.
        """
        rubric = self._make_multi_choice_rubric(max_score=5.0)
        payload = {"q3_1_sources": ["crm", "email", "bbdd_propia"]}
        result = score_block(payload, rubric)
        assert result.raw == pytest.approx(5.0)
