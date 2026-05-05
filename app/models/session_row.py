"""
app/models/session_row — Admin session model.

Named `SessionRow` (not `Session`) to avoid collision with SQLAlchemy's own
`Session` class which appears in imports like `from sqlalchemy.orm import Session`.

Cookie design (per design §2.1):
  - Cookie name: admin_sid
  - Cookie value = session id = uuid4().hex (32 hex chars, opaque, no signing needed)
  - TTL: absolute 30 days (expires_at = created_at + 30d); hard cap on re-login
  - last_seen_at: updated on every request that passes auth (sliding visibility)
    but expires_at is NOT extended — 30-day cap forces a re-login
  - revoked_at: set on explicit logout or password reset (revoke_all_for_user)

Indexes:
  idx_sessions_user_id   — for listing/revoking all sessions of a user
  idx_sessions_expires_at (partial, WHERE revoked_at IS NULL) — for the validity
    check that runs on every authenticated request; partial index keeps it lean
    by excluding already-revoked sessions from the index.

Foreign key:
  user_id → users.id CASCADE DELETE — when a user is deleted, all their sessions
  go with them automatically at the DB level.
"""

from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

logger = structlog.get_logger(__name__)


class SessionRow(Base):
    __tablename__ = "sessions"

    # The session id IS the cookie value — uuid4().hex, 32 hex chars.
    # Stored as Text (not UUID) to avoid any driver coercion; the value is
    # always generated as `uuid4().hex` in app/auth/sessions.py.
    id: Mapped[str] = mapped_column(Text, primary_key=True)

    # FK to users.id — CASCADE DELETE so orphan sessions are impossible.
    # Index defined in __table_args__ via the migration (idx_sessions_user_id).
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Absolute expiry — set once at creation (created_at + SESSION_TTL_DAYS).
    # Never extended on activity — 30-day hard cap forces periodic re-login.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Updated on every authenticated request — provides "last active" visibility
    # in any future session management UI without extending the TTL.
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # NULL = active; set to NOW() on logout or password reset (revoke_all_for_user).
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # Fast lookup for revoking all sessions of a user (logout, password reset).
        Index("idx_sessions_user_id", "user_id"),
        # Partial index: only non-revoked sessions need fast lookup by expiry.
        # Keeps the index lean as the revoked rows accumulate over time.
        Index(
            "idx_sessions_expires_at",
            "expires_at",
            sqlite_where=(revoked_at.is_(None)),  # type: ignore[attr-defined]
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SessionRow id={self.id[:8]}... user_id={self.user_id} "
            f"expires_at={self.expires_at} revoked={self.revoked_at is not None}>"
        )
