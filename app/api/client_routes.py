"""
app/api/client_routes — Batch 8: Public client-facing endpoints for session 2.

All endpoints use signed URL tokens — NO session auth, NO OTP.

Token types:
  deep_form:   {lead_id, branch_ids, purpose="deep_form"}  — TTL 90 days
  report_view: {lead_id, purpose="report_view"}             — TTL 90 days

Endpoints:
  GET  /api/client/deep/{token}          — fetch DEEP branches + questions
  POST /api/client/deep/{token}/submit   — submit responses for one branch
  GET  /api/client/report/{token}        — check report status
  GET  /api/client/report/{token}/download — download report (if ready)
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.email.sender import send_email
from app.email.templates import deep_form_received_thanks_email
from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.signed_urls import SignedUrlError, verify_payload

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["client-session2"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _token_401() -> HTTPException:
    return HTTPException(status_code=401, detail="Token inválido, expirado o malformado.")


def _resolve_deep_token(token: str) -> tuple[str, list[str]]:
    """Verify and unpack a deep_form token → (lead_id, branch_ids)."""
    try:
        payload = verify_payload(token)
    except SignedUrlError:
        raise _token_401()
    if payload.get("purpose") != "deep_form":
        raise _token_401()
    return payload["lead_id"], payload.get("branch_ids", [])


def _resolve_report_token(token: str) -> str:
    """Verify and unpack a report_view token → lead_id."""
    try:
        payload = verify_payload(token)
    except SignedUrlError:
        raise _token_401()
    if payload.get("purpose") != "report_view":
        raise _token_401()
    return payload["lead_id"]


# ---------------------------------------------------------------------------
# GET /api/client/deep/{token}
# ---------------------------------------------------------------------------


@router.get("/client/deep/{token}")
async def get_client_deep_branches(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return DEEP branches + questions for the client to fill in.

    Token must be a valid deep_form signed URL. Branches returned are those
    whose IDs are listed in the token payload (status=sent_to_client or similar).
    """
    lead_id, branch_ids = _resolve_deep_token(token)

    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead is None:
        raise _token_401()

    # Fetch branches — if branch_ids in token, filter by them; else all for lead
    if branch_ids:
        branch_result = await db.execute(
            select(DeepBranch).where(DeepBranch.id.in_(branch_ids))
        )
    else:
        # Fall back: get all branches for this lead's sessions
        session_result = await db.execute(
            select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        )
        sessions = session_result.scalars().all()
        session_ids = [s.id for s in sessions]
        branch_result = await db.execute(
            select(DeepBranch).where(DeepBranch.intake_session_id.in_(session_ids))
        )

    branches = branch_result.scalars().all()

    logger.info(
        "client_deep_get",
        lead_id=lead_id,
        branch_count=len(branches),
    )

    return {
        "lead_id": lead_id,
        "status": "pending" if any(b.status != "received" for b in branches) else "completed",
        "deep_branches": [
            {
                "id": b.id,
                "branch_id": b.branch_id,
                "generated_questions": b.generated_questions,
                "status": b.status,
            }
            for b in branches
        ],
    }


# ---------------------------------------------------------------------------
# POST /api/client/deep/{token}/submit
# ---------------------------------------------------------------------------


class DeepSubmitPayload(BaseModel):
    branch_id: str
    responses: dict


@router.post("/client/deep/{token}/submit")
async def submit_client_deep_branch(
    token: str,
    body: DeepSubmitPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Persist client responses for a single DEEP branch.

    When all branches for the session are received, transitions
    IntakeSession.state → deep_received and sends confirmation email.
    """
    lead_id, branch_ids = _resolve_deep_token(token)

    # Verify lead exists
    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead is None:
        raise _token_401()

    # Find the specific branch to update
    branch_result = await db.execute(
        select(DeepBranch).where(DeepBranch.id == body.branch_id)
    )
    branch = branch_result.scalar_one_or_none()
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch no encontrado.")

    # Persist responses
    branch.client_responses = body.responses
    branch.status = "received"
    branch.received_at = datetime.now(tz=timezone.utc)
    db.add(branch)

    # Check if all branches for the session are received
    session_result = await db.execute(
        select(IntakeSession).where(IntakeSession.id == branch.intake_session_id)
    )
    session = session_result.scalar_one()

    all_branches_result = await db.execute(
        select(DeepBranch).where(
            DeepBranch.intake_session_id == branch.intake_session_id
        )
    )
    all_branches = all_branches_result.scalars().all()

    # A branch is "received" if its status == "received" AFTER the current update
    # (the current branch is in-memory updated, others from DB)
    all_received = all(
        b.status == "received" if b.id != branch.id else True
        for b in all_branches
    )

    if all_received and session.state != "deep_received":
        session.state = "deep_received"
        db.add(session)
        logger.info(
            "deep_received_all_branches",
            lead_id=lead_id,
            session_id=session.id,
        )

    await db.commit()

    # Confirmation email (BackgroundTask — fire and forget)
    subject, body_text = deep_form_received_thanks_email(lead.full_name, lead.company_name)
    background_tasks.add_task(send_email, lead.email, subject, body_text)

    return {
        "received": True,
        "branch_id": branch.id,
        "status": branch.status,
        "session_state": session.state,
    }


# ---------------------------------------------------------------------------
# GET /api/client/report/{token}
# ---------------------------------------------------------------------------


@router.get("/client/report/{token}")
async def get_client_report_status(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Check whether the session 2 report is ready for this client.

    Returns 202 + status=pending when report is not yet generated.
    Returns 200 + status=ready + content when report exists.
    """
    lead_id = _resolve_report_token(token)

    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead is None:
        raise _token_401()

    # Find the most recent intake session for this lead
    session_result = await db.execute(
        select(IntakeSession)
        .where(IntakeSession.lead_id == lead_id)
        .order_by(IntakeSession.created_at.desc())
    )
    session = session_result.scalar_one_or_none()
    if session is None or session.report_content is None:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=202, content={"status": "pending"})

    return {
        "status": "ready",
        "content": session.report_content,
        "lead_id": lead_id,
    }


# ---------------------------------------------------------------------------
# GET /api/client/report/{token}/download
# ---------------------------------------------------------------------------


@router.get("/client/report/{token}/download")
async def download_client_report(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Download the session 2 report for the client (PDF or HTML).

    Returns 202 + status=pending when report is not yet generated.
    Returns 200 + content when report is ready.
    """
    lead_id = _resolve_report_token(token)

    lead_result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if lead is None:
        raise _token_401()

    session_result = await db.execute(
        select(IntakeSession)
        .where(IntakeSession.lead_id == lead_id)
        .order_by(IntakeSession.created_at.desc())
    )
    session = session_result.scalar_one_or_none()
    if session is None or session.report_content is None:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=202, content={"status": "pending"})

    # In MVP: return report content as text (PDF generation out of scope for B8)
    return {
        "status": "ready",
        "content": session.report_content,
        "lead_id": lead_id,
    }
