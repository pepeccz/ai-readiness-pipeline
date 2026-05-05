"""
app/api/_intake_helpers — Shared helpers for intake session management.

Extracted to avoid circular imports between leads_routes and intake_routes.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.block_draft import BlockDraft
from app.models.intake_session import IntakeSession


async def get_or_create_session(db: AsyncSession, lead_id: str) -> IntakeSession:
    """
    Return existing IntakeSession for lead_id or create a new not_started one.

    Race-safety: wraps the INSERT in a SAVEPOINT so that a concurrent INSERT
    (concurrent accept for the same lead) raises IntegrityError on the unique
    constraint, is caught here, and the existing row is re-selected.

    This guarantees exactly-once semantics for IntakeSession per lead.
    """
    # Fast path: row already exists.
    stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is not None:
        return session

    # Slow path: try to create; handle concurrent-create race via IntegrityError.
    # Use a SAVEPOINT (begin_nested) so the outer transaction is not poisoned.
    try:
        async with db.begin_nested():
            session = IntakeSession(
                lead_id=lead_id,
                primary_area="not_set",
                secondary_area=None,
                areas_involved=[],
                state="not_started",
                blocks_completed=[],
            )
            db.add(session)
            # flush inside the savepoint to trigger the unique-constraint check.
            await db.flush()
    except IntegrityError:
        # Savepoint was rolled back automatically by the context manager.
        # Re-select the existing row inserted by the concurrent request.
        result = await db.execute(stmt)
        session = result.scalar_one()

    return session


# ---------------------------------------------------------------------------
# BlockDraft repository helpers (TB.4)
# ---------------------------------------------------------------------------


async def upsert_draft(
    db: AsyncSession, lead_id: str, block_id: str, payload: dict
) -> BlockDraft:
    """
    Insert or update a BlockDraft for (lead_id, block_id).

    Always refreshes updated_at on write.
    """
    from datetime import datetime, timezone  # noqa: PLC0415

    stmt = select(BlockDraft).where(
        BlockDraft.lead_id == lead_id,
        BlockDraft.block_id == block_id,
    )
    result = await db.execute(stmt)
    draft = result.scalar_one_or_none()

    now = datetime.now(tz=timezone.utc)
    if draft is None:
        draft = BlockDraft(lead_id=lead_id, block_id=block_id, payload=payload, updated_at=now)
        db.add(draft)
    else:
        draft.payload = payload
        draft.updated_at = now

    await db.flush()
    return draft


async def get_draft(
    db: AsyncSession, lead_id: str, block_id: str
) -> BlockDraft | None:
    """Return BlockDraft for (lead_id, block_id) or None if not found."""
    stmt = select(BlockDraft).where(
        BlockDraft.lead_id == lead_id,
        BlockDraft.block_id == block_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_draft(db: AsyncSession, lead_id: str, block_id: str) -> None:
    """Delete BlockDraft for (lead_id, block_id) if it exists. No-op if absent."""
    from sqlalchemy import delete as sa_delete  # noqa: PLC0415

    stmt = sa_delete(BlockDraft).where(
        BlockDraft.lead_id == lead_id,
        BlockDraft.block_id == block_id,
    )
    await db.execute(stmt)
