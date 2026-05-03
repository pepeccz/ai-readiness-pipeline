"""
app/models/login_attempt — Rate-limiting log for authentication attempts.

This table serves double duty as per the addendum (TASK-A-16, TASK-C-09):
  - Login attempts:          email=<email>, ip=<ip>, attempt_type='login'
  - Password reset attempts: email=<email>, ip=<ip>, attempt_type='reset'
  - Public form submissions: email=NULL,    ip=<ip>, attempt_type='public_submission'

The `email` column is intentionally NULLABLE to support IP-only scopes
(attempt_type='public_submission') where no user identity is known.

Inline pruning strategy (design §0 A5):
  On every record_attempt() call, app/auth/rate_limit.py runs a DELETE that
  clears rows older than 1 hour for the same (email, ip, attempt_type) tuple.
  This bounds table growth per combination without requiring a sweep job.
  Phase D adds an unscoped sweep for global hygiene.

Index:
  idx_login_attempts_lookup on (email, ip, attempt_type, attempted_at) —
  covers both the COUNT query (check_rate_limit) and the DELETE (inline prune).
  Composite order follows cardinality: email + ip narrows drastically, then type,
  then time for the range scan.

Note: id uses Integer autoincrement (not UUID) — these rows are ephemeral and
high-volume; integer PKs are cheaper to insert and index.
"""

from datetime import datetime

import structlog
from sqlalchemy import Boolean, DateTime, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

logger = structlog.get_logger(__name__)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # NULL for IP-only rate limit scopes (attempt_type='public_submission').
    email: Mapped[str | None] = mapped_column(Text, nullable=True)

    ip: Mapped[str] = mapped_column(Text, nullable=False)

    # Discriminates between rate limit buckets.
    # Values: 'login' | 'reset' | 'public_submission'
    # Default 'login' matches legacy behaviour before TASK-A-16 was added.
    attempt_type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="login"
    )

    success: Mapped[bool] = mapped_column(Boolean, nullable=False)

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index(
            "idx_login_attempts_lookup",
            "email",
            "ip",
            "attempt_type",
            "attempted_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LoginAttempt id={self.id} type={self.attempt_type} "
            f"email={self.email} ip={self.ip} success={self.success}>"
        )
