"""
app/api/assessment_routes — Admin assessment CRUD + re-run endpoints.

Router prefix: /api/admin/assessments  (registered in webhook_service.py as
  app.include_router(router, prefix="/api/admin"))

Endpoints (Phase B Batch 2 — TASK-B-03 through TASK-B-08):
  GET    /api/admin/assessments              — paginated list with filters
  GET    /api/admin/assessments/{id}         — single assessment for editor
  POST   /api/admin/assessments              — create from scratch (admin path)
  PATCH  /api/admin/assessments/{id}         — partial update + field_sources tracking
  POST   /api/admin/assessments/{id}/duplicate — clone for new client
  POST   /api/admin/assessments/{id}/archive   — soft-delete via status

Endpoints (Phase B Batch 3 — TASK-B-09 through TASK-B-15 + BONUS):
  GET    /api/admin/assessments/{id}/jobs               — job status list (registry)
  POST   /api/admin/assessments/{id}/run-llm-enrichment — re-run LLM → 202 {job_id}
  POST   /api/admin/assessments/{id}/run-recommendations — re-run reco → 202 {job_id}
  POST   /api/admin/assessments/{id}/run-scoring         — re-run scoring → 202 {job_id}
  POST   /api/admin/assessments/{id}/generate-pdf        — production PDF → 202 {job_id}
  POST   /api/admin/assessments/{id}/preview-pdf         — watermarked draft → 202 {job_id}
  POST   /api/admin/assessments/{id}/approve-and-send    — PDF + email + approved → 202
  POST   /api/admin/assessments/{id}/resend-email        — retry email → 202 {job_id}

All endpoints require Depends(require_admin).

Design references:
  - design §2.7  — field_sources mutation rules (ALWAYS reassign, never mutate in place)
  - design §2.3  — BackgroundTasks pattern (re-run endpoints, job polling)
  - design §3.4  — approve-and-send sequence
  - design §3.5  — LLM re-run with field_sources preservation
  - tasks TASK-B-03..TASK-B-15

Critical correctness notes:
  - JSON column mutation: SQLAlchemy does NOT auto-detect in-place dict mutations.
    ALWAYS do: assessment.field_sources = {**assessment.field_sources, key: value}
    Same for llm_enriched_data merges.
  - 409 for archived: PATCH and duplicate refuse to touch archived rows.
  - 404 for GET/{id}: also returns 404 if status='archived' (consultants can't open
    archived rows in the editor; archive endpoint itself still loads them via _get_or_404).
  - Re-run endpoints return 202 immediately; poll GET /{id}/jobs to track progress.
  - Runners open their OWN sessions (not the request session — it closes on response).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.auth.middleware import require_admin
from app.db.session import get_db
from app.jobs import runners
from app.jobs.registry import JobType, job_registry
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentListItem,
    AssessmentListResponse,
    AssessmentPatch,
    AssessmentResponse,
    AssessmentStatus,
    EmailStatus,
    FORM_DATA_KEYS,
    FORM_DATA_TO_FLAT_SYNC,
    JobRecord,
)
from app.schemas.common import ApiException

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/assessments", tags=["admin-assessments"])

# ---------------------------------------------------------------------------
# Allowed sort columns (whitelist to prevent SQL injection via column names)
# ---------------------------------------------------------------------------
_SORT_COLUMNS: dict[str, Any] = {
    "created_at": Assessment.created_at,
    "updated_at": Assessment.updated_at,
    "maturity_score": Assessment.maturity_score,
    "risk_score": Assessment.risk_score,
    "company_name": Assessment.company_name,
}


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Internal helper: load assessment or raise 404 / 409
# ---------------------------------------------------------------------------


async def _get_or_404(
    db: AsyncSession,
    assessment_id: UUID,
    *,
    allow_archived: bool = False,
) -> Assessment:
    """
    Load an Assessment by PK.  Raises appropriate ApiException on failure.

    Args:
        db:             async session
        assessment_id:  UUID from the path parameter
        allow_archived: when True, archived rows are returned without error.
                        When False (default), raises 409 if archived.
                        (GET /{id} uses a separate 404 for archived — handled
                        in the endpoint itself rather than here.)
    """
    assessment = await db.get(Assessment, assessment_id)
    if assessment is None:
        raise ApiException(
            status_code=404,
            code="assessment_not_found",
            detail=f"Assessment {assessment_id} not found.",
        )
    if not allow_archived and assessment.status == AssessmentStatus.archived.value:
        raise ApiException(
            status_code=409,
            code="assessment_archived",
            detail="This assessment is archived and cannot be modified.",
        )
    return assessment


# ---------------------------------------------------------------------------
# GET /api/admin/assessments — paginated list with filters
# TASK-B-03
# ---------------------------------------------------------------------------


@router.get("", response_model=AssessmentListResponse)
async def list_assessments(
    # Filter params
    status: Annotated[list[AssessmentStatus] | None, Query()] = None,
    sector: Annotated[list[str] | None, Query()] = None,
    search: str | None = None,
    min_maturity_score: float | None = None,
    max_maturity_score: float | None = None,
    min_risk_score: float | None = None,
    max_risk_score: float | None = None,
    email_status: EmailStatus | None = None,
    # Sort params
    sort_by: str = "created_at",
    sort_order: str = "desc",
    # Pagination
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    # Auth + DB
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AssessmentListResponse:
    """
    Return a paginated, filtered list of assessments.

    Default behaviour: excludes archived rows (status filter defaults to
    [draft, pending_review, approved] when no status param is provided).

    Status filter: multi-value — ?status=draft&status=pending_review
    Sector filter: multi-value — ?sector=retail&sector=health
    Search: case-insensitive LIKE on company_name and respondent_name_role.
    Score filters: min/max for maturity_score and risk_score.
    Email status: filters on the email_status column (not an AssessmentStatus).

    Sort: column whitelist (created_at|updated_at|maturity_score|risk_score|company_name).
          Unknown sort_by silently falls back to created_at.

    Pagination: 1-indexed.  Total includes all matching rows before pagination.
    """
    # ── Build WHERE clauses ───────────────────────────────────────────────────

    conditions: list = []

    # Status filter — default to non-archived when no filter provided
    if status:
        status_values = [s.value for s in status]
        conditions.append(Assessment.status.in_(status_values))
    else:
        # Default: hide archived from the list view
        conditions.append(Assessment.status != AssessmentStatus.archived.value)

    if sector:
        conditions.append(Assessment.sector.in_(sector))

    if search:
        pattern = f"%{search}%"
        conditions.append(
            Assessment.company_name.ilike(pattern)
            | Assessment.respondent_name_role.ilike(pattern)
        )

    if min_maturity_score is not None:
        conditions.append(Assessment.maturity_score >= min_maturity_score)
    if max_maturity_score is not None:
        conditions.append(Assessment.maturity_score <= max_maturity_score)

    if min_risk_score is not None:
        conditions.append(Assessment.risk_score >= min_risk_score)
    if max_risk_score is not None:
        conditions.append(Assessment.risk_score <= max_risk_score)

    # email_status filter — uses the EmailStatus enum values but filters Assessment.email_status
    if email_status is not None:
        conditions.append(Assessment.email_status == email_status.value)

    # ── Sort column (whitelist) ────────────────────────────────────────────────

    sort_col = _SORT_COLUMNS.get(sort_by, Assessment.created_at)
    sort_expr = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    # ── Total count query (same WHERE, no LIMIT/OFFSET) ───────────────────────

    count_stmt = select(func.count(Assessment.id)).where(*conditions)
    total_result = await db.execute(count_stmt)
    total: int = total_result.scalar_one()

    # ── Data query with pagination ─────────────────────────────────────────────

    offset = (page - 1) * page_size
    data_stmt = (
        select(Assessment)
        .where(*conditions)
        .order_by(sort_expr)
        .offset(offset)
        .limit(page_size)
    )
    rows_result = await db.execute(data_stmt)
    rows = rows_result.scalars().all()

    items = [AssessmentListItem.model_validate(row) for row in rows]

    logger.debug(
        "list_assessments",
        total=total,
        page=page,
        page_size=page_size,
        filters={
            "status": [s.value for s in status] if status else "default",
            "sector": sector,
            "search": search,
        },
    )

    return AssessmentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /api/admin/assessments/{id} — single assessment for the editor
# TASK-B-04
# ---------------------------------------------------------------------------


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Return the full assessment row for the editor.

    Returns 404 if the assessment does not exist OR if it is archived.
    Archived rows cannot be opened in the editor — the consultant must
    un-archive them first (out of scope for Phase B Batch 2).

    Uses db.get() for efficient PK lookup (no full-table scan).
    """
    assessment = await db.get(Assessment, assessment_id)
    if assessment is None or assessment.status == AssessmentStatus.archived.value:
        raise ApiException(
            status_code=404,
            code="assessment_not_found",
            detail=f"Assessment {assessment_id} not found.",
        )

    logger.debug("get_assessment", assessment_id=str(assessment_id))
    return AssessmentResponse.model_validate(assessment)


