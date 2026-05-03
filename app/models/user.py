"""
app/models/user — Admin User model.

Columns:
  id                        — UUID primary key
  email                     — unique, indexed, used as login identifier
  password_hash             — Argon2id hash produced by app/auth/password.py
  display_name              — human-readable name shown in the UI
  is_active                 — soft-disable without deleting (revokes sessions on next request)
  last_login_at             — updated on every successful login
  password_reset_token_hash — SHA256 of the raw reset token (never store raw token)
  password_reset_expires_at — 1-hour TTL for the reset link; NULL when no pending reset
  created_at                — UTC timestamp, set once at INSERT

Relationships:
  SessionRow.user_id  → FK to User.id (CASCADE DELETE)
  Assessment.created_by_id / last_edited_by_id → FK to User.id (SET NULL on delete)
"""

from datetime import datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

logger = structlog.get_logger(__name__)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # Account state
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset — SHA256 of the raw token; NULL when no pending reset.
    # Raw token is sent by email and NEVER stored (entropy of token_urlsafe(32) makes
    # SHA256 sufficient — Argon2id would be overkill here).
    password_reset_token_hash: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} active={self.is_active}>"
