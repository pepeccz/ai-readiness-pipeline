"""
app/signed_urls — HMAC-SHA256 signed URL token generation and verification.

Used by approve-and-send and resend-email to produce a time-limited, tamper-proof
download URL for the client's PDF report.

Token format (URL-safe string, passed as ?token= query param):
    {assessment_id}.{expires_at_unix}.{hmac_hex}

Where:
    assessment_id   — UUID string (no braces)
    expires_at_unix — Unix timestamp (integer seconds) at which the URL expires
    hmac_hex        — lowercase hex HMAC-SHA256 of "{assessment_id}.{expires_at_unix}"

Signing key: settings.secret_key (SecretStr). MUST be a separate key from
WEBHOOK_SECRET — different rotation cadence and blast radius (see design §0 A1).

Verification order (design §2.4):
    1. Parse — split on '.'; must have exactly 3 parts
    2. Expiry check — expires_at < now() → 410 (resource gone)
    3. HMAC compare (constant-time) — bad signature → 403

Expiry is checked BEFORE the HMAC to fail fast on obviously stale tokens
without paying the HMAC computation cost. This does NOT introduce a timing
oracle because expiry is not secret — the unix timestamp is in the token itself.

TTLs:
    Client report download: settings.signed_url_ttl_hours (default 168h = 7 days)
    Preview PDF:            1 hour (hard-coded — ephemeral UI artifact)
    Password reset:         separate concern — handled in app/auth/reset.py

Design reference: design §2.4.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class SignedUrlError(Exception):
    """
    Raised by verify() when the token is invalid.

    Attributes:
        reason:      Short machine-readable string ('malformed', 'expired', 'bad_signature')
        status_code: HTTP status code the endpoint should return
                     403 for malformed/bad_signature
                     410 for expired
    """

    def __init__(self, reason: str, status: int) -> None:
        self.reason = reason
        self.status_code = status
        super().__init__(f"Signed URL error: {reason} (HTTP {status})")


def _get_key() -> bytes:
    """
    Return the raw signing key bytes from settings.

    Inline import so that config is not loaded at module import time —
    avoids circular import issues during FastAPI startup.
    """
    from config import settings  # noqa: PLC0415

    raw = settings.secret_key.get_secret_value()
    if not raw:
        # Fallback for dev environments where SECRET_KEY is not set.
        # Will produce valid tokens but they are predictable — document in .env.example.
        raw = "dev-insecure-key-set-SECRET_KEY-in-production"
    return raw.encode("utf-8")


def sign(assessment_id: str, ttl_seconds: int) -> str:
    """
    Generate a signed URL token for a given assessment.

    Args:
        assessment_id: UUID string (no braces).
        ttl_seconds:   Lifetime in seconds from now.

    Returns:
        A string token in the format "{assessment_id}.{expires_at}.{hmac_hex}".
        Pass this as the `token` query parameter in the download URL.

    Example:
        token = sign("abc-123", ttl_seconds=3600)
        url = f"https://assess.zanovix.com/api/assessment/{id}/download?token={token}"
    """
    expires_at = int(time.time()) + ttl_seconds
    payload = f"{assessment_id}.{expires_at}"
    sig = hmac.new(
        _get_key(),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{sig}"


def verify(token: str) -> str:
    """
    Verify a signed URL token and return the assessment_id.

    Verification order (design §2.4):
        1. Parse — must split into exactly 3 parts
        2. Expiry check — raises SignedUrlError('expired', 410) if stale
        3. HMAC compare — constant-time; raises SignedUrlError('bad_signature', 403)

    Args:
        token: The raw token string from the ?token= query parameter.

    Returns:
        The assessment_id embedded in the token (str).

    Raises:
        SignedUrlError('malformed', 403)       — token cannot be parsed
        SignedUrlError('expired', 410)          — token has passed its expiry
        SignedUrlError('bad_signature', 403)    — HMAC mismatch
    """
    # Step 1: Parse
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("wrong part count")
        assessment_id, expires_at_str, sig = parts
        expires_at = int(expires_at_str)
    except (ValueError, AttributeError):
        raise SignedUrlError("malformed", status=403)

    # Step 2: Expiry check (before HMAC — cheap, not secret)
    if expires_at < int(time.time()):
        raise SignedUrlError("expired", status=410)

    # Step 3: Constant-time HMAC compare
    payload = f"{assessment_id}.{expires_at}"
    expected = hmac.new(
        _get_key(),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig, expected):
        raise SignedUrlError("bad_signature", status=403)

    return assessment_id


# ---------------------------------------------------------------------------
# Generic payload signed URL (for DEEP form, multi-branch tokens)
# ---------------------------------------------------------------------------


def sign_payload(payload: dict, ttl_seconds: int) -> str:
    """
    Generate a signed URL token encoding an arbitrary JSON payload.

    Token format: base64(json_payload).{expires_at}.{hmac_hex}

    The payload is base64url-encoded so it survives URL embedding.
    Expiry and HMAC are computed over "b64_payload.expires_at".
    """
    expires_at = int(time.time()) + ttl_seconds
    b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    to_sign = f"{b64}.{expires_at}"
    sig = hmac.new(
        _get_key(),
        to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{to_sign}.{sig}"


def verify_payload(token: str) -> dict:
    """
    Verify a payload signed URL token and return the decoded payload dict.

    Raises SignedUrlError on any validation failure (malformed / expired / bad_signature).
    """
    try:
        # Split from right to handle the b64_payload which may contain dots after encoding
        # Format: b64.expires_at.sig — split from right to separate sig, then expires_at
        last_dot = token.rfind(".")
        second_last_dot = token.rfind(".", 0, last_dot)
        if last_dot == -1 or second_last_dot == -1:
            raise ValueError("wrong part count")
        b64_payload = token[:second_last_dot]
        expires_at_str = token[second_last_dot + 1 : last_dot]
        sig = token[last_dot + 1 :]
        expires_at = int(expires_at_str)
    except (ValueError, AttributeError):
        raise SignedUrlError("malformed", status=403)

    # Expiry before HMAC (cheap, not secret)
    if expires_at < int(time.time()):
        raise SignedUrlError("expired", status=410)

    # HMAC verify
    to_sign = f"{b64_payload}.{expires_at}"
    expected = hmac.new(
        _get_key(),
        to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise SignedUrlError("bad_signature", status=403)

    # Decode payload
    try:
        padding = "=" * (4 - len(b64_payload) % 4) if len(b64_payload) % 4 else ""
        return json.loads(base64.urlsafe_b64decode(b64_payload + padding))
    except Exception:
        raise SignedUrlError("malformed", status=403)
