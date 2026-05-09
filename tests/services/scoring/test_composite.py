"""
tests/services/scoring/test_composite.py

RED phase — A.7 (composite + CMMI) + B.4 (full-session determinism)

Tests for composite_score, level_from_normalized, composite_level_min.
B.4 adds: two sessions with byte-identical payloads for all 7 blocks → identical output.

Design anchors:
- Composite CMMI = min of per-block levels (blocks NOT in insufficient_data)
- insufficient_data blocks are excluded from composite calc but default to level 0
  for risk gates
- composite_normalized = weighted avg of block_normalized over non-insufficient blocks
"""

from __future__ import annotations

import pytest

from app.services.scoring.composite import (
    composite_score,
    level_from_normalized,
    composite_level_min,
)
from app.services.scoring.rubric import BlockScore, Registry
from app.services.scoring.loader import load_block_rubric
from app.services.scoring.scorer import score_block
from app.services.scoring import score_session, SessionScoreResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_registry() -> Registry:
    from app.services.scoring.loader import load_registry
    return load_registry("v1")


def make_seven_block_scores(normalized_values: dict[str, float]) -> dict[str, BlockScore]:
    """Build a dict of BlockScore keyed by block_id with given normalized values."""
    block_ids = [
        "block-1-strategic",
        "block-2-process-critical",
        "block-3-data",
        "block-4-talent",
        "block-5-infrastructure",
        "block-6-compliance",
        "block-7-governance",
    ]
    scores = {}
    for bid in block_ids:
        normalized = normalized_values.get(bid, 0.5)
        scores[bid] = BlockScore(
            raw=normalized * 10,
            normalized=normalized,
            answered_count=5,
            block_id=bid,
            status="scored",
        )
    return scores


def make_block_score(block_id: str, normalized: float, status: str = "scored") -> BlockScore:
    return BlockScore(
        raw=normalized * 10,
        normalized=normalized,
        answered_count=5,
        block_id=block_id,
        status=status,
    )


# ---------------------------------------------------------------------------
# Tests: level_from_normalized
# ---------------------------------------------------------------------------

class TestLevelFromNormalized:
    def test_zero_is_inicial(self, ):
        """0.0 → level 0 (Inicial)."""
        registry = make_registry()
        assert level_from_normalized(0.0, registry.cmmi_thresholds) == 0

    def test_0_1_is_inicial(self):
        """0.1 → level 0 (Inicial)."""
        registry = make_registry()
        assert level_from_normalized(0.1, registry.cmmi_thresholds) == 0

    def test_0_2_is_emergente(self):
        """0.2 → level 1 (Emergente) — boundary at 0.20."""
        registry = make_registry()
        assert level_from_normalized(0.2, registry.cmmi_thresholds) == 1

    def test_0_3_is_emergente(self):
        registry = make_registry()
        assert level_from_normalized(0.3, registry.cmmi_thresholds) == 1

    def test_0_4_is_establecido(self):
        """0.4 → level 2 (Establecido)."""
        registry = make_registry()
        assert level_from_normalized(0.4, registry.cmmi_thresholds) == 2

    def test_0_5_is_establecido(self):
        registry = make_registry()
        assert level_from_normalized(0.5, registry.cmmi_thresholds) == 2

    def test_0_6_is_avanzado(self):
        """0.6 → level 3 (Avanzado)."""
        registry = make_registry()
        assert level_from_normalized(0.6, registry.cmmi_thresholds) == 3

    def test_0_8_is_optimizado(self):
        """0.8 → level 4 (Optimizado)."""
        registry = make_registry()
        assert level_from_normalized(0.8, registry.cmmi_thresholds) == 4

    def test_1_0_is_optimizado(self):
        """1.0 → level 4 (Optimizado)."""
        registry = make_registry()
        assert level_from_normalized(1.0, registry.cmmi_thresholds) == 4

    def test_deterministic_same_score_same_level(self):
        """Same score always produces same level."""
        registry = make_registry()
        assert level_from_normalized(0.55, registry.cmmi_thresholds) == level_from_normalized(0.55, registry.cmmi_thresholds)


