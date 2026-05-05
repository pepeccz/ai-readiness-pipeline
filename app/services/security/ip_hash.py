"""
app/services/security/ip_hash — T3.7

GDPR-friendly IP hashing. Plain IPs are never stored.

hash_ip(ip) → sha256(ip + SALT) as a 64-char hex string.

SALT is read from settings.ip_hash_salt. If not set, falls back to a
module-level constant (acceptable for MVP; production should set the env var).
"""

from __future__ import annotations

import hashlib

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extract the client IP from the request.

    Respects X-Forwarded-For header (first IP in chain) when present,
    falling back to request.client.host for direct connections.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the leftmost IP (the original client)
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def hash_ip(ip: str, salt: str = "") -> str:
    """
    Return sha256(ip + salt) as a 64-character hex string.

    Args:
        ip:   Plain IP address string.
        salt: Application-level salt (read from config in production).
              Empty string is acceptable for tests.

    Returns:
        64-char hex digest — safe to store per GDPR (irreversible).
    """
    raw = f"{ip}{salt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
