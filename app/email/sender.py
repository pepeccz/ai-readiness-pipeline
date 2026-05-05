"""
app/email/sender — Async SMTP email delivery via aiosmtplib.

SMTP mode selection (design §2.5, config.py comments):
  - Port 587 + smtp_use_tls=True  → STARTTLS (most common, e.g. Gmail, SendGrid)
  - Port 465 + smtp_use_tls=False → Implicit TLS / SMTPS (legacy "secure SMTP")

The `aiosmtplib.send()` keyword names are different for each mode:
  - STARTTLS: start_tls=True   (negotiates upgrade after EHLO)
  - SMTPS:    use_tls=True     (TLS handshake before SMTP dialog)

This module selects the correct flag based on port number at call time:
  - Port 465 AND smtp_use_tls=True → use_tls=True (implicit TLS)
  - Any other port + smtp_use_tls=True → start_tls=True (STARTTLS)
  - smtp_use_tls=False → plaintext (dev/test only — never use in production)

Failure policy (design §2.5 + §3.1):
  send_email() NEVER raises. It catches all exceptions, logs them at ERROR level,
  and returns False. Callers interpret the bool and decide what to do:
  - forgot-password: ignores False (fire-and-forget, silent failure per spec)
  - approve-and-send: sets email_status='failed' so the admin can retry manually

From address:
  Prefers settings.smtp_from if set; falls back to settings.smtp_user.
  This lets operators use a "no-reply@" display address while authenticating
  with a different SMTP account (common with Gmail App Passwords).
"""

from email.message import EmailMessage

import aiosmtplib
import structlog

from config import settings

logger = structlog.get_logger(__name__)


def _smtp_from() -> str:
    """Return the From address: smtp_from if set, else smtp_user."""
    return settings.smtp_from or settings.smtp_user


async def send_email(to: str, subject: str, body: str, template: str = "unknown", lead_id: str | None = None) -> bool:
    """
    Send a plain-text email asynchronously.

    Args:
        to:      Recipient email address.
        subject: Email subject line.
        body:    Plain-text email body.

    Returns:
        True if the email was accepted by the SMTP server.
        False on any error (connection failure, auth error, etc.) — error is logged.

    Never raises. Callers are responsible for interpreting the bool return value.

    SMTP mode is chosen at call time based on settings.smtp_port:
      465 + smtp_use_tls=True → implicit TLS (use_tls=True)
      587 + smtp_use_tls=True → STARTTLS (start_tls=True)  ← default
      any port, smtp_use_tls=False → plaintext (test/dev only)
    """
    message = EmailMessage()
    message["From"] = _smtp_from()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    # Determine TLS mode based on port + smtp_use_tls flag.
    # Port 465 with TLS enabled = implicit TLS (connect encrypted from the start).
    # Any other port with TLS enabled = STARTTLS (upgrade after initial handshake).
    use_implicit_tls = settings.smtp_use_tls and settings.smtp_port == 465
    use_starttls = settings.smtp_use_tls and not use_implicit_tls

    smtp_kwargs: dict = {
        "hostname": settings.smtp_host,
        "port": settings.smtp_port,
        "username": settings.smtp_user,
        "password": settings.smtp_password.get_secret_value(),
    }

    if use_implicit_tls:
        smtp_kwargs["use_tls"] = True
        tls_mode = "implicit_tls"
    elif use_starttls:
        smtp_kwargs["start_tls"] = True
        tls_mode = "starttls"
    else:
        tls_mode = "plaintext"

    try:
        await aiosmtplib.send(message, **smtp_kwargs)
        logger.info(
            "email_sent",
            recipient=to,
            template=template,
            lead_id=lead_id,
            subject=subject,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            tls_mode=tls_mode,
        )
        return True
    except Exception as exc:
        logger.error(
            "smtp_send_failed",
            to=to,
            subject=subject,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            tls_mode=tls_mode,
            error=str(exc),
        )
        return False
