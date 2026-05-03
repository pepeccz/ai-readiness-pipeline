"""
app/auth/middleware — FastAPI dependency for authenticated admin routes.

Usage:
    from app.auth.middleware import require_admin
    from app.models.user import User

    @router.get("/some-protected-endpoint")
    async def handler(user: User = Depends(require_admin)):
        ...

The `require_admin` dependency:
  1. Reads the `admin_sid` cookie from the request.
  2. Looks up the session via get_active_session (not revoked, not expired).
  3. Updates last_seen_at (sliding visibility without extending expires_at).
  4. Fetches the User row and verifies is_active.
  5. Commits the last_seen_at update.
  6. Returns the User object for use in the handler.

Raises ApiException (→ 401) on any failure — caught by the global error handler
registered in webhook_service.py (add_error_handlers).

IP detection helper:
  `get_client_ip(request)` reads X-Forwarded-For when settings.trusted_proxy is
  True, otherwise falls back to request.client.host. Both the login and
  forgot-password routes use this helper to populate the rate limiter.
"""

import structlog
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import get_active_session, update_last_seen
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import ApiException
from config import settings

logger = structlog.get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP from the request.

    When settings.trusted_proxy is True, reads the first value from
    X-Forwarded-For (the original client IP set by nginx/Caddy). When False,
    uses request.client.host directly (appropriate for direct connections).

    IP spoofing note: trusting X-Forwarded-For on a directly-exposed server
    allows any client to forge their IP. ONLY set trusted_proxy=True when
    the app runs behind a known reverse proxy that strips/rewrites the header.
    """
    if settings.trusted_proxy:
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            # X-Forwarded-For: client, proxy1, proxy2 — first value is original client
            return xff.split(",")[0].strip()

    host = request.client.host if request.client else "unknown"
    return host


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that authenticates the caller as an active admin.

    Reads the `admin_sid` cookie, validates the session, updates last_seen_at,
    and returns the User row. Raises ApiException(401) on any failure.

    Args:
        request: The incoming HTTP request (injected by FastAPI).
        db:      The async database session (injected by get_db).

    Returns:
        The authenticated and active User instance.

    Raises:
        ApiException(401, "unauthenticated")  — no cookie present
        ApiException(401, "session_invalid")  — session not found, revoked, or expired
        ApiException(401, "user_inactive")    — user account has been deactivated
    """
    sid = request.cookies.get("admin_sid")
    if not sid:
        raise ApiException(
            status_code=401,
            code="unauthenticated",
            detail="Not logged in",
        )

    session = await get_active_session(db, sid)
    if session is None:
        logger.warning("session_invalid_or_expired", sid_prefix=sid[:8])
        raise ApiException(
            status_code=401,
            code="session_invalid",
            detail="Session expired or revoked",
        )

    # Update sliding visibility timestamp.
    # Does NOT extend expires_at — 30-day hard cap is absolute (design §2.1).
    await update_last_seen(db, sid)

    user = await db.get(User, session.user_id)
    if user is None or not user.is_active:
        logger.warning(
            "user_inactive_or_missing",
            user_id=str(session.user_id),
        )
        raise ApiException(
            status_code=401,
            code="user_inactive",
            detail="User no longer active",
        )

    # Commit the last_seen_at update — the request session is still open here.
    await db.commit()

    return user
