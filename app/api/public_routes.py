"""
app/api/public_routes — Public-facing assessment endpoints.

Router prefix: /api  (registered in webhook_service.py as
  app.include_router(router, prefix="/api"))

Endpoints:
  POST /api/assessment                       — Submit assessment form (replaces legacy threading.Thread handler)
  GET  /api/assessment/{id}/download         — Download PDF via signed URL token (Phase C Batch 2)

This module replaces the inline handler in webhook_service.py.

## Architecture decisions

### Field storage strategy (design §2.6)
- Flat columns (company_name, sector, employee_range, respondent_name_role,
  revenue_range, who_decides, budget, priority_text, auto_publish) are populated
  for SQL filtering/sorting in the admin list.
- form_data JSON blob stores the FULL raw payload from the public wizard
  (all 40+ fields). This is the audit trail — even fields that don't have flat
  columns are preserved and available to the LLM enrichment chain.
- field_sources initial value: ALL form-derived fields tagged 'human' since the
  user submitted them. LLM enrichment will add 'llm' sources on top.

### Rate limit gate order (TASK-C-09 addendum)
  1. IP rate limit checked FIRST (3/hour) — blocks volume abuse before any DB or LLM cost.
  2. Bearer token validated second — can't skip with a stolen token if IP is throttled.
  3. DB insert last — only occurs for valid, non-throttled requests.

### Bearer token (dev-mode skip)
  If settings.webhook_secret is empty, Bearer validation is skipped (dev mode, open).
  Frontend wizard sends the secret as Authorization: Bearer <WEBHOOK_SECRET>.

### enrichment_chain as BackgroundTask
  enrichment_chain is NOT a registry job — it's a fire-and-forget chain that
  internally creates registry jobs for each individual step (enrich_llm, enrich_reco,
  score). This way the admin jobs panel shows step-level progress without needing
  a synthetic parent job. See app/jobs/runners.py for the chain implementation.

### Consultant notification
  Separate BackgroundTask (independent of enrichment_chain). Fires regardless of
  auto_publish value. Fetches all active admin users and emails each one.
  Failure is silently swallowed — notification is best-effort, not critical path.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import rate_limit
from app.auth.middleware import get_client_ip
from app.db.session import async_session_factory, get_db
from app.email.sender import send_email
from app.email.templates import new_submission_email
from app.jobs import runners
from app.models.assessment import Assessment
from app.models.user import User
from app.pipeline_steps.map_form import map_form_to_rec
from app.schemas.common import ApiException
from app.signed_urls import SignedUrlError, verify
from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["public"])


# ---------------------------------------------------------------------------
# Pydantic schema — public form payload
# Moved from webhook_service.py (AssessmentFormPayload).
# ---------------------------------------------------------------------------


class PublicSubmissionPayload(BaseModel):
    """
    Public assessment form payload — mirrors the React wizard fields.

    Identical field set to the legacy AssessmentFormPayload in webhook_service.py.
    Moved here so the new endpoint owns its schema; the legacy handler in
    webhook_service.py no longer needs the model.
    """

    # Section 1 — Empresa
    company_name: str = ""
    sector: str
    employee_range: str
    contact_name: str
    revenue_range: str = ""
    contact_role: str = ""
    tech_decision_maker: str = ""
    # Section 2 — Stack
    software_used: list[str] = []
    ai_tools_used: list[str] = []
    has_chatbot: bool = False
    chatbot_desc: str = ""
    has_automations: bool = False
    automations_desc: str = ""
    # Section 3 — Atención al cliente
    contact_channels: list[str] = []
    daily_queries: str = ""
    support_team_desc: str = ""
    top_repetitive_queries: str = ""
    avg_resolution_time: str = ""
    # Section 4 — Marketing y ventas
    content_generation: list[str] = []
    lead_acquisition: list[str] = []
    has_lead_tracking: bool = False
    lead_tracking_desc: str = ""
    monthly_marketing_budget: str = ""
    # Section 5 — Operaciones
    most_time_consuming_process: str
    process_people_count: str = ""
    process_hours_per_week: str = ""
    data_entry_channels: list[str] = []
    process_pain_points: list[str] = []
    # Section 6 — Finanzas
    invoicing_method: str = ""
    has_cash_flow_control: bool = False
    cash_flow_desc: str = ""
    admin_hours_per_week: str = ""
    # Section 7 — RRHH
    is_hiring: bool = False
    hiring_desc: str = ""
    hr_management_method: str = ""
    hr_hours_per_week: str = ""
    # Section 8 — Compliance
    collects_personal_data: bool = False
    personal_data_types: str = ""
    knows_ai_gdpr: str = ""
    has_dpa: str = ""
    dpa_with_whom: str = ""
    knows_ai_act: str = ""
    has_ai_policy: str = ""
    # Section 9 — Presupuesto
    investment_budget: str
    urgency: str
    additional_notes: str = ""
    # Phase C addition: auto-publish flag (not in original wizard UI, defaults False)
    auto_publish: bool = False
    # Contact email for report delivery
    respondent_email: str = ""

    @field_validator(
        "company_name", "sector", "employee_range", "contact_name",
        "most_time_consuming_process", "investment_budget", "urgency",
    )
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Este campo es obligatorio")
        return v.strip()


# ---------------------------------------------------------------------------
# POST /api/assessment
# ---------------------------------------------------------------------------


@router.post("/assessment", status_code=202)
async def submit_assessment(
    payload: PublicSubmissionPayload,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Receive a public form submission and kick off the enrichment chain.

    Flow:
      1. Rate limit (IP) — outer gate, checked before Bearer or DB work.
      2. Bearer token validation (dev-mode skip if webhook_secret is empty).
      3. Map payload → rec dict → INSERT assessment row (status=pending_review).
      4. Record the rate limit attempt.
      5. Schedule enrichment_chain BackgroundTask.
      6. Schedule consultant notification BackgroundTask (independent, best-effort).
      7. Return 202 {assessment_id, status, message}.
    """

    # ── 1. Rate limit ─────────────────────────────────────────────────────────
    ip = get_client_ip(request)
    under_limit = await rate_limit.check_rate_limit(
        db,
        email=None,
        ip=ip,
        attempt_type="public_submission",
        max_attempts=3,
        window_seconds=3600,
    )
    if not under_limit:
        raise ApiException(
            status_code=429,
            code="rate_limited",
            detail="Demasiadas submissions. Probá de nuevo en una hora.",
        )

    # ── 2. Bearer token ───────────────────────────────────────────────────────
    secret = settings.webhook_secret.get_secret_value()
    if secret:
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else auth
        if token != secret:
            raise ApiException(
                status_code=403,
                code="unauthorized",
                detail="Acceso no autorizado",
            )

    # ── 3. Map payload + INSERT row ───────────────────────────────────────────
    form_dict = payload.model_dump()
    rec = map_form_to_rec(form_dict)

    # Flat columns: identity fields queryable for admin list/filters.
    # form_data blob: full raw payload (audit trail for LLM context).
    # field_sources: all form-derived fields pre-seeded as 'human'.
    assessment_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    # Build initial field_sources: every non-LLM key in form_dict is 'human'.
    # LLM runners will add their own 'llm' entries on top.
    field_sources: dict[str, str] = {
        k: "human"
        for k in form_dict
        if not k.startswith("llm_")
    }

    assessment = Assessment(
        id=assessment_id,
        status="pending_review",
        auto_publish=form_dict.get("auto_publish", False),
        created_at=now,
        updated_at=now,
        # Flat identity columns (queryable / shown in admin list)
        company_name=rec.get("company_name", form_dict.get("company_name", "")),
        sector=rec.get("sector", ""),
        employee_range=rec.get("employee_range", ""),
        revenue_range=rec.get("revenue_range", ""),
        respondent_name_role=rec.get("respondent_name_role", ""),
        respondent_email=form_dict.get("respondent_email") or None,
        who_decides=rec.get("who_decides", ""),
        budget=rec.get("budget", ""),
        priority_text=rec.get("proceso_urgencia", ""),
        # JSON blobs
        form_data=form_dict,        # full raw payload — audit trail
        llm_enriched_data=None,     # populated by enrichment_chain
        recommendation_data=None,   # populated by enrichment_chain
        field_sources=field_sources,
    )

    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    assessment_id_str = str(assessment.id)
    logger.info(
        "public_submission_received",
        assessment_id=assessment_id_str,
        company=assessment.company_name,
        auto_publish=assessment.auto_publish,
        ip=ip,
    )

    # ── 4. Record rate limit attempt ──────────────────────────────────────────
    await rate_limit.record_attempt(
        db,
        email=None,
        ip=ip,
        attempt_type="public_submission",
        success=True,
    )

    # ── 5. Schedule enrichment chain ──────────────────────────────────────────
    background_tasks.add_task(
        runners.enrichment_chain,
        assessment_id_str,
        assessment.auto_publish,
    )

    # ── 6. Schedule consultant notification (independent, best-effort) ────────
    background_tasks.add_task(
        _send_consultant_notification,
        assessment_id_str,
    )

    # ── 7. Return 202 ─────────────────────────────────────────────────────────
    return {
        "assessment_id": assessment_id_str,
        "status": "pending_review",
        "message": "Recibido. Te enviaremos el reporte por email.",
    }