# ---------------------------------------------------------------------------
# Tests: composite_level_min
# ---------------------------------------------------------------------------

class TestCompositeLevelMin:
    def test_min_of_levels(self):
        """composite_level_min returns the minimum of all levels."""
        per_block_levels = {
            "block-1-strategic": 3,
            "block-2-process-critical": 2,
            "block-3-data": 1,
            "block-4-talent": 4,
            "block-5-infrastructure": 2,
            "block-6-compliance": 2,
            "block-7-governance": 3,
        }
        assert composite_level_min(per_block_levels) == 1

    def test_all_same_level(self):
        per_block_levels = {bid: 2 for bid in [
            "block-1-strategic", "block-2-process-critical", "block-3-data",
            "block-4-talent", "block-5-infrastructure", "block-6-compliance",
            "block-7-governance",
        ]}
        assert composite_level_min(per_block_levels) == 2

    def test_single_block_zero(self):
        """One block at 0 → composite = 0."""
        per_block_levels = {
            "block-1-strategic": 3,
            "block-6-compliance": 0,
        }
        assert composite_level_min(per_block_levels) == 0


# ---------------------------------------------------------------------------
# Tests: composite_score (full result)
# ---------------------------------------------------------------------------

class TestCompositeScore:
    def test_returns_composite_result(self):
        """composite_score returns a CompositeResult instance."""
        from app.services.scoring.composite import CompositeResult
        registry = make_registry()
        scores = make_seven_block_scores({bid: 0.5 for bid in [
            "block-1-strategic", "block-2-process-critical", "block-3-data",
            "block-4-talent", "block-5-infrastructure", "block-6-compliance",
            "block-7-governance",
        ]})
        result = composite_score(scores, registry)
        assert isinstance(result, CompositeResult)

    def test_composite_level_equals_min(self):
        """composite_level = min of per-block levels."""
        registry = make_registry()
        # One block at normalized=0.1 (Inicial=0), rest at 0.5 (Establecido=2)
        norm_vals = {
            "block-1-strategic": 0.1,   # level 0
            "block-2-process-critical": 0.5,
            "block-3-data": 0.5,
            "block-4-talent": 0.5,
            "block-5-infrastructure": 0.5,
            "block-6-compliance": 0.5,
            "block-7-governance": 0.5,
        }
        scores = make_seven_block_scores(norm_vals)
        result = composite_score(scores, registry)
        assert result.composite_level == 0  # min is Inicial

    def test_composite_normalized_weighted_average(self):
        """composite_normalized is the weighted average of non-insufficient blocks."""
        registry = make_registry()
        # All equal weights 1.0, all normalized = 0.5 → avg = 0.5
        scores = make_seven_block_scores({
            "block-1-strategic": 0.5,
            "block-2-process-critical": 0.5,
            "block-3-data": 0.5,
            "block-4-talent": 0.5,
            "block-5-infrastructure": 0.5,
            "block-6-compliance": 0.5,
            "block-7-governance": 0.5,
        })
        result = composite_score(scores, registry)
        assert result.composite_normalized == pytest.approx(0.5, rel=1e-4)

    def test_has_per_block_levels(self):
        """CompositeResult has per_block_levels dict with all 7 block IDs."""
        registry = make_registry()
        scores = make_seven_block_scores({bid: 0.5 for bid in [
            "block-1-strategic", "block-2-process-critical", "block-3-data",
            "block-4-talent", "block-5-infrastructure", "block-6-compliance",
            "block-7-governance",
        ]})
        result = composite_score(scores, registry)
        assert len(result.per_block_levels) == 7

    def test_has_average_normalized(self):
        """CompositeResult has average_normalized field."""
        from app.services.scoring.composite import CompositeResult
        registry = make_registry()
        scores = make_seven_block_scores({bid: 0.6 for bid in [
            "block-1-strategic", "block-2-process-critical", "block-3-data",
            "block-4-talent", "block-5-infrastructure", "block-6-compliance",
            "block-7-governance",
        ]})
        result = composite_score(scores, registry)
        assert hasattr(result, "average_normalized")
        assert isinstance(result.average_normalized, float)

    def test_insufficient_data_blocks_excluded_from_composite(self):
        """Blocks with status=insufficient_data are excluded from composite_normalized calc."""
        registry = make_registry()
        # 6 blocks at 0.5, 1 insufficient block
        scores = {
            "block-1-strategic": make_block_score("block-1-strategic", 0.5),
            "block-2-process-critical": make_block_score("block-2-process-critical", 0.5),
            "block-3-data": make_block_score("block-3-data", 0.0, status="insufficient_data"),
            "block-4-talent": make_block_score("block-4-talent", 0.5),
            "block-5-infrastructure": make_block_score("block-5-infrastructure", 0.5),
            "block-6-compliance": make_block_score("block-6-compliance", 0.5),
            "block-7-governance": make_block_score("block-7-governance", 0.5),
        }
        result = composite_score(scores, registry)
        # composite_normalized should be average of the 6 scored blocks = 0.5
        assert result.composite_normalized == pytest.approx(0.5, rel=1e-4)

    def test_insufficient_data_block_defaults_to_level_0_in_per_block_levels(self):
        """insufficient_data block appears in per_block_levels with level=0 for risk gates."""
        registry = make_registry()
        scores = {
            "block-1-strategic": make_block_score("block-1-strategic", 0.7),
            "block-2-process-critical": make_block_score("block-2-process-critical", 0.7),
            "block-3-data": make_block_score("block-3-data", 0.0, status="insufficient_data"),
            "block-4-talent": make_block_score("block-4-talent", 0.7),
            "block-5-infrastructure": make_block_score("block-5-infrastructure", 0.7),
            "block-6-compliance": make_block_score("block-6-compliance", 0.7),
            "block-7-governance": make_block_score("block-7-governance", 0.7),
        }
        result = composite_score(scores, registry)
        assert result.per_block_levels["block-3-data"] == 0


