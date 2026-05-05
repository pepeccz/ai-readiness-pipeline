"""
app/api/intake_routes — T3.2 + T3.3

Public TRIAGE endpoints:
  GET  /public/triage/schema   — return serialised schema (no auth, cached)
  POST /public/triage/submit   — validate + score + persist + email (rate limited)

Rate limiting: reuses app/auth/rate_limit.py with attempt_type='public_submission'
(3 per hour per IP, sliding window via LoginAttempt table).

Email: dispatched as BackgroundTask so response returns immediately.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rate_limit import check_rate_limit, record_attempt
from app.db.session import get_db
from app.email.sender import send_email
from app.models.consent import Consent
from app.models.lead import Lead
from app.schemas.triage import TriagePayload, TriageResponse
from app.services.email.triage_emails import (
    triage_consultant_notification,
    triage_email_for_bucket,
)
from app.services.questionnaire import schema_loader
from app.services.scoring.lead_scorer import LeadScorer
from app.services.security.ip_hash import get_client_ip, hash_ip
from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["public-triage"])

# Module-level scorer instance (stateless)
_scorer = LeadScorer()


# ---------------------------------------------------------------------------
# T3.2 — GET /public/triage/schema
# ---------------------------------------------------------------------------


@router.get("/public/triage/schema")
async def get_triage_schema():
    """
    Return the serialised TRIAGE schema from the in-memory cache.

    No auth required. Response is deterministic per server restart — no file I/O.
    """
    try:
        # Lazy-load if not yet loaded (e.g. in test context without lifespan)
        try:
            version = schema_loader.get_schema_version()
        except RuntimeError:
            schema_loader.load_all()
            version = schema_loader.get_schema_version()
        triage = schema_loader.get_triage_schema()
    except Exception as exc:
        logger.error("triage_schema_unavailable", error=str(exc))
        raise HTTPException(status_code=503, detail="Schema not loaded")

    return {"schema_version": version, "schema": triage}


# ---------------------------------------------------------------------------
# T3.3 — POST /public/triage/submit
# ---------------------------------------------------------------------------


@router.post("/public/triage/submit", status_code=201)
async def submit_triage(
    payload: TriagePayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> TriageResponse:
    """
    Validate + score + persist + dispatch email for a TRIAGE submission.

    Steps:
      1. Rate limit check (3/h per IP) — 429 on breach
      2. Score answers via LeadScorer
      3. Apply override rules from schema YAML
      4. Persist Lead (status=pending_review)
      5. Persist Consent rows (privacy + optional marketing)
      6. Record rate-limit attempt (success=True so it counts toward window)
      7. Dispatch background email to lead
      8. Dispatch background notification to consultant if bucket=auto_accept
      9. Return 201 with lead_id + bucket + message
    """
    ip = get_client_ip(request)
    ip_h = hash_ip(ip, salt=settings.ip_hash_salt)

    # ── 1. Rate limit ────────────────────────────────────────────────────────
    allowed = await check_rate_limit(
        db=db,
        email=None,
        ip=ip,
        attempt_type="public_submission",
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "retry_after_seconds": 3600,
            },
        )

    # ── 2. Score ─────────────────────────────────────────────────────────────
    answers = payload.answers
    answers_dict = {
        "triage.q.sector": answers.sector,
        "triage.q.company_size": answers.company_size,
        "triage.q.respondent_role": answers.respondent_role,
        "triage.q.ai_maturity": answers.ai_maturity,
        "triage.q.urgency": answers.urgency,
        "triage.q.ai_goals": answers.ai_goals,
        "triage.q.commitment": answers.commitment,
    }

    # ── 3. Override rules ─────────────────────────────────────────────────────
    override_rules = _get_override_rules()
    score_result = _scorer.score(answers=answers_dict, override_rules=override_rules)
    bucket = score_result.bucket

    # ── 4. Persist Lead ───────────────────────────────────────────────────────
    lead = Lead(
        full_name=answers.full_name,
        email=str(answers.email),
        company_name=answers.company_name,
        phone=answers.phone,
        sector=answers.sector,
        company_size=answers.company_size,
        respondent_role=answers.respondent_role,
        ai_maturity=answers.ai_maturity,
        ai_goals=answers.ai_goals,
        urgency=answers.urgency,
        commitment=answers.commitment,
        triage_payload=answers_dict,
        triage_score=score_result.total_score,
        triage_bucket=bucket,
        status="pending_review",
    )

    # Set external_advocate flag if override flagged it
    if score_result.flags.get("external_advocate"):
        lead.rejected_reason = None  # flag lives in payload for now

    db.add(lead)
    await db.flush()  # get lead.id before adding consents

    # ── 5. Persist Consents ───────────────────────────────────────────────────
    now = datetime.now(tz=timezone.utc)
    for consent_entry in payload.consents:
        consent = Consent(
            lead_id=lead.id,
            type=consent_entry.type,
            accepted=consent_entry.accepted,
            timestamp=now,
            policy_version=consent_entry.policy_version,
            ip_hash=ip_h,
        )
        db.add(consent)

    # ── 6. Record rate-limit attempt (success=False = counts toward window) ──────
    # For public_submission, EVERY submission counts toward the hourly cap,
    # regardless of outcome. The rate_limit module counts success=False rows.
    await record_attempt(
        db=db,
        email=None,
        ip=ip,
        attempt_type="public_submission",
        success=False,
    )

    await db.commit()
    await db.refresh(lead)

    # ── 7. Background email to lead ───────────────────────────────────────────
    lead_email = str(answers.email)
    lead_name = answers.full_name
    company = answers.company_name

    async def _send_lead_email():
        subject, body = triage_email_for_bucket(
            bucket, full_name=lead_name, company_name=company
        )
        await send_email(to=lead_email, subject=subject, body=body)
        logger.info("triage_email_sent", lead_id=lead.id, bucket=bucket)

    background_tasks.add_task(_send_lead_email)

    # ── 8. Notify consultant if auto_accept ───────────────────────────────────
    if bucket == "auto_accept" and settings.consultant_email:
        async def _notify_consultant():
            subject, body = triage_consultant_notification(
                full_name=lead_name,
                company_name=company,
                bucket=bucket,
                lead_id=lead.id,
            )
            await send_email(to=settings.consultant_email, subject=subject, body=body)
            logger.info("consultant_notified", lead_id=lead.id)

        background_tasks.add_task(_notify_consultant)

    logger.info(
        "triage_submitted",
        lead_id=lead.id,
        bucket=bucket,
        score=score_result.total_score,
    )

    return TriageResponse(
        lead_id=lead.id,
        bucket=bucket,
        message=_bucket_message(bucket),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_override_rules() -> list[dict] | None:
    """Extract override rules from loaded schema. Returns fallback if unavailable."""
    try:
        schema = schema_loader.get_root_schema()
        override_rules = schema.get("override_rules")
        if isinstance(override_rules, list) and override_rules:
            return override_rules
        if isinstance(override_rules, dict):
            rules = override_rules.get("rules")
            if rules and isinstance(rules, list):
                return rules
    except RuntimeError:
        pass

    # Fallback: hardcoded rules matching triage.yaml structure
    return [
        {
            "id": "regulated_urgent_force_accept",
            "condition": {
                "sector_in": ["salud", "legal", "finanzas"],
                "urgency_in": ["critica", "alta"],
                "min_score": 55,
            },
            "action": "force_bucket",
            "target_bucket": "auto_accept",
            "applies_only_upgrade": True,
        },
        {
            "id": "external_advocate_review",
            "condition": {
                "respondent_role": "consultor_externo",
                "commitment": "agendar",
            },
            "action": "force_bucket",
            "target_bucket": "review",
            "applies_only_upgrade": False,
            "set_flag": "external_advocate",
        },
    ]


def _bucket_message(bucket: str) -> str:
    messages = {
        "auto_accept": "¡Perfil excelente! Un consultor te contactará en 24-48 horas.",
        "review": "Tu perfil está en revisión. Te contactaremos en 2-3 días hábiles.",
        "cold_warm": "Perfil interesante. Te enviamos recursos y te reevaluamos en 4 meses.",
        "cold_cool": "Te enviamos un checklist para preparar tu madurez IA.",
        "reject_soft": "Gracias por tu interés. Te enviaremos contenido formativo.",
    }
    return messages.get(bucket, "Solicitud recibida.")
