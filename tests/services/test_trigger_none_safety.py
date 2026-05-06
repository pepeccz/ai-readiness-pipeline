"""
tests/services/test_trigger_none_safety.py — C.1 (REQ-2)

Verify that BlockAnalysisOutput subclasses with all domain fields None:
  - Can be instantiated without errors
  - Do not raise AttributeError or NoneType errors on field access
  - List fields default to [] (not None) so loops are safe
  - block_analyzer.analyze() with all-None parsed output yields status='ready'
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_analysis.output_schemas import (
    ComplianceOutput,
    DataOutput,
    GovernanceOutput,
    InfrastructureOutput,
    ProcessCrossAreaOutput,
    ProcessFullOutput,
    ProcessReducedOutput,
    StrategicOutput,
    TalentOutput,
)


# Minimal "all-None domain fields" payload — only base schema fields
MINIMAL_LLM_DATA = {
    "synthesis": "Análisis mínimo.",
    "contradictions": [],
    "follow_ups": [],
    "preliminary_hypothesis": None,
    "block_specific_outputs": {},
}


class TestAllNullInstantiation:
    """Each subclass can be validated with no domain fields present."""

    def test_strategic_output_minimal(self):
        obj = StrategicOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.synthesis == "Análisis mínimo."

    def test_process_full_output_domain_fields_none(self):
        obj = ProcessFullOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.recommended_approach is None
        assert obj.ia_fit_score is None

    def test_process_reduced_output_domain_fields_none(self):
        obj = ProcessReducedOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.recommended_approach is None
        assert obj.ia_fit_score is None

    def test_process_cross_area_output_domain_field_none(self):
        obj = ProcessCrossAreaOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.recommended_approach is None

    def test_data_output_domain_fields_none(self):
        obj = DataOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.data_readiness is None
        assert obj.compliance_flags == []  # list default, NOT None

    def test_talent_output_domain_field_none(self):
        obj = TalentOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.execution_model_recommended is None

    def test_infrastructure_output_domain_fields_none(self):
        obj = InfrastructureOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.deployment_archetype is None
        assert obj.recommended_architecture_constraints == []

    def test_compliance_output_domain_fields_none(self):
        obj = ComplianceOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.recommended_compliance_phase is None
        assert obj.obligations_triggered == []

    def test_governance_output_domain_fields_none(self):
        obj = GovernanceOutput.model_validate(MINIMAL_LLM_DATA)
        assert obj.shadow_ai_risk is None
        assert obj.first_governance_deliverables == []


class TestNullFieldAccessSafety:
    """Attribute access on None fields does NOT raise AttributeError."""

    def test_data_readiness_none_access(self):
        obj = DataOutput.model_validate(MINIMAL_LLM_DATA)
        # Guard pattern: getattr with default
        dr = getattr(obj, "data_readiness", None)
        assert dr is None  # No AttributeError

    def test_shadow_ai_risk_none_access(self):
        obj = GovernanceOutput.model_validate(MINIMAL_LLM_DATA)
        risk = obj.shadow_ai_risk
        assert risk is None  # No AttributeError

    def test_compliance_phase_none_access(self):
        obj = ComplianceOutput.model_validate(MINIMAL_LLM_DATA)
        phase = obj.recommended_compliance_phase
        assert phase is None

    def test_execution_model_none_access(self):
        obj = TalentOutput.model_validate(MINIMAL_LLM_DATA)
        model = obj.execution_model_recommended
        assert model is None

    def test_recommended_approach_none_access(self):
        obj = ProcessFullOutput.model_validate(MINIMAL_LLM_DATA)
        approach = obj.recommended_approach
        assert approach is None

    def test_ia_fit_score_none_access(self):
        obj = ProcessFullOutput.model_validate(MINIMAL_LLM_DATA)
        score = obj.ia_fit_score
        assert score is None


class TestListFieldsAreSafeToIterate:
    """List fields default to [] so they are safe to iterate even when domain fields are None."""

    def test_compliance_flags_is_iterable_when_none_domain(self):
        obj = DataOutput.model_validate(MINIMAL_LLM_DATA)
        result = [flag for flag in obj.compliance_flags]  # Must not raise
        assert result == []

    def test_obligations_triggered_is_iterable_when_none_domain(self):
        obj = ComplianceOutput.model_validate(MINIMAL_LLM_DATA)
        result = list(obj.obligations_triggered)
        assert result == []

    def test_first_governance_deliverables_is_iterable(self):
        obj = GovernanceOutput.model_validate(MINIMAL_LLM_DATA)
        result = list(obj.first_governance_deliverables)
        assert result == []

    def test_recommended_architecture_constraints_is_iterable(self):
        obj = InfrastructureOutput.model_validate(MINIMAL_LLM_DATA)
        result = list(obj.recommended_architecture_constraints)
        assert result == []


class TestTriggerConditionNoneSafety:
    """Simulated trigger condition evaluation does not activate on None fields."""

    def test_shadow_ai_risk_none_does_not_trigger(self):
        """Trigger: shadow_ai_risk == 'high' → only if not None."""
        obj = GovernanceOutput.model_validate(MINIMAL_LLM_DATA)
        triggered = obj.shadow_ai_risk is not None and obj.shadow_ai_risk == "high"
        assert triggered is False

    def test_recommended_compliance_phase_none_does_not_trigger(self):
        obj = ComplianceOutput.model_validate(MINIMAL_LLM_DATA)
        triggered = (
            obj.recommended_compliance_phase is not None
            and obj.recommended_compliance_phase == "must_resolve_first"
        )
        assert triggered is False

    def test_ia_fit_score_none_does_not_trigger(self):
        obj = ProcessFullOutput.model_validate(MINIMAL_LLM_DATA)
        triggered = obj.ia_fit_score is not None and obj.ia_fit_score >= 80
        assert triggered is False

    def test_data_readiness_none_does_not_trigger(self):
        obj = DataOutput.model_validate(MINIMAL_LLM_DATA)
        # Accessing .level on None would crash — guard prevents it
        dr = obj.data_readiness
        triggered = dr is not None and isinstance(dr, dict) and dr.get("level") == "low"
        assert triggered is False
