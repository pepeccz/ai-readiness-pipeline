"""
app/api/admin/leads_routes — Admin lead management endpoints.

Router prefix: /api/admin/leads  (registered in webhook_service.py)

Endpoints:
  GET   /api/admin/leads          — paginated + filtered list  (T4.1)
  GET   /api/admin/leads/{id}     — full detail + consents     (T4.2)
  PATCH /api/admin/leads/{id}     — action: accept|reject|request_extra_info|assign_consultant  (T4.3-T4.6)

All endpoints require admin session cookie (Depends(require_admin)).

Filter params for GET /api/admin/leads:
  bucket, status, sector, from_date, to_date, search, page, page_size

PATCH body (LeadActionRequest):
  action         — accept | reject | request_extra_info | assign_consultant
  reason         — required for reject (predefined reasons)
  consultant_id  — required for accept and assign_consultant

Status transition rules (409 on violation):
  - accept: only from pending_review
  - reject: only from pending_review
  - request_extra_info: only from pending_review (status unchanged)
  - assign_consultant: any status (assignment without status change)
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.middleware import require_admin
from app.db.session import get_db
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.user import User
from app.schemas.admin_leads import (
    LeadActionRequest,
    LeadActionResponse,
    LeadDetailDTO,
    LeadListResponse,
    LeadSummaryDTO,
    SideEffect,
)
from app.schemas.common import ApiException
from app.services.leads.lead_service import (
    send_lead_accepted_email,
    send_lead_extra_info_email,
    send_lead_rejected_email,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/leads", tags=["admin-leads"])


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


async def _get_lead_or_404(db: AsyncSession, lead_id: str) -> Lead:
    """Load Lead with consents eagerly. Raises 404 if not found."""
    stmt = (
        select(Lead)
        .where(Lead.id == lead_id)
        .options(selectinload(Lead.consents))
    )
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if lead is None:
        raise ApiException(
            status_code=404,
            code="lead_not_found",
            detail=f"Lead {lead_id} not found.",
        )
    return lead


# ---------------------------------------------------------------------------
# GET /api/admin/leads — paginated list with filters
# T4.1
# ---------------------------------------------------------------------------


@router.get("", response_model=LeadListResponse)
async def list_leads(
    # Filters
    bucket: str | None = None,
    status: str | None = None,
    sector: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    search: str | None = None,
    # Pagination
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    # Auth + DB
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> LeadListResponse:
    """
    Return paginated, filtered list of leads.

    Filters:
      bucket    — triage_bucket value (auto_accept|review|cold_warm|cold_cool|reject_soft)
      status    — lead status (pending_review|accepted|rejected|converted)
      sector    — sector string (case-sensitive)
      from_date — ISO date string (YYYY-MM-DD), inclusive
      to_date   — ISO date string (YYYY-MM-DD), inclusive
      search    — case-insensitive match on email OR company_name

    Pagination: 1-indexed. Returns total + pages count.
    """
    conditions: list = []

    if bucket:
        conditions.append(Lead.triage_bucket == bucket)
    if status:
        conditions.append(Lead.status == status)
    if sector:
        conditions.append(Lead.sector == sector)
    if from_date:
        try:
            dt_from = datetime.fromisoformat(from_date).replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
            conditions.append(Lead.created_at >= dt_from)
        except ValueError:
            raise ApiException(
                status_code=422,
                code="invalid_from_date",
                detail="from_date must be a valid ISO date (YYYY-MM-DD).",
            )
    if to_date:
        try:
            dt_to = datetime.fromisoformat(to_date).replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
            conditions.append(Lead.created_at <= dt_to)
        except ValueError:
            raise ApiException(
                status_code=422,
                code="invalid_to_date",
                detail="to_date must be a valid ISO date (YYYY-MM-DD).",
            )
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(
                Lead.email.ilike(pattern),
                Lead.company_name.ilike(pattern),
            )
        )

    # Count
    count_stmt = select(func.count(Lead.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total_result = await db.execute(count_stmt)
    total: int = total_result.scalar_one()

    # Data
    offset = (page - 1) * page_size
    data_stmt = select(Lead).order_by(Lead.created_at.desc()).offset(offset).limit(page_size)
    if conditions:
        data_stmt = data_stmt.where(*conditions)
    rows_result = await db.execute(data_stmt)
    rows = rows_result.scalars().all()

    items = [LeadSummaryDTO.model_validate(row) for row in rows]
    pages = ceil(total / page_size) if page_size > 0 else 0

    logger.debug(
        "list_leads",
        total=total,
        page=page,
        page_size=page_size,
        filters={"bucket": bucket, "status": status, "sector": sector, "search": search},
    )

    return LeadListResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


# ---------------------------------------------------------------------------
# GET /api/admin/leads/{id} — full detail
# T4.2
# ---------------------------------------------------------------------------


@router.get("/{lead_id}", response_model=LeadDetailDTO)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> LeadDetailDTO:
    """Return full lead detail including consents audit trail."""
    lead = await _get_lead_or_404(db, lead_id)
    logger.debug("get_lead", lead_id=lead_id)
    return LeadDetailDTO.model_validate(lead)


# ---------------------------------------------------------------------------
# PATCH /api/admin/leads/{id} — action dispatch
# T4.3-T4.6
# ---------------------------------------------------------------------------


@router.patch("/{lead_id}", response_model=LeadActionResponse)
async def patch_lead(
    lead_id: str,
    body: LeadActionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> LeadActionResponse:
    """
    Dispatch a lead management action.

    Actions:
      accept             — lead.status → accepted; requires consultant_id
      reject             — lead.status → rejected; requires reason
      request_extra_info — sends email to lead; status unchanged
      assign_consultant  — sets assigned_consultant_id; status unchanged

    Status transition guard:
      accept and reject only allowed from status=pending_review → 409 otherwise.
    """
    lead = await _get_lead_or_404(db, lead_id)
    side_effects: list[SideEffect] = []

    # ── action=accept ─────────────────────────────────────────────────────────
    if body.action == "accept":
        if lead.status != "pending_review":
            raise ApiException(
                status_code=409,
                code="invalid_status_transition",
                detail=f"Cannot accept a lead with status={lead.status}",
            )
        lead.status = "accepted"
        lead.accepted_at = _now_utc()
        # assigned_consultant_id FK to users.id (UUID CHAR(32) column) — must store UUID
        lead.assigned_consultant_id = UUID(body.consultant_id) if body.consultant_id else None  # type: ignore[assignment]

        # Create IntakeSession for the accepted lead
        intake_session = IntakeSession(
            lead_id=lead.id,
            primary_area="not_set",
            secondary_area=None,
            areas_involved=[],
            state="not_started",
            blocks_completed=[],
        )
        db.add(intake_session)

        background_tasks.add_task(send_lead_accepted_email, lead)
        side_effects.append(
            SideEffect(type="email_sent", description="Acceptance email queued for delivery")
        )
        side_effects.append(
            SideEffect(type="intake_session_created", description="IntakeSession created for consultant workflow")
        )
        logger.info("lead_accepted", lead_id=lead_id, consultant_id=body.consultant_id)

    # ── action=reject ─────────────────────────────────────────────────────────
    elif body.action == "reject":
        if lead.status != "pending_review":
            raise ApiException(
                status_code=409,
                code="invalid_status_transition",
                detail=f"Cannot reject a lead with status={lead.status}",
            )
        lead.status = "rejected"
        lead.rejected_reason = body.reason

        background_tasks.add_task(send_lead_rejected_email, lead)
        side_effects.append(
            SideEffect(type="email_sent", description="Rejection email queued for delivery")
        )
        logger.info("lead_rejected", lead_id=lead_id, reason=body.reason)

    # ── action=request_extra_info ──────────────────────────────────────────────
    elif body.action == "request_extra_info":
        if lead.status != "pending_review":
            raise ApiException(
                status_code=409,
                code="invalid_status_transition",
                detail=f"Cannot request extra info for lead with status={lead.status}",
            )
        background_tasks.add_task(send_lead_extra_info_email, lead)
        side_effects.append(
            SideEffect(type="email_sent", description="Extra info request email queued")
        )
        logger.info("lead_extra_info_requested", lead_id=lead_id)

    # ── action=assign_consultant ───────────────────────────────────────────────
    elif body.action == "assign_consultant":
        lead.assigned_consultant_id = UUID(body.consultant_id) if body.consultant_id else None  # type: ignore[assignment]
        side_effects.append(
            SideEffect(type="consultant_assigned", description=f"Consultant {body.consultant_id} assigned")
        )
        logger.info("lead_consultant_assigned", lead_id=lead_id, consultant_id=body.consultant_id)

    await db.commit()
    # Reload with eagerly loaded consents — SQLAlchemy async requires explicit eager load.
    lead = await _get_lead_or_404(db, lead_id)

    return LeadActionResponse(
        lead=LeadDetailDTO.model_validate(lead),
        side_effects=side_effects,
    )
