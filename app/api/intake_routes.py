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
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import require_admin
from app.auth.rate_limit import check_rate_limit, record_attempt
from app.db.session import get_db
from app.email.sender import send_email
from app.models.block_analysis import BlockAnalysis
from app.models.consent import Consent
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.suggestion import Suggestion
from app.models.user import User
from app.services.ai_analysis.block_analyzer import BlockAnalyzer
from app.schemas.common import ApiException
from app.schemas.triage import TriagePayload, TriageResponse
from app.services.email.triage_emails import (
    triage_consultant_notification,
    triage_email_for_bucket,
)
from app.services.intake.session_service import (
    VALID_PRIMARY_AREAS,
    build_session_payload,
    mark_block_completed,
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


# ===========================================================================
# INTAKE CONSULTOR — endpoints autenticados (B5)
# ===========================================================================

# ---------------------------------------------------------------------------
# Pydantic schemas for intake
# ---------------------------------------------------------------------------

VALID_AREA_VALUES = list(VALID_PRIMARY_AREAS)


class AreaSelectionRequest(BaseModel):
    primary_area: str
    secondary_area: str | None = None
    areas_involved: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_area(self) -> "AreaSelectionRequest":
        if self.primary_area not in VALID_PRIMARY_AREAS:
            raise ValueError(
                f"primary_area must be one of: {sorted(VALID_PRIMARY_AREAS)}"
            )
        if self.primary_area == "cross_area_communication":
            if not self.areas_involved or len(self.areas_involved) < 2:
                raise ValueError(
                    "areas_involved requires at least 2 areas when primary_area is cross_area_communication"
                )
        return self


class AreaSelectionResponse(BaseModel):
    lead_id: str
    primary_area: str
    secondary_area: str | None = None
    areas_involved: list[str] = Field(default_factory=list)
    state: str


class BlockSubmitRequest(BaseModel):
    payload: dict


class BlockSubmitResponse(BaseModel):
    block_analysis_id: str
    status: str = "submitted"


class BlockPayloadResponse(BaseModel):
    block_id: str
    payload: dict
    status: str


class IntakeStateResponse(BaseModel):
    lead_id: str
    state: str
    primary_area: str | None = None
    secondary_area: str | None = None
    areas_involved: list[str] = Field(default_factory=list)
    blocks_completed: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_accepted_lead(db: AsyncSession, lead_id: str) -> Lead:
    """Load Lead, raise 404 if not found, 403 if not accepted."""
    stmt = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    if lead is None:
        raise ApiException(status_code=404, code="lead_not_found", detail=f"Lead {lead_id} not found.")
    if lead.status != "accepted":
        raise ApiException(
            status_code=403,
            code="lead_not_accepted",
            detail=f"Lead {lead_id} is not accepted (status={lead.status}).",
        )
    return lead


async def _get_or_create_session(db: AsyncSession, lead_id: str) -> IntakeSession:
    """Return existing IntakeSession or create a new not_started one."""
    stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        session = IntakeSession(
            lead_id=lead_id,
            primary_area="not_set",
            secondary_area=None,
            areas_involved=[],
            state="not_started",
            blocks_completed=[],
        )
        db.add(session)
        await db.flush()
    return session


# ---------------------------------------------------------------------------
# GET /api/intake/{lead_id}/schema
# ---------------------------------------------------------------------------

@router.get("/intake/{lead_id}/schema")
async def get_intake_schema(
    lead_id: str,
    area: str | None = Query(default=None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return CORE schema personalised by area.

    If area param is provided, block-2 is instantiated for that area.
    Otherwise, returns full schema with area selector.
    """
    await _get_accepted_lead(db, lead_id)

    try:
        try:
            schema_loader.get_schema_version()
        except RuntimeError:
            schema_loader.load_all()

        root = schema_loader.get_root_schema()
    except Exception as exc:
        logger.error("schema_unavailable", error=str(exc))
        raise HTTPException(status_code=503, detail="Schema not loaded")

    core = root.get("core", {})
    blocks_order = core.get("blocks_order", [])
    area_selector = core.get("area_selector", {})

    if area:
        # Build personalised response with blocks list
        variant = core.get("block_2_variants", {})
        b2_id = variant.get("full", "block-2-process-critical-full")

        # Instantiate blocks
        blocks_data = root.get("blocks", [])
        if not blocks_data:
            # Load blocks directly from schema files
            blocks_data = _load_core_blocks(blocks_order)

        return {
            "blocks_order": blocks_order,
            "area_selector": area_selector,
            "area": area,
            "blocks": blocks_data,
        }

    return {
        "blocks_order": blocks_order,
        "area_selector": area_selector,
    }


def _load_core_blocks(blocks_order: list[str]) -> list[dict]:
    """Load and return core block schemas."""
    import yaml
    from pathlib import Path
    schema_dir = Path(__file__).parents[2] / "schemas" / "questionnaire-v2" / "core"
    blocks = []
    for block_id in blocks_order:
        block_file = schema_dir / f"{block_id}.yaml"
        if block_file.exists():
            with block_file.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                blocks.append(data)
    return blocks


# ---------------------------------------------------------------------------
# POST /api/intake/{lead_id}/area-selection
# ---------------------------------------------------------------------------

@router.post("/intake/{lead_id}/area-selection")
async def post_area_selection(
    lead_id: str,
    body: AreaSelectionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AreaSelectionResponse:
    """
    Register primary_area + secondary_area + areas_involved for an intake session.

    Creates IntakeSession if it doesn't exist.
    Cross-area sessions: secondary_area is silently cleared.
    """
    await _get_accepted_lead(db, lead_id)
    session = await _get_or_create_session(db, lead_id)

    is_cross = body.primary_area == "cross_area_communication"

    session.primary_area = body.primary_area
    session.secondary_area = None if is_cross else body.secondary_area
    session.areas_involved = body.areas_involved if is_cross else []
    if session.state == "not_started":
        session.state = "in_progress"

    await db.commit()

    logger.info(
        "intake_area_selected",
        lead_id=lead_id,
        primary_area=body.primary_area,
        cross_area=is_cross,
    )

    return AreaSelectionResponse(
        lead_id=lead_id,
        primary_area=session.primary_area,
        secondary_area=session.secondary_area,
        areas_involved=session.areas_involved,
        state=session.state,
    )


# ---------------------------------------------------------------------------
# GET /api/intake/{lead_id}/state
# ---------------------------------------------------------------------------

@router.get("/intake/{lead_id}/state")
async def get_intake_state(
    lead_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> IntakeStateResponse:
    """Return current IntakeSession state for a lead."""
    await _get_accepted_lead(db, lead_id)
    session = await _get_or_create_session(db, lead_id)
    await db.commit()

    return IntakeStateResponse(
        lead_id=lead_id,
        state=session.state,
        primary_area=session.primary_area if session.primary_area != "not_set" else None,
        secondary_area=session.secondary_area,
        areas_involved=session.areas_involved or [],
        blocks_completed=session.blocks_completed or [],
    )


# ---------------------------------------------------------------------------
# POST /api/intake/{lead_id}/blocks/{block_id}/submit
# ---------------------------------------------------------------------------

@router.post("/intake/{lead_id}/blocks/{block_id}/submit", status_code=202)
async def submit_block(
    lead_id: str,
    block_id: str,
    body: BlockSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> BlockSubmitResponse:
    """
    Validate + persist block payload.

    Idempotent: re-submitting same block_id replaces previous BlockAnalysis.
    Auto-dispatches LLM analysis as BackgroundTask (T6.13).
    """
    await _get_accepted_lead(db, lead_id)
    session = await _get_or_create_session(db, lead_id)

    # Delete existing BlockAnalysis for this session+block (idempotency)
    existing_stmt = select(BlockAnalysis).where(
        BlockAnalysis.intake_session_id == session.id,
        BlockAnalysis.block_id == block_id,
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        await db.delete(existing)
        await db.flush()

    # Create new BlockAnalysis (status=pending_analysis, LLM will fill it)
    block_analysis = BlockAnalysis(
        intake_session_id=session.id,
        block_id=block_id,
        payload=body.payload,
        status="pending_analysis",
        llm_output=None,
        llm_model_used=None,
    )
    db.add(block_analysis)

    # Mark block as completed in session
    session.blocks_completed = mark_block_completed(
        session.blocks_completed or [], block_id
    )

    await db.commit()

    # Auto-dispatch LLM analysis (T6.13)
    ba_id = block_analysis.id

    async def _run_analysis():
        from app.db.session import async_session_factory  # noqa: PLC0415
        async with async_session_factory() as analysis_db:
            analyzer = BlockAnalyzer(db=analysis_db)
            await analyzer.analyze(block_analysis_id=ba_id, block_id=block_id)

    background_tasks.add_task(_run_analysis)

    logger.info(
        "block_submitted",
        lead_id=lead_id,
        block_id=block_id,
        block_analysis_id=block_analysis.id,
    )

    return BlockSubmitResponse(
        block_analysis_id=block_analysis.id,
        status="pending_analysis",
    )


# ---------------------------------------------------------------------------
# GET /api/intake/{lead_id}/blocks/{block_id}/payload
# ---------------------------------------------------------------------------

@router.get("/intake/{lead_id}/blocks/{block_id}/payload")
async def get_block_payload(
    lead_id: str,
    block_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> BlockPayloadResponse:
    """Return stored payload for a submitted block (auto-save retrieval)."""
    await _get_accepted_lead(db, lead_id)

    # Find session
    session_stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if session is None:
        raise ApiException(status_code=404, code="session_not_found", detail="No intake session found.")

    # Find block analysis
    ba_stmt = select(BlockAnalysis).where(
        BlockAnalysis.intake_session_id == session.id,
        BlockAnalysis.block_id == block_id,
    )
    ba_result = await db.execute(ba_stmt)
    block_analysis = ba_result.scalar_one_or_none()
    if block_analysis is None:
        raise ApiException(status_code=404, code="block_not_found", detail=f"No payload for block {block_id}.")

    return BlockPayloadResponse(
        block_id=block_id,
        payload=block_analysis.payload,
        status=block_analysis.status,
    )


# ===========================================================================
# ANALYSIS ENDPOINTS — B6
# ===========================================================================

class AnalyzeRequest(BaseModel):
    block_id: str


class AnalyzeResponse(BaseModel):
    block_analysis_id: str
    status: str


class AnalysisResponse(BaseModel):
    block_analysis_id: str
    status: str
    llm_output: dict | None = None
    suggestions: list[dict] = Field(default_factory=list)
    generated_at: str | None = None


class SuggestionActionRequest(BaseModel):
    action: Literal["done", "discarded", "irrelevant"]


class SuggestionResponse(BaseModel):
    id: str
    type: str
    text: str
    rationale: str | None = None
    confidence: float
    priority: str
    consultant_action: str


# ---------------------------------------------------------------------------
# POST /api/intake/{lead_id}/analyze  — manual re-trigger
# ---------------------------------------------------------------------------

@router.post("/intake/{lead_id}/analyze", status_code=202)
async def trigger_analyze(
    lead_id: str,
    body: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """
    Manually (re-)trigger LLM analysis for a specific block.

    Finds or creates a BlockAnalysis for the block, sets status=pending_analysis,
    and dispatches a BackgroundTask to run the LLM analysis.
    """
    await _get_accepted_lead(db, lead_id)

    session_stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="No intake session found for this lead.")

    # Find existing BlockAnalysis
    ba_stmt = select(BlockAnalysis).where(
        BlockAnalysis.intake_session_id == session.id,
        BlockAnalysis.block_id == body.block_id,
    )
    ba_result = await db.execute(ba_stmt)
    ba = ba_result.scalar_one_or_none()

    if ba is None:
        raise HTTPException(status_code=404, detail=f"No block analysis found for block_id={body.block_id}.")

    # Reset status to pending_analysis
    ba.status = "pending_analysis"
    ba.llm_output = None
    ba.error_message = None
    await db.commit()

    # Dispatch BackgroundTask
    ba_id = ba.id
    block_id = body.block_id

    async def _run_analysis():
        from app.db.session import async_session_factory  # noqa: PLC0415
        async with async_session_factory() as analysis_db:
            analyzer = BlockAnalyzer(db=analysis_db)
            await analyzer.analyze(block_analysis_id=ba_id, block_id=block_id)

    background_tasks.add_task(_run_analysis)

    logger.info("block_analysis_triggered", lead_id=lead_id, block_id=block_id, block_analysis_id=ba_id)

    return AnalyzeResponse(block_analysis_id=ba_id, status="pending_analysis")


# ---------------------------------------------------------------------------
# GET /api/intake/{lead_id}/blocks/{block_id}/analysis  — polling
# ---------------------------------------------------------------------------

@router.get("/intake/{lead_id}/blocks/{block_id}/analysis")
async def get_block_analysis(
    lead_id: str,
    block_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Return current analysis status + output for a block.

    Used for polling from frontend (refetchInterval 2s while pending_analysis).
    """
    await _get_accepted_lead(db, lead_id)

    session_stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="No intake session found for this lead.")

    ba_stmt = select(BlockAnalysis).where(
        BlockAnalysis.intake_session_id == session.id,
        BlockAnalysis.block_id == block_id,
    )
    ba_result = await db.execute(ba_stmt)
    ba = ba_result.scalar_one_or_none()
    if ba is None:
        raise HTTPException(status_code=404, detail=f"No analysis found for block_id={block_id}.")

    # Load suggestions if ready
    suggestions_data: list[dict] = []
    if ba.status == "ready":
        sug_stmt = select(Suggestion).where(Suggestion.block_analysis_id == ba.id)
        sug_result = await db.execute(sug_stmt)
        suggestions = sug_result.scalars().all()
        suggestions_data = [
            {
                "id": s.id,
                "type": s.type,
                "text": s.text,
                "rationale": s.rationale,
                "confidence": s.confidence,
                "priority": s.priority,
                "consultant_action": s.consultant_action,
            }
            for s in suggestions
        ]

    return AnalysisResponse(
        block_analysis_id=ba.id,
        status=ba.status,
        llm_output=ba.llm_output,
        suggestions=suggestions_data,
        generated_at=ba.generated_at.isoformat() if ba.generated_at else None,
    )


# ---------------------------------------------------------------------------
# POST /api/intake/{lead_id}/suggestions/{suggestion_id}/action
# ---------------------------------------------------------------------------

@router.post("/intake/{lead_id}/suggestions/{suggestion_id}/action")
async def suggestion_action(
    lead_id: str,
    suggestion_id: str,
    body: SuggestionActionRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    """
    Update consultant_action on a Suggestion.

    Validates the suggestion belongs to this lead's session.
    """
    await _get_accepted_lead(db, lead_id)

    session_stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="No intake session found for this lead.")

    # Fetch suggestion via join to verify ownership
    sug_stmt = (
        select(Suggestion)
        .join(BlockAnalysis, Suggestion.block_analysis_id == BlockAnalysis.id)
        .where(
            Suggestion.id == suggestion_id,
            BlockAnalysis.intake_session_id == session.id,
        )
    )
    sug_result = await db.execute(sug_stmt)
    suggestion = sug_result.scalar_one_or_none()

    if suggestion is None:
        raise HTTPException(
            status_code=404,
            detail=f"Suggestion {suggestion_id} not found for this lead.",
        )

    suggestion.consultant_action = body.action
    await db.commit()

    logger.info(
        "suggestion_action_recorded",
        lead_id=lead_id,
        suggestion_id=suggestion_id,
        action=body.action,
    )

    return SuggestionResponse(
        id=suggestion.id,
        type=suggestion.type,
        text=suggestion.text,
        rationale=suggestion.rationale,
        confidence=suggestion.confidence,
        priority=suggestion.priority,
        consultant_action=suggestion.consultant_action,
    )
