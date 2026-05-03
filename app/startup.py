"""
app/startup — Lifecycle hooks wired to FastAPI's lifespan in webhook_service.py.

Runs at app start (after configure_logging) and cancels background loops on
shutdown. Three hooks:

  prune_login_attempts()       — one-time hygiene DELETE on startup
  resume_orphaned_assessments() — re-enqueues pending_review rows missing enrichment
  session_cleanup_loop()        — background task, prunes expired sessions every hour

Design references:
  - §0 A4: job registry is in-memory only; startup re-enqueue recovers durability
  - §0 A5: Phase A inline prune handles per-(email,ip) bounds; this catches the rest
  - Phase D tasks D-01, D-02, D-03
"""

import asyncio

import structlog
from sqlalchemy import select, text

from app.auth.sessions import prune_expired
from app.db.session import async_session_factory
from app.models.assessment import Assessment

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# TASK-D-01 — Global login_attempts hygiene sweep
# ---------------------------------------------------------------------------


async def prune_login_attempts() -> int:
    """
    Delete login_attempt rows older than 7 days (global, unscoped sweep).

    The inline prune in rate_limit.py handles per-(email, ip, attempt_type)
    bounds during normal operation. This sweep is a hygiene backstop that
    catches rows from IPs/emails that never re-appear (so inline prune never
    fires for them).

    Returns: count of rows deleted.
    """
    async with async_session_factory() as db:
        result = await db.execute(
            text(
                "DELETE FROM login_attempts "
                "WHERE attempted_at < datetime('now', '-7 days')"
            )
        )
        await db.commit()
        count: int = result.rowcount
    logger.info("login_attempts_pruned", count=count)
    return count


# ---------------------------------------------------------------------------
# TASK-D-02 — Startup re-enqueue for orphaned pending_review rows
# ---------------------------------------------------------------------------


async def resume_orphaned_assessments() -> int:
    """
    Re-enqueue enrichment_chain for assessments that were left half-processed.

    An assessment is "orphaned" if:
      - status == 'pending_review'  (was submitted but not yet approved)
      - llm_enriched_data IS NULL   (enrichment chain never completed)

    This happens when the process restarts mid-chain: the BackgroundTask was
    running in the old process's event loop, and it vanished on shutdown.
    The job_registry is in-memory only (design §0 A4), so there is no other
    recovery mechanism.

    Each job is spawned as asyncio.create_task() so startup returns immediately
    even when there are many orphans.

    Returns: count of orphaned assessments re-enqueued.
    """
    # Import here to avoid a circular import: startup.py imports runners.py,
    # runners.py imports from app.db.session — all fine, but runners imports
    # assessment model which triggers models/__init__.py. Lazy import keeps the
    # module graph clean and avoids any risk of import-order issues at startup.
    from app.jobs.runners import enrichment_chain  # noqa: PLC0415

    async with async_session_factory() as db:
        result = await db.execute(
            select(Assessment).where(
                Assessment.status == "pending_review",
                Assessment.llm_enriched_data.is_(None),
            )
        )
        orphans = result.scalars().all()
        ids = [str(a.id) for a in orphans]

    for assessment_id in ids:
        # auto_publish=False: they're already in pending_review; the consultant
        # will manually approve after reviewing the enriched data. We don't
        # want to bypass that review step just because the process restarted.
        asyncio.create_task(
            enrichment_chain(assessment_id, auto_publish=False),
            name=f"resume_orphan_{assessment_id[:8]}",
        )

    count = len(ids)
    logger.info("orphaned_assessments_resumed", count=count, ids=ids)
    return count


# ---------------------------------------------------------------------------
# TASK-D-03 — Background session cleanup loop
# ---------------------------------------------------------------------------


async def session_cleanup_loop() -> None:
    """
    Hourly background sweep of expired admin sessions.

    Runs forever until cancelled (on app shutdown via lifespan handler).
    Wraps the sweep body in try/except so a transient DB error does not
    kill the loop — it logs and retries on the next cycle.

    Calls prune_expired() from app/auth/sessions.py, which deletes all
    SessionRow records where expires_at < NOW() (including revoked ones).
    """
    logger.info("session_cleanup_loop_started")
    while True:
        try:
            async with async_session_factory() as db:
                count = await prune_expired(db)
                await db.commit()
                if count > 0:
                    logger.info("session_cleanup_pruned", count=count)
        except asyncio.CancelledError:
            # CancelledError must propagate — re-raise so the task exits cleanly.
            raise
        except Exception as exc:
            # Any other error: log and keep looping. A persistent error
            # (e.g. DB locked) produces one log line per hour, not a storm.
            logger.exception("session_cleanup_failed", error=str(exc))

        await asyncio.sleep(3600)
