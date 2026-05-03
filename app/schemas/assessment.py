"""
app/schemas/assessment — Pydantic v2 schemas for the admin assessment API.

Schema hierarchy:
  AssessmentStatus     — lifecycle enum (draft | pending_review | approved | archived)
  EmailStatus          — email delivery enum (not_sent | sent | failed)
  AssessmentListItem   — compact row for list view (14 fields)
  AssessmentResponse   — full assessment for the editor (44 model columns + derived)
  AssessmentCreate     — payload to create a new assessment from scratch (admin path)
  AssessmentPatch      — partial update payload (all fields Optional — debounced PATCH)
  AssessmentListResponse — paginated list wrapper
  JobStatus            — job lifecycle enum
  JobType              — job type enum
  JobRecord            — single job record shape (from in-memory registry)

All response schemas use `model_config = ConfigDict(from_attributes=True)` so
they can be constructed directly from SQLAlchemy ORM instances:
    AssessmentResponse.model_validate(orm_row)

Design reference: design §1 (app/schemas/assessment.py), design §2.7
(field_sources), design §2.3 (JobRegistry shape), tasks TASK-B-02.

Column alignment: every field here matches the corresponding Mapped[] column
in app/models/assessment.py.  Column count: 44 Mapped[] annotations.

FORM_DATA_KEYS / _FLAT_COLUMN_FIELDS (TASK-IN-01):
  Circular-import safe: public_routes.py only imports app.schemas.common,
  NOT app.schemas.assessment, so this import is one-directional.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.public_routes import PublicSubmissionPayload

# ---------------------------------------------------------------------------
# TASK-IN-01: Canonical form_data key set
# ---------------------------------------------------------------------------

# Fields from PublicSubmissionPayload that are stored as flat ORM columns and
# MUST NOT go into form_data.  Also includes defensive entries for admin-only
# flat fields (who_decides, budget, priority_text) and the reserved _token
# key — none of these are in PublicSubmissionPayload, so the frozenset
# subtraction is a no-op for them; they are listed here so future readers
# understand why they're excluded and don't accidentally re-add them.
_FLAT_COLUMN_FIELDS: frozenset[str] = frozenset({
    "company_name",
    "sector",
    "employee_range",
    "revenue_range",
    "respondent_name_role",   # admin-only flat column, not in PublicSubmissionPayload
    "respondent_email",
    "who_decides",            # admin-only flat column, not in PublicSubmissionPayload
    "budget",                 # admin-only flat shadow of investment_budget (R5 sync target)
    "priority_text",          # admin-only flat shadow of urgency (R5 sync target)
    "auto_publish",
    "_token",                 # reserved exclusion — not in current payload
})

# Built once at import time.
# PublicSubmissionPayload has 48 fields; 6 of them are in _FLAT_COLUMN_FIELDS
# (company_name, sector, employee_range, revenue_range, respondent_email,
# auto_publish).  The remaining 5 entries in _FLAT_COLUMN_FIELDS are not in
# PublicSubmissionPayload so the subtraction is a no-op for them.
# Result: 48 - 6 = 42 canonical form_data keys.
FORM_DATA_KEYS: frozenset[str] = (
    frozenset(PublicSubmissionPayload.model_fields.keys()) - _FLAT_COLUMN_FIELDS
)

# Form-data → flat-column sync mapping (design R5).
# When PATCH writes the LHS form_data key, the RHS flat column is also updated.
# ONE-WAY: form_data → flat only (flat edits do not propagate back to form_data).
FORM_DATA_TO_FLAT_SYNC: dict[str, str] = {
    "investment_budget": "budget",
    "urgency": "priority_text",
}


# ── Enums ─────────────────────────────────────────────────────────────────────


class AssessmentStatus(str, Enum):
    """Assessment lifecycle states."""

    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    archived = "archived"


class EmailStatus(str, Enum):
    """Email delivery states."""

    not_sent = "not_sent"
    sent = "sent"
    failed = "failed"


class JobStatus(str, Enum):
    """Job lifecycle states (mirrors app/jobs/registry.py JobStatus)."""

    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class JobType(str, Enum):
    """Job types supported by the registry."""

    enrich_llm = "enrich_llm"
    enrich_recommendations = "enrich_recommendations"
    score = "score"
    generate_pdf = "generate_pdf"
    preview_pdf = "preview_pdf"
    approve_and_send = "approve_and_send"
    public_submission = "public_submission"
    resend_email = "resend_email"


# ── Job schemas ────────────────────────────────────────────────────────────────


class JobRecord(BaseModel):
    """Shape of a job record from the in-memory registry.

    Used by GET /api/admin/assessments/{id}/jobs.
    No from_attributes needed — constructed from the dataclass, not ORM.
    """

    id: str
    type: JobType
    assessment_id: str
    status: JobStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


# ── List item schema ───────────────────────────────────────────────────────────


class AssessmentListItem(BaseModel):
    """Compact assessment row for the list view.

    14 fields — only what is needed to render the list table and filters.
    Avoids serialising large JSON blobs (llm_enriched_data, recommendation_data).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: AssessmentStatus
    company_name: str
    sector: str
    employee_range: str
    created_at: datetime
    updated_at: datetime

    # Scoring (nullable until scoring step runs)
    maturity_score: float | None = None
    maturity_level: str | None = None
    risk_score: float | None = None

    # PDF & email
    pdf_path: str | None = None
    email_status: EmailStatus = EmailStatus.not_sent

    # Ownership
    last_edited_by_id: UUID | None = None


