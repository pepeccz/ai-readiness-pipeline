"""
app/auth/rate_limit — Fixed-window rate limiter using the login_attempts table.

Supports multiple attempt types (TASK-A-16 addendum):
  'login'             — 5 attempts per 15 minutes per (email, ip)
  'reset'             — 3 attempts per 1 hour per (email, ip)
  'public_submission' — 3 attempts per 1 hour per ip only (email=NULL)

Algorithm: simple fixed window per (email, ip, attempt_type).
  - Pre-check: COUNT rows in the window where success=false.
  - If count >= max_attempts → rate limited (return False from check_rate_limit).
  - Every attempt (success or fail) records a row.
  - Inline prune: DELETE rows older than the window for the same key to bound growth.

Inline pruning rationale (design §0 A5):
  On every record_attempt() call, we DELETE rows older than 1 hour (or the window,
  whichever is larger) for the same (email, ip, attempt_type) combination. This is
  O(1) amortised — bounded by the window, covered by the composite index, and cheap
  because it's scoped tightly. Phase D adds a global unscoped sweep for hygiene.

  Prune window is 1 hour regardless of the rate limit window, so login rows
  (15-min window) are kept for up to 1 hour for audit purposes before deletion.

SQLite datetime notes:
  SQLite stores datetimes as text in ISO-8601 format when using DateTime(timezone=True).
  aiosqlite (and the sync engine) represent timezone-aware datetimes correctly.
  For the comparison `attempted_at > :cutoff`, both sides must be timezone-aware
  Python datetimes — SQLAlchemy handles the serialisation.

IP detection:
  Callers are responsible for extracting the client IP from the request and passing
  it here. In public_routes.py, X-Forwarded-For is used when trusted_proxy=True
  (config setting); direct IP otherwise. This module is IP-agnostic.
"""

from datetime import datetime, timedelta, timezone
from typing import Literal

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_attempt import LoginAttempt

logger = structlog.get_logger(__name__)

AttemptType = Literal["login", "reset", "public_submission"]

# Default rate limit parameters per attempt type.
# Callers may override these via the max_attempts / window_seconds parameters.
_DEFAULTS: dict[str, tuple[int, int]] = {
    "login": (5, 15 * 60),       # 5 per 15 minutes
    "reset": (3, 60 * 60),       # 3 per hour
    "public_submission": (3, 60 * 60),  # 3 per hour
}

# Prune rows older than this, regardless of rate limit window.
_PRUNE_HORIZON_SECONDS = 60 * 60  # 1 hour


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


async def check_rate_limit(
    db: AsyncSession,
    email: str | None,
    ip: str,
    attempt_type: AttemptType = "login",
    max_attempts: int | None = None,
    window_seconds: int | None = None,
) -> bool:
    """
    Check whether a client is under the rate limit.

    Counts failed attempts (success=False) within the window. Successful attempts
    are recorded but do NOT count toward the rate limit — a successful login resets
    the practical window because subsequent attempts need a new login flow.

    Args:
        db:             Active AsyncSession.
        email:          User email (None for IP-only scopes like 'public_submission').
        ip:             Client IP address.
        attempt_type:   One of 'login', 'reset', 'public_submission'.
        max_attempts:   Override the default max for this type. If None, uses default.
        window_seconds: Override the default window for this type. If None, uses default.

    Returns:
        True  — client is UNDER the limit (request may proceed).
        False — client has EXCEEDED the limit (caller should return 429).
    """
    default_max, default_window = _DEFAULTS.get(attempt_type, (5, 900))
    max_attempts = max_attempts if max_attempts is not None else default_max
    window_seconds = window_seconds if window_seconds is not None else default_window

    cutoff = _now_utc() - timedelta(seconds=window_seconds)

    query = select(func.count()).select_from(LoginAttempt).where(
        LoginAttempt.ip == ip,
        LoginAttempt.attempt_type == attempt_type,
        LoginAttempt.success.is_(False),
        LoginAttempt.attempted_at > cutoff,
    )

    # For email-scoped types, add email filter.
    # For 'public_submission' (IP-only), email IS NULL — don't filter by email.
    if email is not None:
        query = query.where(LoginAttempt.email == email)
    else:
        query = query.where(LoginAttempt.email.is_(None))

    result = await db.execute(query)
    count = result.scalar_one()

    is_under_limit = count < max_attempts
    if not is_under_limit:
        logger.warning(
            "rate_limit_exceeded",
            email=email,
            ip=ip,
            attempt_type=attempt_type,
            count=count,
            max_attempts=max_attempts,
        )
    return is_under_limit


async def record_attempt(
    db: AsyncSession,
    email: str | None,
    ip: str,
    attempt_type: AttemptType = "login",
    success: bool = False,
) -> None:
    """
    Record an authentication attempt and run inline prune.

    Inserts a LoginAttempt row, then immediately prunes rows older than
    _PRUNE_HORIZON_SECONDS for the same (email, ip, attempt_type) combination.

    Prune is inline (not a background task) because it's O(1) amortised, cheap,
    and avoids unbounded table growth without needing a scheduled job.

    Args:
        db:           Active AsyncSession.
        email:        User email (None for IP-only scopes).
        ip:           Client IP address.
        attempt_type: Discriminates the rate limit bucket.
        success:      Whether this attempt succeeded.
    """
    now = _now_utc()

    attempt = LoginAttempt(
        email=email,
        ip=ip,
        attempt_type=attempt_type,
        success=success,
        attempted_at=now,
    )
    db.add(attempt)

    # Inline prune: DELETE rows older than 1 hour for this (email, ip, attempt_type).
    # Scoped tightly to avoid a full-table scan — covered by idx_login_attempts_lookup.
    prune_cutoff = now - timedelta(seconds=_PRUNE_HORIZON_SECONDS)

    prune_query = delete(LoginAttempt).where(
        LoginAttempt.ip == ip,
        LoginAttempt.attempt_type == attempt_type,
        LoginAttempt.attempted_at < prune_cutoff,
    )

    if email is not None:
        prune_query = prune_query.where(LoginAttempt.email == email)
    else:
        prune_query = prune_query.where(LoginAttempt.email.is_(None))

    result = await db.execute(prune_query)
    pruned = result.rowcount

    await db.flush()

    logger.debug(
        "attempt_recorded",
        email=email,
        ip=ip,
        attempt_type=attempt_type,
        success=success,
        pruned=pruned,
    )
