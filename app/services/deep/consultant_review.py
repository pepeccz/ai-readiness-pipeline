"""
app/services/deep/consultant_review — Manages consultant review of DEEP branches.

Handles:
- Listing DeepBranch rows for a session
- Editing generated questions (PATCH)
- Sending to client: generates signed URL, dispatches email

Status transitions:
  pending_review → (consultant edits) → pending_review (no status change on edit)
  pending_review → approved (on send)
  approved → sent_to_client (after email dispatched)
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.lead import Lead

logger = structlog.get_logger(__name__)


async def list_branches(db: AsyncSession, intake_session_id: str) -> list[DeepBranch]:
    """Return all DeepBranch rows for a session, ordered by branch_id."""
    stmt = (
        select(DeepBranch)
        .where(DeepBranch.intake_session_id == intake_session_id)
        .order_by(DeepBranch.branch_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_branch_questions(
    db: AsyncSession,
    deep_branch_id: str,
    questions: list[dict],
) -> DeepBranch:
    """
    Update generated_questions on a DeepBranch (consultant edit).

    Args:
        db: Async session.
        deep_branch_id: UUID of the DeepBranch.
        questions: New questions list (consultant's edited version).

    Returns:
        Updated DeepBranch.

    Raises:
        ValueError: If branch not found.
    """
    stmt = select(DeepBranch).where(DeepBranch.id == deep_branch_id)
    result = await db.execute(stmt)
    branch = result.scalar_one_or_none()

    if branch is None:
        raise ValueError(f"DeepBranch {deep_branch_id} not found")

    # Store original questions as consultant_edits if this is the first edit
    if branch.consultant_edits is None:
        branch.consultant_edits = branch.generated_questions

    branch.generated_questions = questions
    branch.consultant_reviewed_at = datetime.now(tz=timezone.utc)
    await db.commit()

    logger.info(
        "deep_branch_questions_updated",
        branch_id=deep_branch_id,
        question_count=len(questions),
    )
    return branch


async def send_branch_to_client(
    db: AsyncSession,
    lead_id: str,
    deep_branch_id: str,
) -> dict:
    """
    Approve a DeepBranch and send signed URL to client via email.

    Steps:
    1. Load branch + session + lead
    2. Generate signed URL token (TTL from settings)
    3. Persist token + sent_to_client_at + status=sent_to_client
    4. Dispatch email to lead

    Returns:
        dict with signed_url, sent_to (email), expires_at
    """
    from app.email.sender import send_email
    from app.signed_urls import sign_payload
    from config import settings

    stmt = select(DeepBranch).where(DeepBranch.id == deep_branch_id)
    result = await db.execute(stmt)
    branch = result.scalar_one_or_none()
    if branch is None:
        raise ValueError(f"DeepBranch {deep_branch_id} not found")

    # Load lead email
    session_stmt = select(IntakeSession).where(
        IntakeSession.id == branch.intake_session_id
    )
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"IntakeSession for branch {deep_branch_id} not found")

    lead_stmt = select(Lead).where(Lead.id == lead_id)
    lead_result = await db.execute(lead_stmt)
    lead = lead_result.scalar_one_or_none()
    if lead is None:
        raise ValueError(f"Lead {lead_id} not found")

    # Generate signed URL
    ttl_days = getattr(settings, "deep_session_ttl_days", 90)
    ttl_seconds = ttl_days * 86400
    token = sign_payload(
        {
            "lead_id": lead_id,
            "branch_ids": [branch.id],
            "purpose": "deep_form",
        },
        ttl_seconds=ttl_seconds,
    )

    from datetime import timedelta
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=ttl_seconds)

    # Persist
    branch.signed_token = token
    branch.status = "sent_to_client"
    branch.sent_to_client_at = datetime.now(tz=timezone.utc)
    branch.consultant_reviewed_at = branch.consultant_reviewed_at or datetime.now(tz=timezone.utc)
    await db.commit()

    # Build signed URL (frontend base URL + token)
    base_url = getattr(settings, "frontend_base_url", "https://air.zanovix.com")
    signed_url = f"{base_url}/deep/{token}"

    # Send email
    subject = "Tu cuestionario de profundización IA está listo"
    body = (
        f"Hola {lead.full_name},\n\n"
        f"Tu consultor ha preparado un cuestionario personalizado para continuar el diagnóstico de madurez IA.\n\n"
        f"Accedé aquí: {signed_url}\n\n"
        f"Este enlace es válido por {ttl_days} días.\n\n"
        f"Saludos,\nEquipo de Consultoría IA"
    )

    try:
        await send_email(to=lead.email, subject=subject, body=body)
        logger.info("deep_branch_sent_to_client", branch_id=deep_branch_id, lead_email=lead.email)
    except Exception as exc:
        logger.error("deep_branch_email_failed", branch_id=deep_branch_id, error=str(exc))
        # Don't roll back — branch is already marked as sent

    return {
        "signed_url": signed_url,
        "sent_to": lead.email,
        "expires_at": expires_at.isoformat(),
    }
