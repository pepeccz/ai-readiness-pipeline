"""
app/models/intake_session — IntakeSession model.

Represents a consultant-led intake session for an accepted Lead.

State machine:
  in_progress → blocks_completed → deep_pending → deep_received → closed
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
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

    # Report content generated after session 2 (HTML or PDF path string)
    report_content: Mapped[str | None] = mapped_column(
        String(10000), nullable=True
    )

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