# ---------------------------------------------------------------------------
# B.4 RED — Full-session determinism test (REQ-05)
# Two sessions with byte-identical payloads for all 7 blocks → identical outputs
# Uses load_block_rubric (WARNING-02 fix) + score_block for all 7 blocks
# ---------------------------------------------------------------------------


# Pepe Cabeza SL-analogue: representative realistic payloads for all 7 blocks
_PEPE_CABEZA_PAYLOADS: dict[str, dict] = {
    "block-1-strategic": {
        "q1_1_objective": {
            "q1_1_outcome": "Reducir tiempo de respuesta al cliente un 40% en 6 meses",
            "q1_1_metric": "Tiempo medio de respuesta en CRM",
            "q1_1_timeframe": "12m",
        },
        "q1_2_sponsor": "ceo_total",
        "q1_3_previous": "exitoso_produccion",
        "q1_4_appetite": {
            "q1_4_risk": "moderado",
            "q1_4_horizon": "12m",
        },
    },
    "block-2-process-critical": {
        "q2_1_process": {
            "q2_1_name": "Revisión de contratos",
            "q2_1_frequency": "diario",
        },
        "q2_2_variability": "variable",
        "q2_3_metrics": {
            "q2_3_documented": "parcial",
        },
        "q2_4_failure_cost": {
            "q2_4_level": "alto",
        },
        "q2_5_dependencies": {
            "q2_5_key_person": "parcial",
        },
    },
    "block-3-data": {
        "q3_1_sources": ["crm", "email", "bbdd_propia"],
        "q3_2_quality": {
            "q3_2_level": "buena",
        },
        "q3_3_volume": {
            "q3_3_volume_count": "1k_10k",
            "q3_3_retention": "2a_5a",
        },
        "q3_4_personal_data": {
            "q3_4_category": "personal_identificable",
        },
        "q3_5_accessibility": "exportable",
    },
    "block-4-talent": {
        "q4_1_team": {
            "q4_1_profiles": ["dev_software", "data_analyst"],
        },
        "q4_2_experience": {
            "q4_2_level": "uso_individual",
        },
        "q4_3_training": {
            "q4_3_plan": "hablado_no_formal",
            "q4_3_disposition": "mixto",
        },
        "q4_4_change_capacity": {
            "q4_4_history": "exitosos",
        },
    },
    "block-5-infrastructure": {
        "q5_1_infra": {
            "q5_1_model": "mayoria_cloud",
        },
        "q5_3_deploy": {
            "q5_3_frequency": "mensual",
            "q5_3_time_new_tool": "semanas",
        },
        "q5_4_lockin": {
            "q5_4_level": "medio",
        },
    },
    "block-6-compliance": {
        "q6_1_dpia": {
            "q6_1_dpia_status": "hecha_informal",
            "q6_1_base_juridica": "asumido_no_doc",
        },
        "q6_2_automated_decisions": {
            "q6_2_status": "planeamos_ia",
        },
        "q6_3_ai_act_category": {
            "q6_3_category": "limitado",
        },
        "q6_4_arco": "sabemos_no_formal",
        "q6_5_incidents": {
            "q6_5_status": "menores_resueltos",
        },
    },
    "block-7-governance": {
        "q7_1_approval": {
            "q7_1_process": "persona_criterios",
        },
        "q7_2_genai_policy": {
            "q7_2_policy_status": "verbal",
        },
        "q7_3_transparency": "casos_sensibles",
        "q7_4_error_plan": {
            "q7_4_plan_status": "sabemos_no_doc",
        },
    },
}