# ── Full response schema ───────────────────────────────────────────────────────


class AssessmentResponse(BaseModel):
    """Full assessment for the editor.

    Covers ALL 44 Mapped[] columns from app/models/assessment.py plus
    field_sources (JSON column, already on the model).
    Use model_validate(orm_instance) to construct from SQLAlchemy rows.
    """

    model_config = ConfigDict(from_attributes=True)

    # ── Identity ──────────────────────────────────────────────────────────────
    id: UUID
    status: AssessmentStatus
    auto_publish: bool

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: datetime
    updated_at: datetime

    # ── Ownership ────────────────────────────────────────────────────────────
    created_by_id: UUID | None = None
    last_edited_by_id: UUID | None = None

    # ── Flat identity columns ─────────────────────────────────────────────────
    company_name: str
    sector: str
    employee_range: str
    revenue_range: str
    respondent_name_role: str
    respondent_email: str | None = None
    who_decides: str
    budget: str
    priority_text: str

    # ── Scoring (flat queryable) ──────────────────────────────────────────────
    maturity_score: float | None = None
    maturity_level: str | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    priority_score: float | None = None
    priority_level: str | None = None

    # Sub-score pts_* (flat in model for editor display)
    pts_tools: float | None = None
    pts_automation: float | None = None
    pts_area_usage: float | None = None
    pts_governance: float | None = None
    pts_goal_clarity: float | None = None
    pts_data_risk: float | None = None
    pts_ai_personal_data: float | None = None
    pts_dpa: float | None = None
    pts_dpia: float | None = None
    pts_automated_decisions: float | None = None
    pts_sector: float | None = None
    pts_incident: float | None = None

    # ── PDF & email ───────────────────────────────────────────────────────────
    pdf_path: str | None = None
    pdf_generated_at: datetime | None = None
    email_status: EmailStatus = EmailStatus.not_sent
    email_sent_at: datetime | None = None
    email_error: str | None = None

    # ── Legacy ────────────────────────────────────────────────────────────────
    task_id: str | None = None

    # ── JSON blobs ────────────────────────────────────────────────────────────
    # form_data: raw rec dict from map_form_to_rec
    form_data: dict[str, Any] = Field(default_factory=dict)

    # llm_enriched_data: all llm_* fields; NULL until first enrichment
    llm_enriched_data: dict[str, Any] | None = None

    # recommendation_data: structured reco output
    recommendation_data: dict[str, Any] | None = None

    # field_sources: {field_name: 'human' | 'llm'} — explicit entries only
    # Absent key → default ('human' for form fields, 'llm' for llm_* fields)
    field_sources: dict[str, str] = Field(default_factory=dict)


# ── Create schema ──────────────────────────────────────────────────────────────


class AssessmentCreate(BaseModel):
    """Payload to create a new assessment from scratch (admin path — no public form).

    All fields have defaults so the admin can create a minimal draft and fill
    the rest in the editor via debounced PATCH.
    Required fields for a meaningful assessment: company_name, sector.
    """

    model_config = ConfigDict(extra="forbid")

    # Core identity
    company_name: str = Field(default="", description="Nombre de la empresa")
    sector: str = Field(default="", description="Sector de actividad")
    employee_range: str = Field(default="", description="Rango de empleados")
    revenue_range: str = Field(default="", description="Rango de facturación")
    respondent_name_role: str = Field(default="", description="Nombre y cargo del respondente")
    respondent_email: str | None = Field(default=None, description="Email del contacto cliente")
    who_decides: str = Field(default="", description="Quién toma decisiones tecnológicas")
    budget: str = Field(default="", description="Presupuesto de inversión en IA")
    priority_text: str = Field(default="", description="Urgencia / prioridad declarada")

    # Pipeline control
    auto_publish: bool = Field(
        default=False,
        description=(
            "Si True: en el flujo público, tras enriquecimiento se genera PDF "
            "y se envía email automáticamente (status=approved). "
            "Si False (default): queda en pending_review."
        ),
    )

    # Initial form data blob (optional — can be empty dict, filled via PATCH later)
    form_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Datos del formulario en formato rec (opcional en creación desde admin)",
    )


# ── Patch schema ───────────────────────────────────────────────────────────────


