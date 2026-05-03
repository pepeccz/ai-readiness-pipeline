"""
app/jobs/registry — In-memory job registry singleton.

IMPORTANT: Process-local. Lost on restart by design (see design §0 A4).
Jobs in 'running' status at process restart become orphans and are never
resurected. Phase D adds a startup re-enqueue for pending_review rows with
llm_enriched_data IS NULL, which covers the only durability case that matters.
Job listing is best-effort UX, not a system of record.

Ring buffer: each assessment keeps at most _max_per_assessment (50) job IDs.
When the 51st job arrives, the oldest job ID is dropped from the index (the
JobRecord itself is also removed from _jobs to avoid unbounded growth).

Thread safety: all mutations hold self._lock (asyncio.Lock). All public
methods are async and acquire the lock before touching shared state.

Design reference: design §2.3.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────────────


class JobStatus(str, Enum):
    """Job lifecycle states."""

    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class JobType(str, Enum):
    """Job types supported by the registry."""

    enrich_llm = "enrich_llm"
    enrich_recommendations = "enrich_recommendations"
    score = "score"
    generate_pdf = "generate_pdf"
    preview_pdf = "preview_pdf"
    approve_and_send = "approve_and_send"
    public_submission = "public_submission"
    resend_email = "resend_email"


# ── JobRecord dataclass ────────────────────────────────────────────────────────


@dataclass
class JobRecord:
    """Single job record. Stored in the in-memory registry by job_id."""

    id: str                              # uuid4 hex
    type: JobType
    assessment_id: str
    status: JobStatus = JobStatus.pending
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


# ── JobRegistry ────────────────────────────────────────────────────────────────


class JobRegistry:
    """
    In-memory registry of background jobs.

    Process-local — all state is lost on restart. This is intentional (design §0 A4).

    Internal structure:
      _jobs            dict[job_id → JobRecord]
      _by_assessment   dict[assessment_id → list[job_id]]  (insertion order, oldest first)

    Ring buffer per assessment: when the list exceeds _max_per_assessment, the
    oldest job_id is evicted from both _by_assessment and _jobs.

    All methods acquire _lock (asyncio.Lock) before touching shared state.
    Do NOT call methods from sync context — they are all async.
    """

    _max_per_assessment: int = 50

    def __init__(self) -> None:
        self._lock: asyncio.Lock = asyncio.Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._by_assessment: dict[str, list[str]] = {}

    # ── Mutating methods ───────────────────────────────────────────────────────

    async def create(self, type: JobType, assessment_id: str) -> JobRecord:
        """
        Create a new job in 'pending' state and register it.

        Enforces the ring buffer: if the assessment already has
        _max_per_assessment jobs, the oldest is dropped before adding the new one.

        Returns the new JobRecord (status=pending, no timestamps yet).
        """
        job = JobRecord(
            id=uuid4().hex,
            type=type,
            assessment_id=assessment_id,
            status=JobStatus.pending,
        )

        async with self._lock:
            self._jobs[job.id] = job

            bucket = self._by_assessment.setdefault(assessment_id, [])
            bucket.append(job.id)

            # Enforce ring buffer — evict oldest if over the cap
            while len(bucket) > self._max_per_assessment:
                evicted_id = bucket.pop(0)
                self._jobs.pop(evicted_id, None)
                logger.debug(
                    "job_registry_evicted",
                    evicted_job_id=evicted_id,
                    assessment_id=assessment_id,
                )

        logger.info(
            "job_created",
            job_id=job.id,
            job_type=type.value,
            assessment_id=assessment_id,
        )
        return job

    async def mark_running(self, job_id: str) -> None:
        """Transition job to 'running' and record started_at."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                logger.warning("job_not_found_mark_running", job_id=job_id)
                return
            job.status = JobStatus.running
            job.started_at = datetime.now(tz=timezone.utc)

        logger.info("job_running", job_id=job_id)

    async def mark_done(self, job_id: str) -> None:
        """Transition job to 'done' and record finished_at."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                logger.warning("job_not_found_mark_done", job_id=job_id)
                return
            job.status = JobStatus.done
            job.finished_at = datetime.now(tz=timezone.utc)

        logger.info("job_done", job_id=job_id)

    async def mark_failed(self, job_id: str, error: str) -> None:
        """Transition job to 'failed', record finished_at and error message."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                logger.warning("job_not_found_mark_failed", job_id=job_id)
                return
            job.status = JobStatus.failed
            job.finished_at = datetime.now(tz=timezone.utc)
            job.error = error

        logger.error("job_failed", job_id=job_id, error=error)

    # ── Read methods ───────────────────────────────────────────────────────────

    async def get(self, job_id: str) -> JobRecord | None:
        """Return the JobRecord for job_id, or None if not found."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_for_assessment(self, assessment_id: str) -> list[JobRecord]:
        """
        Return all jobs for an assessment, sorted by started_at desc
        (most recent first).  Jobs without started_at (still pending) come first.

        Returns an empty list if the assessment has no registered jobs.
        """
        async with self._lock:
            job_ids = self._by_assessment.get(assessment_id, [])
            records = [self._jobs[jid] for jid in job_ids if jid in self._jobs]

        # Sort: pending (no started_at) before running/done/failed;
        # within started jobs, most recent first.
        records.sort(
            key=lambda r: r.started_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return records


# ── Singleton ──────────────────────────────────────────────────────────────────

# One instance per process. All routes and runners import this symbol.
# Do NOT instantiate JobRegistry elsewhere.
job_registry = JobRegistry()
