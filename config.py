"""
Centralized configuration from environment variables.
Uses Pydantic BaseSettings for validation and .env file support.

New settings added in TASK-X-04 (admin platform Phase A):
  SECRET_KEY         — HMAC signing key for signed URLs and session integrity.
                       MUST be separate from WEBHOOK_SECRET (different rotation
                       cadence and blast radius — see design §0 A1).
  DB_URL             — SQLAlchemy async URL for aiosqlite.
  SESSION_TTL_DAYS   — Admin session lifetime (absolute cap, default 30d).
  SIGNED_URL_TTL_HOURS — Client report download link lifetime (default 168h = 7d).
  SMTP_*             — Email delivery (aiosmtplib). SMTP_FROM defaults to SMTP_USER.
  TRUSTED_PROXY      — If true, X-Forwarded-For is trusted for IP detection (used
                       by the rate limiter on the public form endpoint).
"""

from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    # Anthropic (LLM)
    anthropic_api_key: SecretStr = SecretStr("")

    # Webhook (public form auth)
    webhook_secret: SecretStr = SecretStr("")
    webhook_port: int = 8100

    # CORS
    cors_origins: str = "https://assess.zanovix.com,http://localhost:5173"

    # --- Admin platform (TASK-X-04) ---

    # Signing key for HMAC-signed download URLs. Generate with:
    #   python -c "import secrets; print(secrets.token_urlsafe(32))"
    # Keep separate from WEBHOOK_SECRET — different concerns, different rotation cadence.
    secret_key: SecretStr = SecretStr("")

    # SQLAlchemy async URL. The app/ package uses the async engine via aiosqlite.
    # Alembic (Phase A TASK-A-04) uses a separate SYNC engine pointing at the same file.
    db_url: str = "sqlite+aiosqlite:///app/data/app.db"

    # Admin session lifetime — absolute cap, re-login required after expiry.
    session_ttl_days: int = 30

    # Signed URL TTL for client report downloads (7 days default).
    # Preview PDF TTLs are hard-coded to 1 hour in signed_urls.py (not env-configurable —
    # they are ephemeral UI artifacts, not something operators should tune).
    signed_url_ttl_hours: int = 168

    # SMTP — used by app/email/sender.py via aiosmtplib.
    # SMTP_USE_TLS controls STARTTLS (port 587). For implicit TLS (port 465) you would
    # need a different flag — aiosmtplib exposes use_tls for that. Defaulting to STARTTLS.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = ""          # defaults to smtp_user at runtime if left empty
    smtp_use_tls: bool = True    # STARTTLS on port 587

    # If True, X-Forwarded-For is trusted for client IP detection (rate limiter).
    # Set to True ONLY when the app runs behind a known reverse proxy (nginx/Caddy).
    # Setting this to True on a directly-exposed app allows IP spoofing.
    trusted_proxy: bool = False

    # Salt for IP hashing (GDPR). Combined with raw IP before sha256.
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    ip_hash_salt: str = ""

    # Consultant notification email — receives auto_accept + new lead alerts.
    consultant_email: str = ""

    # Consultant display name shown on PDF deliverables (cover + closing page).
    consultant_name: str = "Equipo Zanovix"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton — import this from other modules
settings = Settings()
