"""
app/services/ai_analysis/output_schemas — Pydantic v2 output schemas for LLM responses.

Common schema (all blocks):
  synthesis, contradictions, follow_ups, preliminary_hypothesis, block_specific_outputs

Block-specific schemas add additional validated fields — ALL domain fields are Optional
so that partial LLM responses do not fail the pipeline (REQ-2 / ADR-2).
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Common sub-models
# ---------------------------------------------------------------------------

class Contradiction(BaseModel):
    text: str
    severity: Literal["low", "med", "high"]


class FollowUp(BaseModel):
    text: str
    rationale: str
    priority: Literal["high", "med", "low"]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


# ---------------------------------------------------------------------------
# Base output model (all blocks share this)
# ---------------------------------------------------------------------------

class BlockAnalysisOutput(BaseModel):
    """Common output schema for all block analyses.

    extra='allow' keeps unexpected LLM keys rather than rejecting them (ADR-2).
    """

    model_config = ConfigDict(extra="allow")

    synthesis: Optional[str] = None
    contradictions: list[Contradiction] = Field(default_factory=list)
    follow_ups: list[FollowUp] = Field(default_factory=list)
    preliminary_hypothesis: Optional[str] = None
    block_specific_outputs: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Block-1 Strategic — no extra fields required
# ---------------------------------------------------------------------------

class StrategicOutput(BlockAnalysisOutput):
    """Block-1 strategic output — common fields only."""
    pass


# ---------------------------------------------------------------------------
# Block-2 Process (full variant)
# ---------------------------------------------------------------------------

ProcessApproach = Literal[
    "automation_simple",
    "automation_advanced",
    "rules_engine",
    "ai_with_guardrails",
    "ai_full",
    "not_recommended",
]


class ProcessFullOutput(BlockAnalysisOutput):
    """Block-2 process (full variant) output."""

    recommended_approach: Optional[ProcessApproach] = None
    ia_fit_score: Optional[int] = None


# ---------------------------------------------------------------------------
# Block-2 Process (reduced variant)
# ---------------------------------------------------------------------------

class ProcessReducedOutput(BlockAnalysisOutput):
    """Block-2 process (reduced variant) output — same as full."""

    recommended_approach: Optional[ProcessApproach] = None
    ia_fit_score: Optional[int] = None


# ---------------------------------------------------------------------------
# Block-2 Cross-area
# ---------------------------------------------------------------------------

CrossAreaApproach = Literal[
    "single_source_of_truth",
    "integration_layer",
    "centralized_dashboard",
    "process_redesign",
    "governance_first",
    "ai_assisted_routing",
]


class ProcessCrossAreaOutput(BlockAnalysisOutput):
    """Block-2 cross-area output."""

    recommended_approach: Optional[CrossAreaApproach] = None


# ---------------------------------------------------------------------------
# Block-3 Data
# ---------------------------------------------------------------------------

class DataReadiness(BaseModel):
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    level: Literal["low", "medium", "high"]


class DataOutput(BlockAnalysisOutput):
    """Block-3 data output."""

    data_readiness: Optional[DataReadiness | dict] = None
    compliance_flags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Block-4 Talent
# ---------------------------------------------------------------------------

ExecutionModel = Literal["saas_only", "partner_managed", "hybrid", "in_house"]


class TalentOutput(BlockAnalysisOutput):
    """Block-4 talent output."""

    execution_model_recommended: Optional[ExecutionModel] = None


# ---------------------------------------------------------------------------
# Block-5 Infrastructure
# ---------------------------------------------------------------------------

class InfrastructureOutput(BlockAnalysisOutput):
    """Block-5 infrastructure output."""

    deployment_archetype: Optional[str] = None
    recommended_architecture_constraints: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Block-6 Compliance
# ---------------------------------------------------------------------------

CompliancePhase = Literal["must_resolve_first", "parallel_to_pilot", "post_pilot"]


class ComplianceOutput(BlockAnalysisOutput):
    """Block-6 compliance output."""

    recommended_compliance_phase: Optional[CompliancePhase] = None
    obligations_triggered: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Block-7 Governance
# ---------------------------------------------------------------------------

class GovernanceOutput(BlockAnalysisOutput):
    """Block-7 governance output."""

    shadow_ai_risk: Optional[Literal["low", "medium", "high"]] = None
    first_governance_deliverables: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry: block_id → output schema class
# ---------------------------------------------------------------------------

BLOCK_OUTPUT_SCHEMA: dict[str, type[BlockAnalysisOutput]] = {
    "block-1-strategic": StrategicOutput,
    "block-2-process-critical-full": ProcessFullOutput,
    "block-2-process-critical-reduced": ProcessReducedOutput,
    "block-2-process-critical-cross-area": ProcessCrossAreaOutput,
    "block-3-data": DataOutput,
    "block-4-talent": TalentOutput,
    "block-5-infrastructure": InfrastructureOutput,
    "block-6-compliance": ComplianceOutput,
    "block-7-governance": GovernanceOutput,
}


def get_output_schema(block_id: str) -> type[BlockAnalysisOutput]:
    """Return the Pydantic output schema class for a given block_id."""
    return BLOCK_OUTPUT_SCHEMA.get(block_id, BlockAnalysisOutput)
