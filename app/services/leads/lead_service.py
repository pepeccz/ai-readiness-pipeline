"""
app/services/leads/lead_service — Business logic for admin lead actions.

Actions:
  accept             — status → accepted, set assigned_consultant_id, set accepted_at
  reject             — status → rejected, set rejected_reason
  request_extra_info — send email to lead (status unchanged)
  assign_consultant  — set assigned_consultant_id (status unchanged)

Email dispatched for accept and reject as BackgroundTask.
"""

from __future__ import annotations

import structlog

from app.email import sender as email_sender
from app.email.templates import get_lead_accepted_email, get_lead_rejected_email, get_lead_extra_info_email
from app.models.lead import Lead

logger = structlog.get_logger(__name__)


async def send_lead_accepted_email(lead: Lead) -> None:
    """Send acceptance email to lead. Fire-and-forget (ignores return value)."""
    subject, body = get_lead_accepted_email(lead)
    await email_sender.send_email(lead.email, subject, body)
    logger.info("lead_accepted_email_sent", lead_id=lead.id)


async def send_lead_rejected_email(lead: Lead) -> None:
    """Send rejection email to lead. Fire-and-forget."""
    subject, body = get_lead_rejected_email(lead)
    await email_sender.send_email(lead.email, subject, body)
    logger.info("lead_rejected_email_sent", lead_id=lead.id)


async def send_lead_extra_info_email(lead: Lead) -> None:
    """Send 'request extra info' email to lead."""
    subject, body = get_lead_extra_info_email(lead)
    await email_sender.send_email(lead.email, subject, body)
    logger.info("lead_extra_info_email_sent", lead_id=lead.id)
