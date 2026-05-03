"""
app/schemas/auth — Pydantic request/response schemas for admin auth endpoints.

Endpoints covered:
  POST /api/admin/auth/login          → LoginRequest / LoginResponse
  POST /api/admin/auth/logout         → (no body; 204 response)
  GET  /api/admin/auth/me             → MeResponse
  POST /api/admin/auth/forgot-password → ForgotPasswordRequest
  POST /api/admin/auth/reset-password  → ResetPasswordRequest
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Returned on successful login. Thin shape — session lives in the cookie."""

    user: dict  # {id: str, email: str}


class MeResponse(BaseModel):
    """Returned by GET /api/admin/auth/me for authenticated users."""

    id: str
    email: str
    last_login_at: datetime | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """
    Password policy (design §2.1 / TASK-A-11):
      - Minimum 12 characters (enforced by Pydantic Field)
      - At least 1 letter AND at least 1 digit (enforced in the route handler)

    The 12-char floor is deliberately low — this is an admin tool used by trusted
    operators who will use a password manager. The letter+digit rule prevents trivially
    guessable all-digit PINs. Argon2id makes brute-force irrelevant for online attacks,
    and the rate limiter (login, 5/15min) caps offline attempts that don't have the hash.
    """

    token: str
    new_password: str = Field(min_length=12)
