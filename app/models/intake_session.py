"""
app/models/intake_session — IntakeSession model.

Represents a consultant-led intake session for an accepted Lead.

State machine (new — PR5a):
  in_progress → blocks_completed → session2_pending → closed

State machine (legacy — retired by PR5a migration):
  deep_pending, deep_received are no longer reachable from any code path.
  Existing rows were migrated to session2_pending by migration 5a6b7c8d9e0f.
  The string constants DEEP_PENDING / DEEP_RECEIVED are kept below as read-only
  aliases for one release cycle so any in-flight code can still reference them
  without crashing. Write paths only emit the new state names.

State constant aliases (backwards-compat, read-only):
  STATE_DEEP_PENDING = "deep_pending"    # → treat as session2_pending for reads
  STATE_DEEP_RECEIVED = "deep_received"  # → treat as session2_pending for reads
  STATE_SESSION2_PENDING = "session2_pending"
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

# ---------------------------------------------------------------------------
# State constants — backwards-compat aliases (PR5a)
# ---------------------------------------------------------------------------
# Write paths only emit new state names. Legacy constants are read-only aliases
# that remain for one release cycle to avoid crashing any in-flight references.
STATE_IN_PROGRESS = "in_progress"
STATE_BLOCKS_COMPLETED = "blocks_completed"
STATE_SESSION2_PENDING = "session2_pending"
STATE_CLOSED = "closed"

# Retired states — kept as read-only aliases. No code path may SET these.
STATE_DEEP_PENDING = "deep_pending"    # retired → session2_pending
STATE_DEEP_RECEIVED = "deep_received"  # retired → session2_pending


class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Rubric version used for scoring. Anchors which registry.yaml snapshot
    # was used so old sessions can be re-scored reproducibly.
    # server_default ensures all pre-existing rows receive "v1" on migration.
    rubric_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="v1", server_default="v1"
    )

    lead_id: Mapped[str] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    primary_area: Mapped[str] = mapped_column(String(50), nullable=False, server_default="not_set")
    secondary_area: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # JSON array of area strings for cross-area sessions
    areas_involved: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # State machine values defined above
    state: Mapped[str] = mapped_column(
        String(40), nullable=False, default="in_progress"
    )

    # JSON array of block_id strings: ["block-1-strategic", ...]
    blocks_completed: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    session1_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    session2_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # LLM-generated synthesis produced at session 1 close (write-once, opaque JSON blob)
    session1_synthesis: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # Edited synthesis — written by PATCH /session1/synthesis endpoint (never modifies session1_synthesis)
    synthesis_edited_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # Timestamp of last PATCH edit to synthesis_edited_json
    synthesis_edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamp of last successful PDF export
    synthesis_last_exported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Count of successful PDF exports
    synthesis_export_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Report content generated after session 2 (HTML or PDF path string)
    report_content: Mapped[str | None] = mapped_column(
        String(10000), nullable=True
    )

    # ── Timer columns (REQ-1) ─────────────────────────────────────────────────
    # timer_started_at IS NOT NULL → timer is running (canonical "is_running" signal)
    # timer_started_at IS NULL     → timer is paused or never started
    # timer_paused_at is informational (last pause wall-clock); not used for logic
    # timer_accumulated_seconds holds sum of all prior closed run intervals
    timer_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timer_paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timer_accumulated_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    @property
    def is_timer_running(self) -> bool:
        """True when timer_started_at is set (canonical running signal per ADR-2)."""
        return self.timer_started_at is not None

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    lead: Mapped["Lead"] = relationship(  # noqa: F821
        "Lead", back_populates="intake_sessions"
    )
    block_analyses: Mapped[list["BlockAnalysis"]] = relationship(  # noqa: F821
        "BlockAnalysis",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    deep_branches: Mapped[list["DeepBranch"]] = relationship(  # noqa: F821
        "DeepBranch",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<IntakeSession id={self.id} lead_id={self.lead_id} "
            f"state={self.state}>"
        )