class AssessmentPatch(BaseModel):
    """Partial update payload for the debounced editor PATCH.

    ALL fields are Optional[...] — only send the fields you want to update.
    Every included non-None field gets field_sources[field_name] = 'human'
    automatically in the PATCH endpoint handler.

    model_config extra='forbid' prevents sending unknown fields (typo guard).
    """

    model_config = ConfigDict(extra="forbid")

    # ── Flat identity ──────────────────────────────────────────────────────────
    status: AssessmentStatus | None = None
    auto_publish: bool | None = None
    company_name: str | None = None
    sector: str | None = None
    employee_range: str | None = None
    revenue_range: str | None = None
    respondent_name_role: str | None = None
    respondent_email: str | None = None
    who_decides: str | None = None
    budget: str | None = None
    priority_text: str | None = None

    # ── Scoring overrides (admin can manually correct scores) ─────────────────
    maturity_score: float | None = None
    maturity_level: str | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    priority_score: float | None = None
    priority_level: str | None = None

    # Sub-score pts_* (admin can correct individual sub-scores)
    pts_tools: float | None = None
    pts_automation: float | None = None
    pts_area_usage: float | None = None
    pts_governance: float | None = None
    pts_goal_clarity: float | None = None
    pts_data_risk: float | None = None
    pts_ai_personal_data: float | None = None
    pts_dpa: float | None = None
    pts_dpia: float | None = None
    pts_automated_decisions: float | None = None
    pts_sector: float | None = None
    pts_incident: float | None = None

    # ── LLM-enriched fields (admin can manually edit) ─────────────────────────
    # Stored inside llm_enriched_data JSON blob; editor sends individual fields
    # as top-level patch keys so field_sources tracking works field-by-field.
    llm_executive_summary: str | None = None
    llm_current_state: str | None = None
    llm_opportunities: str | None = None
    llm_final_recommendation: str | None = None
    llm_final_narrative: str | None = None
    llm_tools_list: str | None = None
    llm_next_step_proposal: str | None = None
    llm_risk_findings: str | None = None
    llm_roadmap_30_60_90: str | None = None

    # Structured LLM fields (patched as dicts/lists)
    llm_scoring_answers: dict[str, Any] | None = None
    llm_inventory_table: list[Any] | None = None
    llm_risk_findings_structured: list[Any] | None = None
    llm_opportunity_matrix: list[Any] | None = None
    llm_economic_estimate: dict[str, Any] | None = None
    llm_roadmap_structured: list[Any] | None = None
    llm_dependencies: list[Any] | None = None
    llm_tool_recommendations: list[Any] | None = None
    llm_followup_questions: list[Any] | None = None
    llm_ai_policy_draft: str | None = None
    llm_dpa_guidance: str | None = None

    # ── Email status (admin retry) ────────────────────────────────────────────
    email_status: EmailStatus | None = None
    email_error: str | None = None

    # ── JSON blobs (bulk update, e.g. from import) ────────────────────────────
    form_data: dict[str, Any] | None = None
    llm_enriched_data: dict[str, Any] | None = None
    recommendation_data: dict[str, Any] | None = None

    # ── form_data deep-merge (TASK-IN-02 / CAP-S-IN-001) ─────────────────────
    # Mutually exclusive with form_data (which requires ?mode=replace).
    # All keys must belong to FORM_DATA_KEYS (canonical allowlist).
    form_data_patch: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Partial form_data update. Keys are merged into existing form_data. "
            "Mutually exclusive with form_data (which requires ?mode=replace). "
            "All keys must belong to the canonical form_data key set (FORM_DATA_KEYS)."
        ),
    )

    @model_validator(mode="after")
    def _validate_form_data_exclusivity(self) -> Self:
        """R1: form_data and form_data_patch are mutually exclusive (CAP-A-IN-003)."""
        if self.form_data is not None and self.form_data_patch is not None:
            raise ValueError(
                "form_data and form_data_patch are mutually exclusive. "
                "Use form_data_patch for partial updates (default), "
                "or form_data with ?mode=replace for wholesale replacement."
            )
        return self

    @model_validator(mode="after")
    def _validate_form_data_patch_keys(self) -> Self:
        """CAP-S-IN-001: every key in form_data_patch must be in FORM_DATA_KEYS."""
        if self.form_data_patch is None:
            return self
        unknown = set(self.form_data_patch.keys()) - FORM_DATA_KEYS
        if unknown:
            offending = sorted(unknown)[0]
            raise ValueError(
                f"Unknown form_data key: {offending}. "
                "Allowed keys are derived from PublicSubmissionPayload."
            )
        return self


# ── List response schema ───────────────────────────────────────────────────────


class AssessmentListResponse(BaseModel):
    """Paginated list of assessments."""

    items: list[AssessmentListItem]
    total: int = Field(description="Total count matching the filter (before pagination)")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
