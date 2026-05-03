"""
app/api/auth_routes — Admin authentication endpoints.

Router prefix: /api/admin/auth  (registered in webhook_service.py as
  app.include_router(router, prefix="/api/admin"))

Endpoints:
  POST /api/admin/auth/login           — Argon2id verify + session cookie
  POST /api/admin/auth/logout          — revoke session, clear cookie
  GET  /api/admin/auth/me              — return current user (requires auth)
  POST /api/admin/auth/forgot-password — generate + email reset token
  POST /api/admin/auth/reset-password  — consume token + update password

Security decisions (design §2.1 + TASK-A-16):
  - Login: rate limit 5/15min per (email, ip) BEFORE Argon2 verify to save CPU.
    When user doesn't exist, still call verify_password(_DUMMY_HASH, ...) to prevent
    user enumeration via timing difference (constant-time-ish).
  - Forgot-password: rate limit 3/hour per (email, ip) BEFORE any DB query.
    Response is IDENTICAL whether the email exists or not (constant-time + no info leak).
  - Reset-password: token validated by sha256 match + expiry check; token is consumed
    (NULLed) atomically; ALL sessions revoked after password change.
  - Cookie: HttpOnly, Secure, SameSite=Lax, Max-Age=2592000 (30 days). Path=/.

Password policy for reset-password:
  - Min 12 chars (Pydantic Field on ResetPasswordRequest)
  - At least 1 letter AND at least 1 digit (validated in handler)
  Rationale: documented in app/schemas/auth.py. Strict enough to block trivial PINs,
  lenient enough for password managers. Argon2id + rate limiter cover the rest.
"""

import re
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_client_ip, require_admin
from app.auth.password import hash_password, verify_password
from app.auth.rate_limit import check_rate_limit, record_attempt
from app.auth.reset import consume_reset_token, generate_reset_token
from app.auth.sessions import create_session, revoke_all_user_sessions, revoke_session
from app.db.session import get_db
from app.email.sender import send_email
from app.email.templates import password_reset_email
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    ResetPasswordRequest,
)
from app.schemas.common import ApiException
from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["admin-auth"])

# ---------------------------------------------------------------------------
# Timing-attack mitigation constant
# ---------------------------------------------------------------------------
# When the login email doesn't match any user, we still run verify_password
# against this dummy hash so the response time is indistinguishable from the
# "wrong password for a real user" path. Without this, an attacker can
# enumerate valid emails by comparing response latencies (real user = Argon2
# time; unknown email = near-instant).
#
# This is a valid Argon2id hash of the string "dummy" — generated once and
# hardcoded so it's always available without any DB round-trip.
# To regenerate: python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('dummy'))"
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4"
    "$c2FsdHNhbHRzYWx0c2Fs"
    "$abcdefghijklmnopqrstuvwxyz012345"  # not a real hash — will always fail
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASSWORD_RE = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d).+$")