def _score_all_blocks(payloads: dict[str, dict]) -> dict[str, BlockScore]:
    """Score all 7 blocks using load_block_rubric + score_block."""
    registry = make_registry()
    block_scores: dict[str, BlockScore] = {}
    for block_id, payload in payloads.items():
        rubric = load_block_rubric(block_id)
        bs = score_block(payload, rubric)
        # Attach the block_id to the score (score_block uses rubric.block_id automatically)
        block_scores[block_id] = bs
    return block_scores


class TestFullSessionDeterminism:
    """
    REQ-05: Two sessions with byte-identical payloads for all 7 blocks
    must produce identical block_scores, composite_score, and composite_level.
    """

    def test_two_sessions_identical_payloads_identical_block_scores(self):
        """Score run 1 == score run 2 for all 7 blocks (per-block raw + normalized)."""
        scores_1 = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        scores_2 = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        for block_id in _PEPE_CABEZA_PAYLOADS:
            assert scores_1[block_id].raw == scores_2[block_id].raw, (
                f"{block_id} raw differs between runs"
            )
            assert scores_1[block_id].normalized == scores_2[block_id].normalized, (
                f"{block_id} normalized differs between runs"
            )

    def test_two_sessions_identical_payloads_identical_composite(self):
        """Two identical sessions produce the same composite_normalized and composite_level."""
        registry = make_registry()
        scores_1 = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        scores_2 = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        composite_1 = composite_score(scores_1, registry)
        composite_2 = composite_score(scores_2, registry)
        assert composite_1.composite_normalized == pytest.approx(
            composite_2.composite_normalized, rel=1e-9
        )
        assert composite_1.composite_level == composite_2.composite_level

    def test_all_seven_blocks_produce_nonzero_scores(self):
        """Each block in the realistic fixture scores above 0 (non-trivial answers given)."""
        scores = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        for block_id, bs in scores.items():
            assert bs.raw > 0.0, f"{block_id} scored 0 (unexpected with realistic payload)"

    def test_composite_level_is_bounded(self):
        """Composite level is in range [0, 4]."""
        registry = make_registry()
        scores = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        result = composite_score(scores, registry)
        assert 0 <= result.composite_level <= 4

    def test_per_block_levels_all_seven_present(self):
        """All 7 block IDs appear in per_block_levels after composite_score."""
        registry = make_registry()
        scores = _score_all_blocks(_PEPE_CABEZA_PAYLOADS)
        result = composite_score(scores, registry)
        for block_id in _PEPE_CABEZA_PAYLOADS:
            assert block_id in result.per_block_levels


