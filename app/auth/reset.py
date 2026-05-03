"""
app/auth/reset — Password reset token generation and verification.

Design (design §2.1):
  - Token: secrets.token_urlsafe(32) → 43-char URL-safe string (~256 bits entropy)
  - Storage: SHA-256 of the raw token stored in users.password_reset_token_hash.
    The raw token is NEVER stored — only sent by email.
  - Argon2id is intentionally NOT used here. The token has ~256-bit entropy
    (32 random bytes from /dev/urandom), so SHA-256 is sufficient. Argon2id is for
    human-chosen passwords which have much lower entropy. See password.py module note.
  - TTL: 1 hour (password_reset_expires_at = NOW() + 1h).
  - Single-use: consume_reset_token() sets both columns to NULL in the same UPDATE,
    so re-use of the same token is impossible (idempotent — safe to call twice, second
    call just won't find a matching row).

Flow:
  1. generate_reset_token(db, user) → raw_token
     Stores sha256(raw_token) in the user row and returns the raw token.
     Caller emails the raw token; the URL-safe format makes it safe in query params.

  2. consume_reset_token(db, raw_token) → User | None
     Looks up the user by sha256(raw_token) WHERE expires_at > NOW().
     If found, clears both token columns atomically and returns the User.
     Returns None if token is not found or expired.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = structlog.get_logger(__name__)

_TOKEN_TTL_HOURS = 1


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _sha256_token(raw_token: str) -> str:
    """Return the hex-encoded SHA-256 hash of a raw token string."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def generate_reset_token(db: AsyncSession, user: User) -> str:
    """
    Generate a password reset token for the given user, persist the hash, and
    return the raw (unhashed) token for inclusion in the email link.

    This function flushes but does NOT commit — the caller must commit to ensure
    atomicity with any surrounding operations (e.g. rate limit record_attempt).

    Args:
        db:   Active AsyncSession.
        user: The User whose password_reset_token_hash will be updated.

    Returns:
        The raw URL-safe token (43 chars). Include this in the reset URL as the
        `token` query parameter. NEVER log or store this value — only email it.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = _sha256_token(raw_token)
    expires_at = _now_utc() + timedelta(hours=_TOKEN_TTL_HOURS)

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            password_reset_token_hash=token_hash,
            password_reset_expires_at=expires_at,
        )
    )
    await db.flush()

    logger.info(
        "reset_token_generated",
        user_id=str(user.id),
        expires_at=expires_at.isoformat(),
    )
    return raw_token


async def consume_reset_token(
    db: AsyncSession, raw_token: str
) -> User | None:
    """
    Validate and consume a password reset token.

    Looks up the User whose password_reset_token_hash matches sha256(raw_token)
    AND whose password_reset_expires_at is in the future. If found, clears both
    token columns (making the token single-use) and returns the User.

    This function flushes but does NOT commit — the caller must commit after
    updating the password and revoking sessions.

    Args:
        db:        Active AsyncSession.
        raw_token: The raw token string from the URL query parameter.

    Returns:
        The matching User if the token is valid and not expired. None otherwise.
    """
    now = _now_utc()
    token_hash = _sha256_token(raw_token)

    result = await db.execute(
        select(User).where(
            User.password_reset_token_hash == token_hash,
            User.password_reset_expires_at > now,
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning("reset_token_invalid_or_expired")
        return None

    # Clear the token immediately — single-use enforcement.
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            password_reset_token_hash=None,
            password_reset_expires_at=None,
        )
    )
    await db.flush()

    logger.info("reset_token_consumed", user_id=str(user.id))
    return user
