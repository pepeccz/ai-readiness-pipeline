"""
app/api/client_routes — Batch 8: Public client-facing endpoints for session 2.

All endpoints use signed URL tokens — NO session auth, NO OTP.

Token types:
  report_view: {lead_id, purpose="report_view"}  — TTL 90 days

Endpoints:
  GET  /api/client/deep/{token}          — RETIRED (HTTP 410 Gone)
  POST /api/client/deep/{token}/submit   — RETIRED (HTTP 410 Gone)
  GET  /api/client/report/{token}        — check report status
  GET  /api/client/report/{token}/download — download report (if ready)

PR5b: The async deep form flow has been retired. Session 2 is now synchronous.
The deep/* routes are kept registered (returning 410) so in-flight client
URLs do not produce 404 errors. They will be removed in a future cleanup PR.
"""

from __future__ import annotations

import json

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.signed_urls import SignedUrlError, verify_payload
from sqlalchemy import select

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["client-session2"])

_DEEP_GONE_DETAIL = json.dumps(
    {"detail": "Gone — async deep flow has been retired. Sesión 2 is now synchronous."}
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_report_token(token: str) -> str:
    """Verify and unpack a report_view token → lead_id."""
    try:
        payload = verify_payload(token)
    except SignedUrlError:
        raise _token_401()
    if payload.get("purpose") != "report_view":
        raise _token_401()
    return payload["lead_id"]


def _token_401():
    from fastapi import HTTPException
    return HTTPException(status_code=401, detail="Token inválido, expirado o malformado.")


# ---------------------------------------------------------------------------
# GET /api/client/deep/{token} — RETIRED (PR5b)
# ---------------------------------------------------------------------------


@router.get("/client/deep/{token}")
async def get_client_deep_branches(token: str):
    """
    RETIRED: async deep form flow has been retired.

    This route is kept registered so in-flight signed URLs receive a
    meaningful 410 Gone instead of 404 Not Found.
    PR5b: returns HTTP 410.
    """
    return Response(status_code=410, content=_DEEP_GONE_DETAIL, media_type="application/json")


# ---------------------------------------------------------------------------
# POST /api/client/deep/{token}/submit — RETIRED (PR5b)
# ---------------------------------------------------------------------------


@router.post("/client/deep/{token}/submit")
async def submit_client_deep_branch(token: str):
    """
    RETIRED: async deep form flow has been retired.

    This route is kept registered so in-flight signed URLs receive a
    meaningful 410 Gone instead of 404 Not Found.
    PR5b: returns HTTP 410.
    """
    return Response(status_code=410, content=_DEEP_GONE_DETAIL, media_type="application/json")


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