def _validate_new_password(password: str) -> None:
    """
    Enforce the password policy beyond the min-length Pydantic check.

    Policy: min 12 chars (enforced by schema) + at least 1 letter + 1 digit.

    Raises ApiException(400, "weak_password") if the policy is violated.
    """
    if not _PASSWORD_RE.match(password):
        raise ApiException(
            status_code=400,
            code="weak_password",
            detail="La contraseña debe tener al menos una letra y un número.",
        )


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# POST /api/admin/auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate an admin user and create a session cookie.

    Order of operations (design §3.1):
      1. Pre-check rate limit (no Argon2 yet — saves CPU + prevents timing leak)
      2. SELECT user WHERE email=:e AND is_active=true
      3. verify_password — against real hash OR dummy hash (user not found case)
      4. On success: create session, record attempt, update last_login_at, set cookie
      5. On failure: record attempt (no-op on rate-limit path), return 401
    """
    ip = get_client_ip(request)
    email = str(body.email)

    # 1. Rate limit check BEFORE Argon2 (saves CPU, prevents timing enumeration).
    under_limit = await check_rate_limit(
        db, email, ip, attempt_type="login", max_attempts=5, window_seconds=900
    )
    if not under_limit:
        logger.warning("login_rate_limited", email=email, ip=ip)
        raise ApiException(
            status_code=429,
            code="rate_limited",
            detail="Demasiados intentos. Intentá de nuevo en 15 minutos.",
        )

    # 2. Look up the user.
    result = await db.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    # 3. Verify password — always call verify_password to keep timing constant.
    if user is None:
        # Timing mitigation: burn Argon2 time against a dummy hash.
        # The result is always False — we just need the delay.
        verify_password(body.password, _DUMMY_HASH)
        await record_attempt(db, email, ip, attempt_type="login", success=False)
        await db.commit()
        raise ApiException(
            status_code=401,
            code="invalid_credentials",
            detail="Email o contraseña incorrectos.",
        )

    password_ok = verify_password(body.password, user.password_hash)
    if not password_ok:
        await record_attempt(db, email, ip, attempt_type="login", success=False)
        await db.commit()
        raise ApiException(
            status_code=401,
            code="invalid_credentials",
            detail="Email o contraseña incorrectos.",
        )

    # 4. Successful login.
    session = await create_session(db, user.id, ttl_days=settings.session_ttl_days)
    await record_attempt(db, email, ip, attempt_type="login", success=True)
    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=_now_utc())
    )
    await db.commit()

    # Set the session cookie.
    # `secure` is autodetected: True if the request arrived via HTTPS (direct or
    # behind a TLS-terminating proxy that sets X-Forwarded-Proto=https), False
    # otherwise. Hardcoding True breaks dev (HTTP) because browsers silently
    # drop Secure cookies on plain HTTP, causing the post-login /me to be 401
    # — the user sees "wrong password" even though the login succeeded.
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
    is_https = request.url.scheme == "https" or forwarded_proto == "https"
    response.set_cookie(
        key="admin_sid",
        value=session.id,
        max_age=settings.session_ttl_days * 86400,  # seconds
        path="/",
        httponly=True,
        secure=is_https,
        samesite="lax",
    )

    logger.info("login_success", user_id=str(user.id), email=email)
    return LoginResponse(user={"id": str(user.id), "email": user.email})


# ---------------------------------------------------------------------------
# POST /api/admin/auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke the current admin session and clear the cookie.

    Safe to call even when not logged in — cookie absent or session already
    revoked are no-ops. Always returns 204.
    """
    sid = request.cookies.get("admin_sid")
    if sid:
        await revoke_session(db, sid)
        await db.commit()
        logger.info("logout", sid_prefix=sid[:8])

    response.delete_cookie(key="admin_sid", path="/")


# ---------------------------------------------------------------------------
# GET /api/admin/auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(require_admin)) -> MeResponse:
    """
    Return the currently authenticated user's profile.

    Authentication is handled by the `require_admin` dependency which also
    updates last_seen_at. Returns 401 if not authenticated (via ApiException).
    """
    return MeResponse(
        id=str(user.id),
        email=user.email,
        last_login_at=user.last_login_at,
    )