# ---------------------------------------------------------------------------
# B.7 GREEN — score_session entry point tests
# ---------------------------------------------------------------------------


class _FakeBlockAnalysis:
    """Minimal stand-in for a BlockAnalysis row (no DB needed)."""

    def __init__(self, block_id: str, status: str, payload: dict):
        self.block_id = block_id
        self.status = status
        self.payload = payload


class _FakeSession:
    """Minimal stand-in for an IntakeSession row (no DB needed)."""

    def __init__(self, block_analyses: list, rubric_version: str = "v1"):
        self.block_analyses = block_analyses
        self.rubric_version = rubric_version


def _make_fake_session_all_blocks() -> _FakeSession:
    """Build a fake IntakeSession with all 7 blocks using Pepe Cabeza payloads."""
    analyses = [
        _FakeBlockAnalysis(block_id=bid, status="completed", payload=payload)
        for bid, payload in _PEPE_CABEZA_PAYLOADS.items()
    ]
    return _FakeSession(block_analyses=analyses)


class TestScoreSessionEntryPoint:
    """Tests for score_session(session) → SessionScoreResult (B.7 GREEN)."""

    def test_score_session_returns_session_score_result(self):
        """score_session returns a SessionScoreResult instance."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert isinstance(result, SessionScoreResult)

    def test_score_session_has_seven_block_scores(self):
        """Result has per_block_scores for all 7 blocks."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert len(result.per_block_scores) == 7

    def test_score_session_composite_normalized_in_range(self):
        """composite_normalized is in [0, 1]."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert 0.0 <= result.composite_normalized <= 1.0

    def test_score_session_composite_level_in_range(self):
        """composite_level is in [0, 4]."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert 0 <= result.composite_level <= 4

    def test_score_session_risk_profile_valid(self):
        """risk_profile is one of the 4 valid values."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert result.risk_profile in ("low", "medium", "high", "critical")

    def test_score_session_with_insufficient_data_block(self):
        """score_session correctly marks blocks in insufficient_data state."""
        analyses = [
            _FakeBlockAnalysis(
                block_id="block-3-data",
                status="insufficient_data",
                payload={},
            ),
        ] + [
            _FakeBlockAnalysis(block_id=bid, status="completed", payload=payload)
            for bid, payload in _PEPE_CABEZA_PAYLOADS.items()
            if bid != "block-3-data"
        ]
        session = _FakeSession(block_analyses=analyses)
        result = score_session(session)
        assert "block-3-data" in result.insufficient_blocks
        assert result.per_block_scores["block-3-data"].status == "insufficient_data"

    def test_score_session_empty_session_returns_default(self):
        """score_session with no block analyses returns a default result."""
        session = _FakeSession(block_analyses=[])
        result = score_session(session)
        assert isinstance(result, SessionScoreResult)
        assert result.composite_normalized == pytest.approx(0.0)

    def test_score_session_deterministic(self):
        """Calling score_session twice with same session returns identical results."""
        session = _make_fake_session_all_blocks()
        r1 = score_session(session)
        r2 = score_session(session)
        assert r1.composite_normalized == pytest.approx(r2.composite_normalized)
        assert r1.composite_level == r2.composite_level
        assert r1.risk_profile == r2.risk_profile

    def test_score_session_rubric_version_propagated(self):
        """SessionScoreResult.rubric_version matches session.rubric_version."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert result.rubric_version == "v1"

    def test_score_session_per_block_levels_has_all_blocks(self):
        """per_block_levels contains all 7 blocks."""
        session = _make_fake_session_all_blocks()
        result = score_session(session)
        assert len(result.per_block_levels) == 7