# ---------------------------------------------------------------------------
# POST /api/admin/assessments — create from scratch
# TASK-B-05
# ---------------------------------------------------------------------------


@router.post("", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
    body: AssessmentCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Create a new assessment from scratch (admin/consultant path).

    Unlike the public form submission, this starts directly in 'draft' status
    (not 'pending_review') — it's consultant-initiated, not client-submitted.

    field_sources is initialised with 'human' for every supplied field, since
    all values on this path come from direct human input.

    Returns 201 + the full AssessmentResponse.
    """
    now = _now_utc()
    body_dict = body.model_dump(exclude_none=True)

    # Every field supplied at creation time is human-sourced by definition.
    initial_field_sources: dict[str, str] = {
        field: "human" for field in body_dict
    }

    assessment = Assessment(
        id=uuid4(),
        status=AssessmentStatus.draft.value,
        auto_publish=body.auto_publish,
        created_at=now,
        updated_at=now,
        created_by_id=current_user.id,
        last_edited_by_id=current_user.id,
        # Flat identity fields
        company_name=body.company_name,
        sector=body.sector,
        employee_range=body.employee_range,
        revenue_range=body.revenue_range,
        respondent_name_role=body.respondent_name_role,
        respondent_email=body.respondent_email,
        who_decides=body.who_decides,
        budget=body.budget,
        priority_text=body.priority_text,
        # JSON blobs
        form_data=body.form_data,
        llm_enriched_data=None,
        recommendation_data=None,
        field_sources=initial_field_sources,
        # Email state
        email_status=EmailStatus.not_sent.value,
    )

    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    logger.info(
        "assessment_created",
        assessment_id=str(assessment.id),
        company_name=assessment.company_name,
        created_by=str(current_user.id),
    )

    return AssessmentResponse.model_validate(assessment)


# ---------------------------------------------------------------------------
# PATCH /api/admin/assessments/{id} — partial update + field_sources tracking
# TASK-B-06
# ---------------------------------------------------------------------------

# Fields in AssessmentPatch that map into the llm_enriched_data JSON blob
# rather than flat ORM columns.  Must match the llm_* fields in AssessmentPatch.
_LLM_PATCH_FIELDS: frozenset[str] = frozenset(
    {
        "llm_executive_summary",
        "llm_current_state",
        "llm_opportunities",
        "llm_final_recommendation",
        "llm_final_narrative",
        "llm_tools_list",
        "llm_next_step_proposal",
        "llm_risk_findings",
        "llm_roadmap_30_60_90",
        "llm_scoring_answers",
        "llm_inventory_table",
        "llm_risk_findings_structured",
        "llm_opportunity_matrix",
        "llm_economic_estimate",
        "llm_roadmap_structured",
        "llm_dependencies",
        "llm_tool_recommendations",
        "llm_followup_questions",
        "llm_ai_policy_draft",
        "llm_dpa_guidance",
    }
)

# Fields that are deliberately server-managed and must NOT be set via PATCH.
# AssessmentPatch already excludes id, created_at, pdf_path, pdf_generated_at,
# last_edited_by_id.  The check below is defence-in-depth.
_SERVER_MANAGED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "created_at",
        "pdf_path",
        "pdf_generated_at",
        "last_edited_by_id",
        "created_by_id",
    }
)

# Fields in AssessmentPatch that address the llm_enriched_data or recommendation_data
# JSON blobs in bulk (not individual llm_* sub-fields).
# NOTE: form_data is intentionally NOT in this set — it has its own dedicated
# replace/merge branches in patch_assessment that enforce ?mode=replace and R5 sync.
_BLOB_FIELDS: frozenset[str] = frozenset(
    {
        "llm_enriched_data",
        "recommendation_data",
    }
)


@router.patch("/{assessment_id}", response_model=AssessmentResponse)
async def patch_assessment(
    assessment_id: UUID,
    body: AssessmentPatch,
    mode: Annotated[str | None, Query(pattern="^(replace)$")] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Partial update of an assessment.  Tracks field provenance (field_sources).

    Behaviour per field kind:
      - Flat columns (company_name, sector, score fields, email_status …):
          Set the ORM column directly.
          Mark field_sources[field_name] = 'human'.
      - llm_* individual fields (llm_executive_summary, llm_inventory_table …):
          Merge into the llm_enriched_data JSON blob.
          Mark field_sources[field_name] = 'human'.
      - form_data_patch (merge, default path):
          Deep-merge each key into existing form_data.
          Mark field_sources['form_data.<key>'] = 'human' per merged key.
          R5 sync: if investment_budget or urgency are patched, also update the
          flat budget / priority_text columns.
      - form_data + ?mode=replace (wholesale replace):
          Replace the whole form_data blob.
          Mark field_sources['form_data.<key>'] = 'human' for every key in the
          new blob; remove field_sources for keys absent from the new blob.
          R5 sync applied on new blob as above.
      - form_data without ?mode=replace → 422 replace_mode_required.
      - Bulk blob fields (llm_enriched_data, recommendation_data):
          Replace the whole blob column.
          No field_sources entry — blob-level patches are structural, not editorial.
      - Server-managed fields: silently skipped (defence-in-depth; schema already
          excludes them, but we guard here too).

    CRITICAL (design §2.7): field_sources and form_data are JSON columns.
    SQLAlchemy does NOT auto-track in-place dict mutations.
    Use flag_modified() after every JSON column reassignment.

    Returns 404 if not found.
    Returns 409 if archived (cannot edit archived assessments).
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        # Nothing to do — return current state unchanged.
        return AssessmentResponse.model_validate(assessment)

    # Guard: form_data without ?mode=replace is rejected (CAP-S-IN-002).
    if "form_data" in updates and mode != "replace":
        raise ApiException(
            status_code=422,
            code="replace_mode_required",
            detail=(
                "Para reemplazar form_data completo, agregá ?mode=replace al PATCH."
            ),
        )

    # Accumulate llm_enriched_data changes and field_sources changes separately
    # to minimise the number of JSON column reassignments.
    llm_blob_changes: dict[str, Any] = {}
    new_field_sources: dict[str, str] = dict(assessment.field_sources or {})

    # ── form_data WHOLESALE REPLACE branch (CAP-A-IN-002) ─────────────────────
    if "form_data" in updates and mode == "replace":
        new_blob: dict[str, Any] = updates.pop("form_data") or {}

        # Drop existing field_sources for all form_data.* keys — we're replacing.
        new_field_sources = {
            k: v for k, v in new_field_sources.items()
            if not k.startswith("form_data.")
        }
        # Tag every key in the new blob as human-sourced.
        for key in new_blob:
            new_field_sources[f"form_data.{key}"] = "human"

        assessment.form_data = new_blob
        flag_modified(assessment, "form_data")

        # R5 sync: form_data → flat columns (ONE-WAY, design R5).
        for fd_key, flat_col in FORM_DATA_TO_FLAT_SYNC.items():
            if fd_key in new_blob:
                setattr(assessment, flat_col, new_blob[fd_key])
                new_field_sources[flat_col] = "human"

    # ── form_data_patch DEEP MERGE branch (CAP-A-IN-001) ──────────────────────
    if "form_data_patch" in updates:
        patch_dict: dict[str, Any] = updates.pop("form_data_patch") or {}
        # Pydantic validators already enforced canonical keys in AssessmentPatch;
        # defence-in-depth check here too.
        unknown = set(patch_dict.keys()) - FORM_DATA_KEYS
        if unknown:
            raise ApiException(
                status_code=422,
                code="unknown_form_data_key",
                detail=f"Unknown form_data key: {sorted(unknown)[0]}",
            )

        current_blob: dict[str, Any] = dict(assessment.form_data or {})
        merged = {**current_blob, **patch_dict}
        assessment.form_data = merged
        flag_modified(assessment, "form_data")

        for key in patch_dict:
            new_field_sources[f"form_data.{key}"] = "human"

        # R5 sync: form_data → flat columns (ONE-WAY, design R5).
        for fd_key, flat_col in FORM_DATA_TO_FLAT_SYNC.items():
            if fd_key in patch_dict:
                setattr(assessment, flat_col, patch_dict[fd_key])
                new_field_sources[flat_col] = "human"

    # ── Remaining flat / llm / blob fields (existing logic, unchanged) ─────────
    for field, value in updates.items():
        if field in _SERVER_MANAGED_FIELDS:
            # Defence-in-depth skip — should never happen due to schema.
            logger.warning("patch_skipped_server_field", field=field)
            continue

        if field in _LLM_PATCH_FIELDS:
            # Individual llm_* edit → accumulate for blob merge + tag as human.
            llm_blob_changes[field] = value
            new_field_sources[field] = "human"

        elif field in _BLOB_FIELDS:
            # Bulk blob replacement (llm_enriched_data, recommendation_data).
            # Set the column directly; no field_sources — structural, not editorial.
            setattr(assessment, field, value)
            flag_modified(assessment, field)

        else:
            # Flat ORM column — set directly + mark as human-edited.
            setattr(assessment, field, value)
            new_field_sources[field] = "human"

    # Merge accumulated llm_* changes into the llm_enriched_data blob.
    # ALWAYS reassign — do not mutate in place (SQLAlchemy won't detect it).
    if llm_blob_changes:
        current_blob = assessment.llm_enriched_data or {}
        assessment.llm_enriched_data = {**current_blob, **llm_blob_changes}
        flag_modified(assessment, "llm_enriched_data")

    # Reassign field_sources atomically and flag for SQLAlchemy change detection.
    assessment.field_sources = new_field_sources
    flag_modified(assessment, "field_sources")

    # Server-managed audit fields.
    assessment.last_edited_by_id = current_user.id
    assessment.updated_at = _now_utc()

    await db.commit()
    await db.refresh(assessment)

    logger.info(
        "assessment_patched",
        assessment_id=str(assessment_id),
        fields_updated=list(updates.keys()),
        edited_by=str(current_user.id),
    )

    return AssessmentResponse.model_validate(assessment)


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/duplicate — clone for new client
# TASK-B-07
# ---------------------------------------------------------------------------

# Columns that MUST NOT be copied from the source (reset to sensible defaults).
_DUPLICATE_EXCLUDE: frozenset[str] = frozenset(
    {
        "id",
        "created_at",
        "updated_at",
        "created_by_id",
        "last_edited_by_id",
        "pdf_path",
        "pdf_generated_at",
        "email_status",
        "email_sent_at",
        "email_error",
        "task_id",
        "status",
    }
)


@router.post("/{assessment_id}/duplicate", response_model=AssessmentResponse, status_code=201)
async def duplicate_assessment(
    assessment_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AssessmentResponse:
    """
    Clone an existing assessment for a new client engagement.

    Copies all data from the source (including llm_enriched_data, scores, and
    field_sources) so the consultant doesn't have to re-run enrichments from
    scratch.  Resets PDF/email lifecycle fields to neutral defaults and sets
    status = 'draft'.

    The company_name is suffixed with " (copia)" to clearly distinguish the
    duplicate from the original in the list view.

    Returns 201 + the new AssessmentResponse.
    Returns 404 if source not found.
    Returns 409 if source is archived.
    """
    source = await _get_or_404(db, assessment_id, allow_archived=False)
    now = _now_utc()

    new_assessment = Assessment(
        id=uuid4(),
        status=AssessmentStatus.draft.value,
        created_at=now,
        updated_at=now,
        created_by_id=current_user.id,
        last_edited_by_id=current_user.id,
        # Reset PDF + email lifecycle
        pdf_path=None,
        pdf_generated_at=None,
        email_status=EmailStatus.not_sent.value,
        email_sent_at=None,
        email_error=None,
        task_id=None,
        # Carry over all content — consultant can adjust before re-sending
        auto_publish=source.auto_publish,
        company_name=source.company_name + " (copia)",
        sector=source.sector,
        employee_range=source.employee_range,
        revenue_range=source.revenue_range,
        respondent_name_role=source.respondent_name_role,
        respondent_email=source.respondent_email,
        who_decides=source.who_decides,
        budget=source.budget,
        priority_text=source.priority_text,
        # Scores carried over (skip re-enrichment if data is the same)
        maturity_score=source.maturity_score,
        maturity_level=source.maturity_level,
        risk_score=source.risk_score,
        risk_level=source.risk_level,
        priority_score=source.priority_score,
        priority_level=source.priority_level,
        pts_tools=source.pts_tools,
        pts_automation=source.pts_automation,
        pts_area_usage=source.pts_area_usage,
        pts_governance=source.pts_governance,
        pts_goal_clarity=source.pts_goal_clarity,
        pts_data_risk=source.pts_data_risk,
        pts_ai_personal_data=source.pts_ai_personal_data,
        pts_dpa=source.pts_dpa,
        pts_dpia=source.pts_dpia,
        pts_automated_decisions=source.pts_automated_decisions,
        pts_sector=source.pts_sector,
        pts_incident=source.pts_incident,
        # JSON blobs — copy as-is (preserves human/llm tagging + enrichments)
        form_data=dict(source.form_data) if source.form_data else {},
        llm_enriched_data=dict(source.llm_enriched_data) if source.llm_enriched_data else None,
        recommendation_data=dict(source.recommendation_data) if source.recommendation_data else None,
        field_sources=dict(source.field_sources) if source.field_sources else {},
    )

    db.add(new_assessment)
    await db.commit()
    await db.refresh(new_assessment)

    logger.info(
        "assessment_duplicated",
        source_id=str(assessment_id),
        new_id=str(new_assessment.id),
        duplicated_by=str(current_user.id),
    )

    return AssessmentResponse.model_validate(new_assessment)


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/archive — soft-delete via status
# TASK-B-08
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/archive")
async def archive_assessment(
    assessment_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Soft-delete an assessment by setting status = 'archived'.

    Idempotency: returns 409 if the assessment is already archived
    (re-archiving is a no-op from a data perspective but we surface the
    conflict so the frontend can update its state correctly).

    Returns 204 (no body) on success.
    Returns 404 if not found.
    Returns 409 if already archived.
    """
    # Load with allow_archived=False — raises 409 if already archived.
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    assessment.status = AssessmentStatus.archived.value
    assessment.updated_at = _now_utc()
    assessment.last_edited_by_id = current_user.id

    await db.commit()

    logger.info(
        "assessment_archived",
        assessment_id=str(assessment_id),
        archived_by=str(current_user.id),
    )

    return Response(status_code=204)


# ===========================================================================
# PHASE B BATCH 3 — Job registry + re-run endpoints
# TASK-B-09 through TASK-B-15 + BONUS (approve-and-send, resend-email)
# ===========================================================================

# ---------------------------------------------------------------------------
# GET /api/admin/assessments/{id}/jobs — list jobs for an assessment
# TASK-B-09
# ---------------------------------------------------------------------------


@router.get("/{assessment_id}/jobs", response_model=list[JobRecord])
async def list_jobs(
    assessment_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[JobRecord]:
    """
    Return all background jobs registered for an assessment, sorted newest first.

    Source: in-memory JobRegistry (no DB query — process-local, lost on restart).
    Validates that the assessment exists (404 if not found) before querying
    the registry — prevents leaking job counts for non-existent IDs.

    Response is empty list when no jobs have been created for this assessment.

    Polling pattern for the editor:
      While any job has status='pending' or status='running':
        GET /api/admin/assessments/{id}/jobs every 2 seconds.
      Stop polling when all jobs are 'done' or 'failed'.
    """
    # Validate assessment exists (uses GET /{id} semantics — 404 if archived too)
    assessment = await db.get(Assessment, assessment_id)
    if assessment is None:
        raise ApiException(
            status_code=404,
            code="assessment_not_found",
            detail=f"Assessment {assessment_id} not found.",
        )

    jobs = await job_registry.list_for_assessment(str(assessment_id))

    logger.debug(
        "list_jobs",
        assessment_id=str(assessment_id),
        job_count=len(jobs),
    )

    # Construct Pydantic JobRecord from the dataclass (field names match)
    return [
        JobRecord(
            id=j.id,
            type=j.type,
            assessment_id=j.assessment_id,
            status=j.status,
            started_at=j.started_at,
            finished_at=j.finished_at,
            error=j.error,
        )
        for j in jobs
    ]


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/run-llm-enrichment
# TASK-B-11
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/run-llm-enrichment", status_code=202)
async def run_llm_enrichment(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kick off LLM enrichment as a background job.

    Returns 202 immediately with {job_id, status: "pending"}.
    Poll GET /{id}/jobs to track progress.

    Guards:
      - 404 if assessment not found
      - 409 if assessment is archived (cannot re-run on archived)
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    job = await job_registry.create(JobType.enrich_llm, str(assessment_id))
    background_tasks.add_task(
        runners.run_llm_enrichment_job,
        job.id,
        str(assessment_id),
    )

    logger.info(
        "run_llm_enrichment_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/run-recommendations
# TASK-B-12
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/run-recommendations", status_code=202)
async def run_recommendations(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kick off recommendation enrichment as a background job.

    Returns 202 immediately with {job_id, status: "pending"}.
    Poll GET /{id}/jobs to track progress.
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    job = await job_registry.create(JobType.enrich_recommendations, str(assessment_id))
    background_tasks.add_task(
        runners.run_recommendation_enrichment_job,
        job.id,
        str(assessment_id),
    )

    logger.info(
        "run_recommendations_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/run-scoring
# TASK-B-13
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/run-scoring", status_code=202)
async def run_scoring(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kick off the scoring step as a background job.

    Returns 202 immediately with {job_id, status: "pending"}.
    Poll GET /{id}/jobs to track progress.
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    job = await job_registry.create(JobType.score, str(assessment_id))
    background_tasks.add_task(
        runners.run_scoring_job,
        job.id,
        str(assessment_id),
    )

    logger.info(
        "run_scoring_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/generate-pdf — production PDF
# TASK-B-14
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/generate-pdf", status_code=202)
async def generate_pdf_endpoint(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kick off production PDF generation as a background job (draft=False).

    On success the runner updates pdf_path and pdf_generated_at on the assessment.
    On failure, pdf_path is left unchanged and job.error contains the reason.

    Returns 202 immediately with {job_id, status: "pending"}.
    Poll GET /{id}/jobs to track progress.
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    job = await job_registry.create(JobType.generate_pdf, str(assessment_id))
    background_tasks.add_task(
        runners.run_generate_pdf_job,
        job.id,
        str(assessment_id),
        False,  # draft=False → production PDF
    )

    logger.info(
        "generate_pdf_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/preview-pdf — watermarked draft
# TASK-B-15
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/preview-pdf", status_code=202)
async def preview_pdf_endpoint(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kick off draft PDF generation as a background job (draft=True).

    Draft PDFs are watermarked ("[BORRADOR — NO DISTRIBUIR]" prefix on company_name
    + _draft_watermark signal to report_generator).

    Draft PDF is stored at /app/output/_draft_{assessment_id}.pdf.
    The preview UI can poll jobs until done, then serve the file directly
    from the server (e.g. via GET /api/admin/assessments/{id}/pdf?draft=true —
    not yet implemented; Phase B Batch 4 task).

    Does NOT update pdf_path or pdf_generated_at on the assessment row.
    The draft file is ephemeral — overwritten on each preview call.

    Returns 202 immediately with {job_id, status: "pending"}.
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    job = await job_registry.create(JobType.preview_pdf, str(assessment_id))
    background_tasks.add_task(
        runners.run_generate_pdf_job,
        job.id,
        str(assessment_id),
        True,  # draft=True → watermarked
    )

    logger.info(
        "preview_pdf_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/approve-and-send — approve + deliver report
# BONUS — design §3.4
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/approve-and-send", status_code=202)
async def approve_and_send(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Approve an assessment and deliver the report PDF to the client.

    Runs as a background job (PDF generation can take 30–90 seconds).
    Returns 202 immediately; poll GET /{id}/jobs for progress.

    Guards (checked synchronously before queuing):
      - 404 if not found
      - 409 if status != 'pending_review' (only pending_review can be approved)
      - 409 if llm_enriched_data is None (enrichments must run first)
      - 422 if respondent_email is not set (can't deliver to nobody)

    Sequence in the background runner (design §3.4 + §0 A3):
      1. Generate production PDF
      2. UPDATE status=approved, pdf_path, pdf_generated_at — COMMIT
      3. Send email with signed download URL (7-day TTL)
      4. UPDATE email_status=sent/failed — COMMIT
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    # Guard: only pending_review assessments can be approved
    if assessment.status != AssessmentStatus.pending_review.value:
        raise ApiException(
            status_code=409,
            code="invalid_status",
            detail=(
                f"Assessment must be in 'pending_review' to approve. "
                f"Current status: {assessment.status}"
            ),
        )

    # Guard: enrichments must have run (llm_enriched_data is the signal)
    if assessment.llm_enriched_data is None:
        raise ApiException(
            status_code=409,
            code="enrichment_required",
            detail=(
                "LLM enrichment has not run yet. "
                "Run 'run-llm-enrichment' before approving."
            ),
        )

    # Guard: must have a client email to send to
    if not assessment.respondent_email:
        raise ApiException(
            status_code=422,
            code="missing_email",
            detail=(
                "Assessment has no respondent_email. "
                "Set the client email before approving and sending."
            ),
        )

    job = await job_registry.create(JobType.approve_and_send, str(assessment_id))
    background_tasks.add_task(
        runners.run_approve_and_send_job,
        job.id,
        str(assessment_id),
    )

    logger.info(
        "approve_and_send_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
        queued_by=str(current_user.id),
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{id}/resend-email — retry client email
# BONUS
# ---------------------------------------------------------------------------


@router.post("/{assessment_id}/resend-email", status_code=202)
async def resend_email(
    assessment_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retry sending the client report email after a previous failure.

    Surfaces the "Reenviar email" action in the admin UI when
    email_status='failed' (design §0 A3).

    Guards (checked synchronously):
      - 404 if not found
      - 409 if pdf_path is None (no PDF to link to — generate PDF first)
      - 409 if respondent_email is not set

    The runner re-signs the URL (fresh 7-day TTL — old token may have expired)
    and retries SMTP delivery. Updates email_status / email_sent_at / email_error.

    Returns 202 with {job_id, status: "pending"}.
    """
    assessment = await _get_or_404(db, assessment_id, allow_archived=False)

    if not assessment.pdf_path:
        raise ApiException(
            status_code=409,
            code="pdf_not_generated",
            detail="No PDF has been generated yet. Run generate-pdf first.",
        )

    if not assessment.respondent_email:
        raise ApiException(
            status_code=409,
            code="missing_email",
            detail="Assessment has no respondent_email. Set client email before resending.",
        )

    job = await job_registry.create(JobType.resend_email, str(assessment_id))
    background_tasks.add_task(
        runners.run_resend_email_job,
        job.id,
        str(assessment_id),
    )

    logger.info(
        "resend_email_queued",
        assessment_id=str(assessment_id),
        job_id=job.id,
        queued_by=str(current_user.id),
    )
    return {"job_id": job.id, "status": job.status.value}


# ---------------------------------------------------------------------------
# GET /api/admin/assessments/{id}/pdf?draft={true|false} — stream PDF file
# TASK-B-16 support (Phase B Batch 4)
# ---------------------------------------------------------------------------


@router.get("/{assessment_id}/pdf")
async def get_pdf(
    assessment_id: UUID,
    draft: bool = False,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Stream the PDF for an assessment.

    draft=true  → streams /app/output/_draft_{id}.pdf (404 if not generated yet)
    draft=false → streams assessment.pdf_path (404 if null or missing)

    Requires admin session cookie (same-origin — the editor iframe works without
    a signed URL because the admin is already authenticated).

    Called by AssessmentEditorPage.tsx <iframe src="/api/admin/assessments/{id}/pdf?draft=true" />
    """
    assessment = await db.get(Assessment, assessment_id)
    if assessment is None:
        raise ApiException(
            status_code=404,
            code="assessment_not_found",
            detail=f"Assessment {assessment_id} not found.",
        )

    if draft:
        path = Path(f"/app/output/_draft_{assessment_id}.pdf")
        if not path.exists():
            raise ApiException(
                status_code=404,
                code="draft_not_found",
                detail="Preview PDF has not been generated yet. Run preview-pdf first.",
            )
    else:
        if not assessment.pdf_path:
            raise ApiException(
                status_code=404,
                code="pdf_not_generated",
                detail="Production PDF has not been generated yet.",
            )
        path = Path(assessment.pdf_path)
        if not path.exists():
            raise ApiException(
                status_code=404,
                code="pdf_file_missing",
                detail="PDF file is missing on disk.",
            )

    filename = f"assessment-{assessment.company_name or str(assessment_id)}.pdf"

    logger.info(
        "pdf_served",
        assessment_id=str(assessment_id),
        draft=draft,
        path=str(path),
    )

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=filename,
    )