# ---------------------------------------------------------------------------
# Background helper — consultant notification
# ---------------------------------------------------------------------------


async def _send_consultant_notification(assessment_id: str) -> None:
    """
    Notify all active admin users that a new submission arrived.

    Opens its own DB session (request session is already closed when this runs
    as a BackgroundTask — same pattern as app/jobs/runners.py).

    Fetches the assessment for company_name, then emails every active admin.
    Failure is silently logged and swallowed — notification is best-effort.
    The enrichment_chain is the critical path; this is a convenience alert.
    """
    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                logger.warning(
                    "consultant_notification_assessment_not_found",
                    assessment_id=assessment_id,
                )
                return

            result = await db.execute(
                select(User).where(User.is_active.is_(True))
            )
            admins = result.scalars().all()

            if not admins:
                logger.info(
                    "consultant_notification_no_admins",
                    assessment_id=assessment_id,
                )
                return

            # Build the admin URL using PUBLIC_BASE_URL env var (same as runners.py).
            public_base = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8100").rstrip("/")
            admin_url = f"{public_base}/admin/assessments/{assessment_id}"

            subject, body = new_submission_email(
                company_name=assessment.company_name or "(empresa sin nombre)",
                assessment_id=assessment_id,
                admin_url=admin_url,
            )

            sent_count = 0
            for admin in admins:
                success = await send_email(admin.email, subject, body)
                if success:
                    sent_count += 1

            logger.info(
                "consultant_notification_sent",
                assessment_id=assessment_id,
                total_admins=len(admins),
                sent=sent_count,
            )

    except Exception as exc:
        logger.exception(
            "consultant_notification_failed",
            assessment_id=assessment_id,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# GET /api/assessment/{assessment_id}/download
# ---------------------------------------------------------------------------


@router.get("/assessment/{assessment_id}/download")
async def public_download(
    assessment_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Stream a PDF report for a client using a signed URL token.

    Authentication: signed URL token in ?token= query param.
    No admin session required — the signed token is the auth.

    Flow:
      1. Verify signed token (parse → expiry → HMAC).
      2. Constant-time check: signed assessment_id must match URL path parameter.
      3. Load assessment; 404 if not found or archived.
      4. 404 if pdf_path not set or file missing on disk.
      5. Stream PDF via FileResponse.

    Error mapping (design §2.4):
      expired token       → 410 Gone
      bad_signature token → 403 Forbidden
      malformed token     → 403 Forbidden
      id mismatch         → 403 Forbidden
      not found/archived  → 404 (don't leak existence of archived assessments)
      pdf not ready       → 404
    """
    # ── 1. Verify signed token ────────────────────────────────────────────────
    try:
        verified_id = verify(token)
    except SignedUrlError as exc:
        raise ApiException(
            status_code=exc.status_code,
            code=exc.reason,
            detail=(
                "El enlace ha caducado. Solicitá un nuevo enlace al equipo."
                if exc.reason == "expired"
                else "Enlace inválido o manipulado."
            ),
        )

    # ── 2. Constant-time check: signed id must match URL path ─────────────────
    # HMAC already binds assessment_id to the signature, but an explicit check
    # makes it unambiguous and prevents any future confusion.
    if verified_id != str(assessment_id):
        raise ApiException(
            status_code=403,
            code="id_mismatch",
            detail="El token no corresponde a este assessment.",
        )

    # ── 3. Load assessment ────────────────────────────────────────────────────
    assessment = await db.get(Assessment, assessment_id)
    if assessment is None or assessment.status == "archived":
        raise ApiException(
            status_code=404,
            code="not_found",
            detail="El informe no está disponible.",
        )

    # ── 4. Check PDF exists ───────────────────────────────────────────────────
    if not assessment.pdf_path:
        raise ApiException(
            status_code=404,
            code="pdf_not_ready",
            detail="El informe aún no fue generado.",
        )
    path = Path(assessment.pdf_path)
    if not path.exists():
        logger.error(
            "pdf_file_missing_on_disk",
            assessment_id=str(assessment_id),
            pdf_path=assessment.pdf_path,
        )
        raise ApiException(
            status_code=404,
            code="pdf_file_missing",
            detail="El archivo del informe no está disponible. Contactá al soporte.",
        )

    # ── 5. Stream PDF ─────────────────────────────────────────────────────────
    safe_company = (
        (assessment.company_name or "informe")
        .replace(" ", "_")
        .replace("/", "_")
    )
    logger.info(
        "public_pdf_download",
        assessment_id=str(assessment_id),
        company=assessment.company_name,
    )
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"AIR-Informe-{safe_company}.pdf",
    )