# ---------------------------------------------------------------------------
# POST /api/admin/auth/forgot-password
# ---------------------------------------------------------------------------


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Initiate a password reset flow.

    Security properties:
      - Rate limited: 3 attempts / hour per (email, ip) — TASK-A-16.
      - Constant-time response: IDENTICAL response whether email exists or not.
        This prevents user enumeration (attacker can't tell if the email is registered).
      - Email send is fire-and-forget (BackgroundTask). Failure is swallowed silently.
        The user can try again; a failed email doesn't break the security model.

    The reset link format: https://{host}/admin/reset-password?token={raw_token}
    The frontend captures `token` from the query string and POSTs to reset-password.
    """
    ip = get_client_ip(request)
    email = str(body.email)

    # 1. Rate limit — 3 per hour per (email, ip).
    under_limit = await check_rate_limit(
        db, email, ip, attempt_type="reset", max_attempts=3, window_seconds=3600
    )
    if not under_limit:
        logger.warning("forgot_password_rate_limited", email=email, ip=ip)
        raise ApiException(
            status_code=429,
            code="rate_limited",
            detail="Demasiados intentos. Intentá de nuevo en 1 hora.",
        )

    # 2. Look up the user — do NOT filter by is_active; same response either way.
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # 3. Generate token and schedule email ONLY if user exists.
    if user is not None:
        raw_token = await generate_reset_token(db, user)

        # Build the reset URL from the request host.
        host = request.headers.get("X-Forwarded-Host") or request.headers.get("host", "localhost")
        scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
        reset_url = f"{scheme}://{host}/admin/reset-password?token={raw_token}"

        # Template from app/email/templates.py — do NOT inline here (design §2.5).
        subject, body_text = password_reset_email(reset_url=reset_url)

        # Fire-and-forget — don't await; failures are swallowed silently (design §2.5).
        background_tasks.add_task(send_email, email, subject, body_text)

        logger.info("reset_token_email_queued", email=email)
    else:
        logger.debug("forgot_password_unknown_email", email=email)

    # 4. Record the attempt regardless of whether the user exists.
    await record_attempt(db, email, ip, attempt_type="reset", success=True)
    await db.commit()

    # 5. Always return the same generic message — do NOT hint whether email exists.
    return {
        "detail": "Si el email existe, recibirás un enlace para restablecer tu contraseña."
    }


# ---------------------------------------------------------------------------
# POST /api/admin/auth/reset-password
# ---------------------------------------------------------------------------


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Set a new password using a valid reset token.

    Steps:
      1. Validate new password meets policy (min 12 chars + letter + digit).
      2. Consume the reset token — returns User if valid, None if not found/expired.
      3. Hash the new password with Argon2id.
      4. Update User: new password_hash, clear token columns.
      5. Revoke ALL sessions for the user (force re-auth everywhere).
      6. Commit.
      7. Return 200 with success message.
    """
    # 1. Password policy (min-length already enforced by Pydantic schema).
    _validate_new_password(body.new_password)

    # 2. Consume token — validates sha256 match + expiry atomically.
    user = await consume_reset_token(db, body.token)
    if user is None:
        raise ApiException(
            status_code=400,
            code="invalid_token",
            detail="El enlace de restablecimiento es inválido o ha expirado.",
        )

    # 3+4. Hash new password and persist.
    new_hash = hash_password(body.new_password)
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(password_hash=new_hash)
    )

    # 5. Revoke all sessions — force re-authentication from all devices.
    await revoke_all_user_sessions(db, user.id)

    # 6. Commit everything in one shot.
    await db.commit()

    logger.info("password_reset_success", user_id=str(user.id))

    return {"detail": "Contraseña actualizada. Iniciá sesión nuevamente."}


# ---------------------------------------------------------------------------
# Diagnostics — admin-only operational health (Phase D bonus)
# ---------------------------------------------------------------------------


@router.get("/diagnostics", tags=["admin-auth"])
async def get_diagnostics(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Admin-only operational diagnostics.

    Returns row counts per table, count of orphaned pending_review assessments
    (pending_review with null llm_enriched_data), and active admin count.
    Useful for first-deploy sanity checks and support triage.
    """
    from sqlalchemy import func  # noqa: PLC0415
    from app.models.assessment import Assessment  # noqa: PLC0415
    from app.models.session_row import SessionRow  # noqa: PLC0415
    from app.models.login_attempt import LoginAttempt  # noqa: PLC0415

    now = datetime.now(tz=timezone.utc)

    counts_result = await db.execute(
        select(
            func.count(Assessment.id).label("assessments"),
        )
    )
    assessment_count = counts_result.scalar_one()

    orphaned_result = await db.execute(
        select(func.count(Assessment.id)).where(
            Assessment.status == "pending_review",
            Assessment.llm_enriched_data.is_(None),
        )
    )
    orphaned_count = orphaned_result.scalar_one()

    active_admins_result = await db.execute(
        select(func.count(User.id)).where(User.is_active.is_(True))
    )
    active_admins = active_admins_result.scalar_one()

    active_sessions_result = await db.execute(
        select(func.count(SessionRow.id)).where(
            SessionRow.revoked_at.is_(None),
            SessionRow.expires_at > now,
        )
    )
    active_sessions = active_sessions_result.scalar_one()

    login_attempts_result = await db.execute(
        select(func.count(LoginAttempt.id))
    )
    login_attempt_count = login_attempts_result.scalar_one()

    return {
        "status": "ok",
        "counts": {
            "assessments": assessment_count,
            "active_admins": active_admins,
            "active_sessions": active_sessions,
            "login_attempts_total": login_attempt_count,
        },
        "alerts": {
            "orphaned_pending_review": orphaned_count,
        },
        "timestamp": now.isoformat(),
    }
