"""
app/auth/sessions — Server-side admin session management.

Session design (design §2.1):
  - Cookie name: admin_sid
  - Cookie value = session.id = uuid4().hex (32 hex chars, opaque)
  - TTL: absolute 30 days (SESSION_TTL_DAYS config), hard cap — never extended
  - last_seen_at: updated on every authenticated request (sliding visibility)
  - revoked_at: set on logout or password reset; NULL = active

Background job note:
  These functions accept a db (AsyncSession) parameter. Callers from HTTP
  request handlers use the session from get_db(). Background runners must
  pass a session from async_session_factory() directly — do NOT use get_db()
  in background context (session is closed after response is sent).
"""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_row import SessionRow

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


def _now_utc() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


async def create_session(
    db: AsyncSession,
    user_id: UUID,
    ttl_days: int = 30,
) -> SessionRow:
    """
    Create a new admin session and persist it.

    The session id is uuid4().hex — a 32-char hex string used directly as the
    cookie value. No signing is needed because the value is looked up server-side.

    Args:
        db:       Active AsyncSession (from get_db() or async_session_factory).
        user_id:  The user this session belongs to.
        ttl_days: Absolute lifetime in days (default: settings.session_ttl_days=30).

    Returns:
        The persisted SessionRow with all fields populated.
    """
    now = _now_utc()
    session = SessionRow(
        id=uuid4().hex,
        user_id=user_id,
        created_at=now,
        expires_at=now + timedelta(days=ttl_days),
        last_seen_at=now,
        revoked_at=None,
    )
    db.add(session)
    await db.flush()  # Persist without committing — let caller commit.
    logger.info("session_created", session_id=session.id[:8], user_id=str(user_id))
    return session


async def revoke_session(db: AsyncSession, session_id: str) -> None:
    """
    Revoke a single session (e.g. on logout).

    Sets revoked_at = NOW(). Subsequent get_active_session() calls will return None.
    No-op if the session doesn't exist or is already revoked.

    Args:
        db:         Active AsyncSession.
        session_id: The session cookie value (uuid4().hex string).
    """
    now = _now_utc()
    await db.execute(
        update(SessionRow)
        .where(SessionRow.id == session_id, SessionRow.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    logger.info("session_revoked", session_id=session_id[:8])


async def revoke_all_user_sessions(db: AsyncSession, user_id: UUID) -> None:
    """
    Revoke ALL active sessions for a user.

    Called on password reset to force re-authentication from all devices.
    Sessions that are already revoked or expired are left untouched (WHERE clause
    filters to revoked_at IS NULL).

    Args:
        db:      Active AsyncSession.
        user_id: The user whose sessions to revoke.
    """
    now = _now_utc()
    result = await db.execute(
        update(SessionRow)
        .where(
            SessionRow.user_id == user_id,
            SessionRow.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    count = result.rowcount
    logger.info(
        "sessions_revoked_all", user_id=str(user_id), count=count
    )


async def get_active_session(
    db: AsyncSession, session_id: str
) -> SessionRow | None:
    """
    Look up a session and return it if valid (not revoked, not expired).

    This is the hot path — called on EVERY authenticated request via require_admin.

    Validity criteria:
      - revoked_at IS NULL
      - expires_at > NOW()

    Note: last_seen_at is NOT updated here. Call update_last_seen() separately
    after the handler completes to avoid blocking the auth check on the update.
    The middleware in auth/middleware.py calls both.

    Args:
        db:         Active AsyncSession.
        session_id: The value from the admin_sid cookie.

    Returns:
        The SessionRow if active, None if not found/revoked/expired.
    """
    now = _now_utc()
    result = await db.execute(
        select(SessionRow).where(
            SessionRow.id == session_id,
            SessionRow.revoked_at.is_(None),
            SessionRow.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def update_last_seen(db: AsyncSession, session_id: str) -> None:
    """
    Update last_seen_at to NOW() for the given session.

    Called after each authenticated request completes. Does NOT extend expires_at —
    the 30-day cap is absolute (design §2.1: "sliding visibility but no extension").

    Args:
        db:         Active AsyncSession.
        session_id: The session cookie value.
    """
    await db.execute(
        update(SessionRow)
        .where(SessionRow.id == session_id)
        .values(last_seen_at=_now_utc())
    )


async def prune_expired(db: AsyncSession) -> int:
    """
    Delete all sessions that have expired (expires_at < NOW()).

    Includes already-revoked sessions — once expired, they serve no purpose.
    Returns the count of deleted rows for observability.

    Called in Phase D's startup sweep. Can also be triggered manually.

    Args:
        db: Active AsyncSession.

    Returns:
        Number of session rows deleted.
    """
    from sqlalchemy import delete

    now = _now_utc()
    result = await db.execute(
        delete(SessionRow).where(SessionRow.expires_at < now)
    )
    count = result.rowcount
    if count > 0:
        logger.info("sessions_pruned", count=count)
    return count
