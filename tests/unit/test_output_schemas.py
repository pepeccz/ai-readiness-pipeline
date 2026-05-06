"""
tests/unit/test_output_schemas.py — validates Pydantic output schemas per block.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.ai_analysis.output_schemas import (
    BlockAnalysisOutput,
    StrategicOutput,
    ProcessFullOutput,
    ProcessReducedOutput,
    DataOutput,
    TalentOutput,
    InfrastructureOutput,
    ComplianceOutput,
    GovernanceOutput,
    FollowUp,
    Contradiction,
)


VALID_BASE = {
    "synthesis": "La empresa tiene madurez media en IA, con pilotos aislados sin gobierno.",
    "contradictions": [
        {"text": "Dicen urgencia alta pero no tienen sponsor definido", "severity": "high"}
    ],
    "follow_ups": [
        {"text": "¿Quién aprueba el presupuesto del proyecto?", "rationale": "No hay sponsor claro", "priority": "high", "confidence": 0.85}
    ],
    "preliminary_hypothesis": None,
    "block_specific_outputs": {},
}


class TestBaseBlockAnalysisOutput:
    def test_valid_base_output(self):
        obj = BlockAnalysisOutput(**VALID_BASE)
        assert obj.synthesis.startswith("La empresa")

    def test_missing_synthesis_is_none(self):
        """REQ-2: synthesis is now Optional — missing it yields None, not ValidationError."""
        data = {**VALID_BASE}
        del data["synthesis"]
        obj = BlockAnalysisOutput(**data)
        assert obj.synthesis is None

    def test_follow_up_confidence_range(self):
        data = {**VALID_BASE, "follow_ups": [
            {"text": "Pregunta válida", "rationale": "Motivo", "priority": "low", "confidence": 1.5}
        ]}
        with pytest.raises(ValidationError):
            BlockAnalysisOutput(**data)


class TestStrategicOutput:
    def test_strategic_no_extra_required(self):
        # block-1 has no block_specific_outputs required
        obj = StrategicOutput(**VALID_BASE)
        assert obj.synthesis != ""


class TestProcessFullOutput:
    def test_valid_process_full(self):
        data = {
            **VALID_BASE,
            "recommended_approach": "ai_with_guardrails",
            "ia_fit_score": 75,
        }
        obj = ProcessFullOutput(**data)
        assert obj.recommended_approach == "ai_with_guardrails"
        assert obj.ia_fit_score == 75

    def test_invalid_approach_raises(self):
        data = {
            **VALID_BASE,
            "recommended_approach": "magic_solution",
            "ia_fit_score": 75,
        }
        with pytest.raises(ValidationError):
            ProcessFullOutput(**data)

    def test_ia_fit_score_out_of_range_accepted(self):
        """REQ-2: ia_fit_score is now Optional[int] without range constraint — relaxed for partial LLM tolerance."""
        data = {
            **VALID_BASE,
            "recommended_approach": "ai_full",
            "ia_fit_score": 150,
        }
        obj = ProcessFullOutput(**data)
        assert obj.ia_fit_score == 150


class TestDataOutput:
    def test_valid_data_output(self):
        data = {
            **VALID_BASE,
            "data_readiness": {"score": 0.6, "level": "medium"},
            "compliance_flags": ["GDPR"],
        }
        obj = DataOutput(**data)
        dr = obj.data_readiness
        score = dr["score"] if isinstance(dr, dict) else dr.score
        assert score == 0.6


class TestTalentOutput:
    def test_valid_talent_output(self):
        data = {
            **VALID_BASE,
            "execution_model_recommended": "hybrid",
        }
        obj = TalentOutput(**data)
        assert obj.execution_model_recommended == "hybrid"

    def test_invalid_execution_model(self):
        data = {**VALID_BASE, "execution_model_recommended": "outsourced_fully"}
        with pytest.raises(ValidationError):
            TalentOutput(**data)


class TestComplianceOutput:
    def test_valid_compliance_output(self):
        data = {
            **VALID_BASE,
            "recommended_compliance_phase": "parallel_to_pilot",
            "obligations_triggered": ["GDPR Art.22", "ISO 42001"],
        }
        obj = ComplianceOutput(**data)
        assert obj.recommended_compliance_phase == "parallel_to_pilot"


class TestGovernanceOutput:
    def test_valid_governance_output(self):
        data = {
            **VALID_BASE,
            "shadow_ai_risk": "high",
            "first_governance_deliverables": ["AI policy draft", "Use case registry"],
        }
        obj = GovernanceOutput(**data)
        assert obj.shadow_ai_risk == "high"
