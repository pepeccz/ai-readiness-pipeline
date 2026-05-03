"""
app/jobs/runners — Async background runners for assessment enrichment jobs.

Each runner:
  1. Calls job_registry.mark_running(job_id)
  2. Opens its OWN AsyncSession via async_session_factory() (design §2.3 —
     the request-scoped session from get_db() is already closed when the
     BackgroundTask executes).
  3. Does its work (LLM call / scoring / PDF generation / email send).
  4. Persists results to the Assessment row and commits.
  5. Calls job_registry.mark_done(job_id) or mark_failed(job_id, error).

CRITICAL — JSON mutation rule (design §2.7):
  SQLAlchemy does NOT auto-detect in-place dict mutations on JSON columns.
  ALWAYS reassign: assessment.llm_enriched_data = {**current, **changes}
  Use flag_modified() as defence-in-depth after any reassignment of a JSON col.

CRITICAL — field_sources preservation (design §3.5):
  enrich_llm step already handles field_sources via preserve_human_fields arg.
  The runner passes assessment.field_sources directly to enrich_llm so the
  step itself skips human-edited fields. No double-filtering needed here.

CRITICAL — PDF lock (design §2.3):
  pdf_lock is an asyncio.Lock. Use "async with pdf_lock:" — not threading.Lock.
  generate_pdf is a blocking sync function; wrap with asyncio.to_thread().

Runners exposed:
  run_llm_enrichment_job(job_id, assessment_id)
  run_recommendation_enrichment_job(job_id, assessment_id)
  run_scoring_job(job_id, assessment_id)
  run_generate_pdf_job(job_id, assessment_id, draft=False)
  run_preview_pdf_job(job_id, assessment_id)     — alias for run_generate_pdf_job(draft=True)
  run_approve_and_send_job(job_id, assessment_id)
  run_resend_email_job(job_id, assessment_id)
  enrichment_chain(assessment_id, auto_publish)  — public form post-processing chain

Design reference: design §2.3, §3.3, §3.4, §3.5, §2.7.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import structlog
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import async_session_factory
from app.jobs.pdf_lock import pdf_lock
from app.jobs.registry import JobType, job_registry
from app.models.assessment import Assessment
from app.pipeline_steps import (
    enrich_llm,
    enrich_recommendations,
    generate_pdf,
    score,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Public base URL for building download links.
# TODO (Phase D): move to settings.public_base_url env var.
# For now: reads PUBLIC_BASE_URL env var, falls back to localhost (dev).
# ---------------------------------------------------------------------------
_PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8100").rstrip("/")


# ---------------------------------------------------------------------------
# Internal helper: build a rec dict from an Assessment ORM row
# ---------------------------------------------------------------------------


def _assessment_to_rec(assessment: Assessment) -> dict:
    """
    Reverse the rec → Assessment column unpacking, building a unified rec dict.

    Strategy:
      1. Start with all flat column values from the Assessment row.
      2. Merge llm_enriched_data blob (llm_* fields).
      3. Merge recommendation_data blob.
      4. Set assessment_id key so pipeline steps can log it.

    Flat columns that are None are still included (pipeline steps handle None).
    JSON blobs are shallow-merged — they contain only JSON-serialisable values.
    """
    rec: dict = {
        # Identity
        "assessment_id": str(assessment.id),
        "status": assessment.status,
        "auto_publish": assessment.auto_publish,
        # Timestamps (keep as ISO strings for pipeline compat)
        "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
        # Flat form fields
        "company_name": assessment.company_name,
        "sector": assessment.sector,
        "employee_range": assessment.employee_range,
        "revenue_range": assessment.revenue_range,
        "respondent_name_role": assessment.respondent_name_role,
        "respondent_email": assessment.respondent_email,
        "who_decides": assessment.who_decides,
        "budget": assessment.budget,
        "priority_text": assessment.priority_text,
        # Scoring flat columns
        "maturity_score": assessment.maturity_score,
        "maturity_level": assessment.maturity_level,
        "risk_score": assessment.risk_score,
        "risk_level": assessment.risk_level,
        "priority_score": assessment.priority_score,
        "priority_level": assessment.priority_level,
        # Sub-scores
        "pts_tools": assessment.pts_tools,
        "pts_automation": assessment.pts_automation,
        "pts_area_usage": assessment.pts_area_usage,
        "pts_governance": assessment.pts_governance,
        "pts_goal_clarity": assessment.pts_goal_clarity,
        "pts_data_risk": assessment.pts_data_risk,
        "pts_ai_personal_data": assessment.pts_ai_personal_data,
        "pts_dpa": assessment.pts_dpa,
        "pts_dpia": assessment.pts_dpia,
        "pts_automated_decisions": assessment.pts_automated_decisions,
        "pts_sector": assessment.pts_sector,
        "pts_incident": assessment.pts_incident,
    }

    # Merge form_data blob (raw form answers — provides context for LLM)
    if assessment.form_data:
        rec.update(assessment.form_data)

    # Merge LLM-enriched fields (llm_* keys)
    if assessment.llm_enriched_data:
        rec.update(assessment.llm_enriched_data)

    # Merge recommendation data
    if assessment.recommendation_data:
        rec.update(assessment.recommendation_data)

    return rec


# ---------------------------------------------------------------------------
# Score column helpers
# ---------------------------------------------------------------------------

_SCORE_COLUMNS = (
    "maturity_score",
    "maturity_level",
    "risk_score",
    "risk_level",
    "priority_score",
    "priority_level",
    "pts_tools",
    "pts_automation",
    "pts_area_usage",
    "pts_governance",
    "pts_goal_clarity",
    "pts_data_risk",
    "pts_ai_personal_data",
    "pts_dpa",
    "pts_dpia",
    "pts_automated_decisions",
    "pts_sector",
    "pts_incident",
)


# ---------------------------------------------------------------------------
# Runner: LLM enrichment
# TASK-B-11
# ---------------------------------------------------------------------------


async def run_llm_enrichment_job(job_id: str, assessment_id: str) -> None:
    """
    Run LLM enrichment in the background.

    Honors field_sources: enrich_llm() is passed assessment.field_sources so it
    skips fields already marked as 'human' (design §3.5).

    Persists the enriched llm_* fields back into llm_enriched_data blob.
    Does NOT overwrite human-edited flat fields.
    Sets last_edited_by_id = None to mark this as a system edit.
    """
    await job_registry.mark_running(job_id)
    logger.info("run_llm_enrichment_start", job_id=job_id, assessment_id=assessment_id)

    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                raise RuntimeError(f"Assessment {assessment_id} not found")

            rec = _assessment_to_rec(assessment)
            field_sources = assessment.field_sources or {}

            # enrich_llm is SYNC — wrap in to_thread so event loop stays free.
            # Pass field_sources so the step preserves human-edited fields.
            enriched_rec = await asyncio.to_thread(enrich_llm, rec, field_sources)

            # Extract only llm_* fields from the enriched rec for blob storage.
            # field_sources preservation was already handled inside enrich_llm.
            llm_fields = {
                k: v
                for k, v in enriched_rec.items()
                if k.startswith("llm_")
            }

            # Reassign blob — never mutate in place (SQLAlchemy JSON tracking).
            current_blob = assessment.llm_enriched_data or {}
            assessment.llm_enriched_data = {**current_blob, **llm_fields}
            flag_modified(assessment, "llm_enriched_data")

            # System edit — no human user triggered this.
            assessment.last_edited_by_id = None
            assessment.updated_at = datetime.now(tz=timezone.utc)

            await db.commit()

        await job_registry.mark_done(job_id)
        logger.info("run_llm_enrichment_done", job_id=job_id, assessment_id=assessment_id)

    except Exception as exc:
        logger.exception(
            "run_llm_enrichment_failed",
            job_id=job_id,
            assessment_id=assessment_id,
            error=str(exc),
        )
        await job_registry.mark_failed(job_id, str(exc))


# ---------------------------------------------------------------------------
# Runner: Recommendation enrichment
# TASK-B-12
# ---------------------------------------------------------------------------


async def run_recommendation_enrichment_job(job_id: str, assessment_id: str) -> None:
    """
    Run recommendation enrichment in the background.

    Persists results into recommendation_data blob.
    Also merges any new llm_* keys (tool_recommendations, followup_questions,
    ai_policy_draft, dpa_guidance) into llm_enriched_data for editor display.
    """
    await job_registry.mark_running(job_id)
    logger.info(
        "run_recommendation_enrichment_start",
        job_id=job_id,
        assessment_id=assessment_id,
    )

    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                raise RuntimeError(f"Assessment {assessment_id} not found")

            rec = _assessment_to_rec(assessment)

            # enrich_recommendations is SYNC — wrap in to_thread.
            enriched_rec = await asyncio.to_thread(enrich_recommendations, rec)

            # Recommendation-specific llm_* fields produced by this step:
            reco_llm_keys = {
                "llm_tool_recommendations",
                "llm_followup_questions",
                "llm_ai_policy_draft",
                "llm_dpa_guidance",
            }

            # Build recommendation_data blob from the new reco keys
            reco_blob: dict = {
                k: enriched_rec[k]
                for k in reco_llm_keys
                if k in enriched_rec
            }

            # Merge reco llm_* fields into llm_enriched_data as well
            # (editor displays all llm_* from llm_enriched_data)
            current_llm_blob = assessment.llm_enriched_data or {}
            assessment.llm_enriched_data = {**current_llm_blob, **reco_blob}
            flag_modified(assessment, "llm_enriched_data")

            # Store full reco output in recommendation_data blob
            assessment.recommendation_data = reco_blob
            flag_modified(assessment, "recommendation_data")

            assessment.last_edited_by_id = None
            assessment.updated_at = datetime.now(tz=timezone.utc)

            await db.commit()

        await job_registry.mark_done(job_id)
        logger.info(
            "run_recommendation_enrichment_done",
            job_id=job_id,
            assessment_id=assessment_id,
        )

    except Exception as exc:
        logger.exception(
            "run_recommendation_enrichment_failed",
            job_id=job_id,
            assessment_id=assessment_id,
            error=str(exc),
        )
        await job_registry.mark_failed(job_id, str(exc))


# ---------------------------------------------------------------------------
# Runner: Scoring
# TASK-B-13
# ---------------------------------------------------------------------------


async def run_scoring_job(job_id: str, assessment_id: str) -> None:
    """
    Run scoring in the background.

    score() is CPU-only (no I/O) but we still wrap it in to_thread for
    consistency and to keep the event loop unblocked on heavy data.

    Persists the flat score columns (maturity_score, risk_score, etc.) and
    all pts_* sub-scores. Scoring is deterministic from its inputs, so
    re-runs always overwrite previous score values.
    """
    await job_registry.mark_running(job_id)
    logger.info("run_scoring_start", job_id=job_id, assessment_id=assessment_id)

    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                raise RuntimeError(f"Assessment {assessment_id} not found")

            rec = _assessment_to_rec(assessment)

            # score() is SYNC — wrap in to_thread
            scored_rec = await asyncio.to_thread(score, rec)

            # Write flat score columns directly to the ORM row
            for col in _SCORE_COLUMNS:
                if col in scored_rec:
                    setattr(assessment, col, scored_rec[col])

            assessment.last_edited_by_id = None
            assessment.updated_at = datetime.now(tz=timezone.utc)

            await db.commit()

        await job_registry.mark_done(job_id)
        logger.info(
            "run_scoring_done",
            job_id=job_id,
            assessment_id=assessment_id,
            maturity_score=scored_rec.get("maturity_score"),
        )

    except Exception as exc:
        logger.exception(
            "run_scoring_failed",
            job_id=job_id,
            assessment_id=assessment_id,
            error=str(exc),
        )
        await job_registry.mark_failed(job_id, str(exc))


# ---------------------------------------------------------------------------
# Runner: PDF generation (production + draft)
# TASK-B-14 (generate-pdf) / TASK-B-15 (preview-pdf)
# ---------------------------------------------------------------------------


async def run_generate_pdf_job(
    job_id: str,
    assessment_id: str,
    draft: bool = False,
) -> None:
    """
    Generate a PDF report for an assessment.

    Acquires pdf_lock before calling generate_pdf() to serialise LibreOffice
    invocations (only one at a time per process — design §2.3).

    Args:
        job_id:        Registry job ID (for status tracking).
        assessment_id: UUID string of the assessment row.
        draft:         When True, produces a watermarked preview PDF.
                       Draft PDFs do NOT update assessment.pdf_path — they
                       are ephemeral and stored with a "_draft_" prefix
                       (generate_pdf.py handles the filename).

    On success (production only, draft=False):
        Updates pdf_path and pdf_generated_at on the assessment row.

    On failure:
        Marks job as failed. pdf_path is left unchanged (remains null for
        first generation, unchanged for re-runs — design §3.4).
    """
    await job_registry.mark_running(job_id)
    logger.info(
        "run_generate_pdf_start",
        job_id=job_id,
        assessment_id=assessment_id,
        draft=draft,
    )

    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                raise RuntimeError(f"Assessment {assessment_id} not found")

            rec = _assessment_to_rec(assessment)

            # Acquire lock BEFORE to_thread — the lock guards the LibreOffice
            # process, not just the Python call. generate_pdf itself is sync.
            async with pdf_lock:
                pdf_path: Path = await asyncio.to_thread(generate_pdf, rec, draft)

            if not draft:
                # Production PDF: persist path and timestamp
                assessment.pdf_path = str(pdf_path)
                assessment.pdf_generated_at = datetime.now(tz=timezone.utc)
                assessment.updated_at = datetime.now(tz=timezone.utc)
                await db.commit()
            # Draft: no DB update — file is ephemeral (short-lived signed URL)

        await job_registry.mark_done(job_id)
        logger.info(
            "run_generate_pdf_done",
            job_id=job_id,
            assessment_id=assessment_id,
            draft=draft,
            pdf_path=str(pdf_path),
        )

    except Exception as exc:
        logger.exception(
            "run_generate_pdf_failed",
            job_id=job_id,
            assessment_id=assessment_id,
            draft=draft,
            error=str(exc),
        )
        await job_registry.mark_failed(job_id, str(exc))


async def run_preview_pdf_job(job_id: str, assessment_id: str) -> None:
    """Alias for run_generate_pdf_job with draft=True (watermarked preview)."""
    await run_generate_pdf_job(job_id, assessment_id, draft=True)


# ---------------------------------------------------------------------------
# Runner: Approve and send (PDF + email + status transition)
# BONUS — design §3.4
# ---------------------------------------------------------------------------


async def run_approve_and_send_job(job_id: str, assessment_id: str) -> None:
    """
    Approve an assessment and deliver the report to the client.

    Sequence (design §3.4 + §0 A3):
      1. Generate production PDF (acquires pdf_lock)
      2. UPDATE pdf_path, pdf_generated_at, status='approved' — COMMIT
         (PDF success = approval criterion; email failure does not roll back)
      3. Build signed download URL (7-day TTL from settings)
      4. Compose client email via client_report_email()
      5. Send email — update email_status='sent'/'failed' — COMMIT

    Email failure does NOT reverse the approval. Admin UI surfaces the
    'failed' email_status with a "Reenviar email" button.
    """
    await job_registry.mark_running(job_id)
    logger.info(
        "run_approve_and_send_start",
        job_id=job_id,
        assessment_id=assessment_id,
    )

    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                raise RuntimeError(f"Assessment {assessment_id} not found")

            rec = _assessment_to_rec(assessment)
            company_name = assessment.company_name
            client_email = assessment.respondent_email

            # ── Step 1: Generate PDF ────────────────────────────────────────
            async with pdf_lock:
                pdf_path: Path = await asyncio.to_thread(generate_pdf, rec, False)

            # ── Step 2: Persist PDF + approve (commit before email attempt) ─
            assessment.pdf_path = str(pdf_path)
            assessment.pdf_generated_at = datetime.now(tz=timezone.utc)
            assessment.status = "approved"
            assessment.updated_at = datetime.now(tz=timezone.utc)
            await db.commit()

            logger.info(
                "approve_and_send_pdf_done",
                job_id=job_id,
                assessment_id=assessment_id,
                pdf_path=str(pdf_path),
            )

            # ── Step 3: Build signed URL ───────────────────────────────────
            from app.signed_urls import sign  # noqa: PLC0415
            from config import settings  # noqa: PLC0415

            ttl_seconds = settings.signed_url_ttl_hours * 3600
            token = sign(assessment_id, ttl_seconds)
            download_url = (
                f"{_PUBLIC_BASE_URL}/api/assessment/{assessment_id}/download"
                f"?token={token}"
            )

            # ── Step 4 + 5: Compose and send email ─────────────────────────
            from app.email.templates import client_report_email  # noqa: PLC0415
            from app.email.sender import send_email  # noqa: PLC0415

            subject, body = client_report_email(company_name, download_url)
            email_success = await send_email(client_email, subject, body)

            # ── Step 6: Persist email outcome ─────────────────────────────
            now = datetime.now(tz=timezone.utc)
            if email_success:
                assessment.email_status = "sent"
                assessment.email_sent_at = now
                assessment.email_error = None
            else:
                assessment.email_status = "failed"
                assessment.email_error = "SMTP delivery failed — check logs"

            assessment.updated_at = now
            await db.commit()

        await job_registry.mark_done(job_id)
        logger.info(
            "run_approve_and_send_done",
            job_id=job_id,
            assessment_id=assessment_id,
            email_success=email_success,
        )

    except Exception as exc:
        logger.exception(
            "run_approve_and_send_failed",
            job_id=job_id,
            assessment_id=assessment_id,
            error=str(exc),
        )
        await job_registry.mark_failed(job_id, str(exc))


# ---------------------------------------------------------------------------
# Runner: Resend email (retry after previous failure)
# BONUS
# ---------------------------------------------------------------------------


async def run_resend_email_job(job_id: str, assessment_id: str) -> None:
    """
    Retry sending the client email for an assessment that already has a PDF.

    Verifies that pdf_path is set (cannot resend without a PDF).
    Re-signs the URL (fresh TTL — old token may have expired).
    Updates email_status / email_sent_at / email_error.
    """
    await job_registry.mark_running(job_id)
    logger.info(
        "run_resend_email_start",
        job_id=job_id,
        assessment_id=assessment_id,
    )

    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                raise RuntimeError(f"Assessment {assessment_id} not found")

            if not assessment.pdf_path:
                raise RuntimeError(
                    "Cannot resend email: no PDF has been generated for this assessment. "
                    "Run generate-pdf first."
                )

            if not assessment.respondent_email:
                raise RuntimeError(
                    "Cannot resend email: no respondent_email set on assessment."
                )

            company_name = assessment.company_name
            client_email = assessment.respondent_email

            # ── Build fresh signed URL ─────────────────────────────────────
            from app.signed_urls import sign  # noqa: PLC0415
            from config import settings  # noqa: PLC0415

            ttl_seconds = settings.signed_url_ttl_hours * 3600
            token = sign(assessment_id, ttl_seconds)
            download_url = (
                f"{_PUBLIC_BASE_URL}/api/assessment/{assessment_id}/download"
                f"?token={token}"
            )

            # ── Compose and send ───────────────────────────────────────────
            from app.email.templates import client_report_email  # noqa: PLC0415
            from app.email.sender import send_email  # noqa: PLC0415

            subject, body = client_report_email(company_name, download_url)
            email_success = await send_email(client_email, subject, body)

            # ── Persist outcome ────────────────────────────────────────────
            now = datetime.now(tz=timezone.utc)
            if email_success:
                assessment.email_status = "sent"
                assessment.email_sent_at = now
                assessment.email_error = None
            else:
                assessment.email_status = "failed"
                assessment.email_error = "SMTP delivery failed on resend — check logs"

            assessment.updated_at = now
            await db.commit()

        await job_registry.mark_done(job_id)
        logger.info(
            "run_resend_email_done",
            job_id=job_id,
            assessment_id=assessment_id,
            email_success=email_success,
        )

    except Exception as exc:
        logger.exception(
            "run_resend_email_failed",
            job_id=job_id,
            assessment_id=assessment_id,
            error=str(exc),
        )
        await job_registry.mark_failed(job_id, str(exc))


# ---------------------------------------------------------------------------
# Enrichment chain — used by the public form submission flow (Phase C)
# design §3.2 / §3.3
# ---------------------------------------------------------------------------


async def enrichment_chain(assessment_id: str, auto_publish: bool) -> None:
    """
    Full enrichment chain for a freshly submitted assessment.

    Called as a BackgroundTask from the public form endpoint (Phase C).
    No job_id — this is a fire-and-forget chain, not a registry job.
    (Each individual step creates its own registry job for the admin UI.)

    Sequence:
      enrich_llm → enrich_recommendations → score
      If auto_publish=True: generate_pdf → send email → status=approved

    If auto_publish=False: status stays 'pending_review' after scoring.
    """
    logger.info(
        "enrichment_chain_start",
        assessment_id=assessment_id,
        auto_publish=auto_publish,
    )

    # Step 1: LLM enrichment
    llm_job = await job_registry.create(JobType.enrich_llm, assessment_id)
    await run_llm_enrichment_job(llm_job.id, assessment_id)

    # Step 2: Recommendation enrichment
    reco_job = await job_registry.create(JobType.enrich_recommendations, assessment_id)
    await run_recommendation_enrichment_job(reco_job.id, assessment_id)

    # Step 3: Scoring
    score_job = await job_registry.create(JobType.score, assessment_id)
    await run_scoring_job(score_job.id, assessment_id)

    if not auto_publish:
        logger.info(
            "enrichment_chain_done_pending_review",
            assessment_id=assessment_id,
        )
        return

    # auto_publish=True: generate PDF + send email + set approved
    pdf_job = await job_registry.create(JobType.generate_pdf, assessment_id)
    await run_generate_pdf_job(pdf_job.id, assessment_id, draft=False)

    if pdf_job.status.value != "done":
        logger.error(
            "enrichment_chain_pdf_failed_skip_email",
            assessment_id=assessment_id,
            pdf_job_id=pdf_job.id,
        )
        return

    # Email + approve are handled together in approve_and_send — but since the
    # PDF is already done, we do inline email + approve here to avoid a second
    # PDF generation in run_approve_and_send_job.
    try:
        async with async_session_factory() as db:
            assessment = await db.get(Assessment, UUID(assessment_id))
            if assessment is None:
                return

            from app.signed_urls import sign  # noqa: PLC0415
            from config import settings  # noqa: PLC0415
            from app.email.templates import client_report_email  # noqa: PLC0415
            from app.email.sender import send_email  # noqa: PLC0415

            if assessment.respondent_email:
                ttl_seconds = settings.signed_url_ttl_hours * 3600
                token = sign(assessment_id, ttl_seconds)
                download_url = (
                    f"{_PUBLIC_BASE_URL}/api/assessment/{assessment_id}/download"
                    f"?token={token}"
                )
                subject, body = client_report_email(assessment.company_name, download_url)
                email_success = await send_email(assessment.respondent_email, subject, body)
            else:
                email_success = False

            now = datetime.now(tz=timezone.utc)
            assessment.status = "approved"
            assessment.updated_at = now
            if email_success:
                assessment.email_status = "sent"
                assessment.email_sent_at = now
                assessment.email_error = None
            else:
                assessment.email_status = "failed"
                assessment.email_error = "No respondent_email or SMTP failure"

            await db.commit()

        logger.info(
            "enrichment_chain_done_approved",
            assessment_id=assessment_id,
            email_success=email_success,
        )

    except Exception as exc:
        logger.exception(
            "enrichment_chain_auto_publish_failed",
            assessment_id=assessment_id,
            error=str(exc),
        )
