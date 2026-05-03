"""
app/models/assessment — Assessment model (hybrid flat+JSON schema).

Hybrid schema rationale (design §2.2):
  - FLAT columns: identity/status/scoring fields that need SQL filtering/sorting.
    These are queryable (WHERE, ORDER BY) and appear in the list view.
  - JSON blobs: llm_enriched_data, recommendation_data, form_data, field_sources.
    The JSON blobs hold the full rec dict sections; they are read as whole objects
    and never queried column-by-column in SQL.

Flat queryable columns (required for list/filter in AssessmentListPage):
  status, company_name, sector, employee_range, respondent_name_role, revenue_range,
  who_decides, budget, priority_text, maturity_score, maturity_level, risk_score,
  risk_level, priority_score, priority_level, pdf_path, pdf_generated_at,
  email_status, email_sent_at, email_error, created_at, updated_at

JSON blobs:
  form_data          — raw rec fields from map_form_to_rec (the full form answers)
  llm_enriched_data  — all llm_* fields written by enrich_llm step; NULL until enriched
  recommendation_data — structured recommendation data from enrich_recommendations step
  field_sources      — {field_name: 'human' | 'llm'} — explicit entries only;
                       absent = default (form fields → 'human', llm_* fields → 'llm')

Foreign keys:
  created_by_id      → users.id SET NULL on user delete (nullable)
  last_edited_by_id  → users.id SET NULL on user delete (nullable, NULL = system edit)

Status lifecycle:
  draft → pending_review → approved → archived
  (auto_publish=true skips pending_review on successful enrichment+PDF+email)

Email status lifecycle:
  not_sent → sent       (PDF generated + email delivered)
  not_sent → failed     (PDF generated + email delivery failed)
  failed   → sent       (retry via "Reenviar email" button in admin UI)

task_id:
  Legacy field from the pre-DB era. Kept nullable for backwards compatibility;
  new assessments use the jobs registry (in-memory) and don't need this column.
  Will be removed in a future migration once legacy data is migrated.

Indexes:
  idx_assessments_status     — list view default filter (excludes archived)
  idx_assessments_created_at — default sort on list view
"""

from datetime import datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base

logger = structlog.get_logger(__name__)


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # ── Status & lifecycle ────────────────────────────────────────────────────
    # Values: 'draft' | 'pending_review' | 'approved' | 'archived'
    # Index defined in __table_args__ as idx_assessments_status (named per convention).
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )

    # When True: on public submission, enrichment chain auto-publishes (PDF + email).
    # When False (default): stays at pending_review for consultant review.
    auto_publish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Timestamps ───────────────────────────────────────────────────────────
    # Index defined in __table_args__ as idx_assessments_created_at (named per convention).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    # Nullable FKs — SET NULL when user is deleted (handled in app layer since
    # SQLite doesn't support partial ON DELETE actions per-column in SQLAlchemy
    # mapped_column without explicit ForeignKey constructor; the migration sets
    # ON DELETE SET NULL at the DDL level).
    created_by_id: Mapped[UUID | None] = mapped_column(nullable=True)
    last_edited_by_id: Mapped[UUID | None] = mapped_column(nullable=True)

    # ── Flat identity columns (queryable / shown in list) ────────────────────
    company_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sector: Mapped[str] = mapped_column(Text, nullable=False, default="")
    employee_range: Mapped[str] = mapped_column(Text, nullable=False, default="")
    revenue_range: Mapped[str] = mapped_column(Text, nullable=False, default="")
    respondent_name_role: Mapped[str] = mapped_column(Text, nullable=False, default="")
    respondent_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    who_decides: Mapped[str] = mapped_column(Text, nullable=False, default="")
    budget: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Scoring columns (flat — queryable for score range filter) ────────────
    maturity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    maturity_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_level: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Intermediate scoring sub-scores (from scoring_engine pts_* fields).
    # Stored flat so the editor can display them without parsing JSON.
    pts_tools: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_automation: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_area_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_governance: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_goal_clarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_data_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_ai_personal_data: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_dpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_dpia: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_automated_decisions: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_sector: Mapped[float | None] = mapped_column(Float, nullable=True)
    pts_incident: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── PDF & email ───────────────────────────────────────────────────────────
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # email_status: 'not_sent' | 'sent' | 'failed'
    # Design decision (§0 A3): PDF success criterion = approved; email is separate.
    email_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="not_sent"
    )
    email_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    email_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Legacy compatibility ──────────────────────────────────────────────────
    # task_id from the pre-DB era (process_assessment_v2 returned a threading task id).
    # Kept nullable; new rows will have this as NULL. Remove once legacy data is cleared.
    task_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── JSON blobs ────────────────────────────────────────────────────────────

    # Raw form fields as returned by map_form_to_rec() — the full rec dict.
    # Stored so the editor can display all form answers and the LLM re-run
    # has access to the complete context.
    form_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # All llm_* fields from enrich_llm step. NULL until first enrichment runs.
    # Shape matches the rec dict keys starting with llm_:
    #   llm_executive_summary, llm_current_state, llm_opportunities,
    #   llm_final_recommendation, llm_final_narrative, llm_tools_list,
    #   llm_next_step_proposal, llm_risk_findings, llm_roadmap_30_60_90,
    #   llm_scoring_answers, llm_inventory_table, llm_risk_findings_structured,
    #   llm_opportunity_matrix, llm_economic_estimate, llm_roadmap_structured,
    #   llm_dependencies, llm_tool_recommendations, llm_followup_questions,
    #   llm_ai_policy_draft, llm_dpa_guidance
    llm_enriched_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Structured recommendation data from enrich_recommendations step.
    recommendation_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Field source tracking: {field_name: 'human' | 'llm'}
    # Only stores EXPLICIT overrides — absent key means use default:
    #   form-derived fields → default 'human'
    #   llm_* fields → default 'llm'
    # Every PATCH sets field_sources[field_name] = 'human' for patched fields.
    # LLM re-run skips fields where field_sources.get(field) == 'human'.
    field_sources: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_assessments_status", "status"),
        Index("idx_assessments_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Assessment id={self.id} company={self.company_name!r} "
            f"status={self.status} maturity={self.maturity_score}>"
        )
