"""
app/auth/password — Argon2id password hashing wrapper.

Uses argon2-cffi (https://argon2-cffi.readthedocs.io/) with explicit parameters
matching design §2.1:

  time_cost=3       — 3 iterations
  memory_cost=65536 — 64 MiB per hash operation (KiB units)
  parallelism=4     — 4 parallel lanes
  hash_len=32       — 32-byte output
  salt_len=16       — 16-byte random salt

Estimated cost: ~80–120 ms on a modern VPS. At 5–10 logins/day this is
negligible. If this becomes a bottleneck, profile first — then reduce time_cost
before memory_cost (memory is the primary defence against GPU cracking).
See https://argon2-cffi.readthedocs.io/en/stable/parameters.html for tuning.

Singleton pattern:
  `_hasher` is a module-level instance created once at import time. Creating a
  new PasswordHasher on every call would re-parse the parameters each time —
  unnecessary overhead.

NOTE: Do NOT use this module for password reset tokens. `secrets.token_urlsafe(32)`
already has ~256-bit entropy — SHA256 is sufficient for tokens. Argon2id is only
needed where a human-chosen (low-entropy) secret is the input.
"""

import structlog
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

logger = structlog.get_logger(__name__)

# Module-level singleton — instantiated once at import time.
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB (in KiB)
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password with Argon2id.

    Returns an Argon2 encoded string starting with '$argon2id$...'.
    The salt is randomly generated for each call — never call this twice and
    compare the outputs to check equality; use verify_password() instead.

    Args:
        plain: The plaintext password to hash.

    Returns:
        The Argon2id encoded hash string (includes algorithm, params, salt, hash).
    """
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns True if the password matches, False if it doesn't.
    Never raises on a mismatch — callers should treat False as "wrong password"
    and not inspect the exception type for flow control.

    The argon2-cffi library handles the rehash-if-parameters-changed case
    internally (check_needs_rehash). If we ever update the PasswordHasher
    parameters, we should add a rehash path in the login flow. For now,
    parameters are stable so this is not needed.

    Args:
        plain:  The plaintext password to check.
        hashed: The stored Argon2 encoded hash string.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        _hasher.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        # Other exceptions (InvalidHashError, VerificationError) indicate a
        # corrupted hash or algorithm mismatch — treat as failed verification
        # to avoid leaking information, but log for observability.
        logger.warning("password_verify_error", exc_info=True)
        return False
