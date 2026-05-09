"""
app/models/block_analysis — BlockAnalysis model.

Stores LLM analysis output per (session, block) pair.

UNIQUE constraint on (intake_session_id, block_id): a session can have at most
one BlockAnalysis per block. Re-submitting a block replaces the existing row.

status values: in_progress | ready | failed
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class BlockAnalysis(Base):
    __tablename__ = "block_analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    intake_session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    block_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Raw answers from the block form
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # LLM output: synthesis, contradictions, follow_ups, etc.
    llm_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    llm_model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # in_progress | ready | failed
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )

    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # dismissed_findings — stores consultant-dismissed contradictions / follow_ups.
    # Shape: {"contradictions": ["sha1...", ...], "follow_ups": ["sha1..."]}
    # JSON column added in migration 5a6b7c8d9e0f (PR5a).
    dismissed_findings: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}"
    )

    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["IntakeSession"] = relationship(  # noqa: F821
        "IntakeSession", back_populates="block_analyses"
    )
    suggestions: Mapped[list["Suggestion"]] = relationship(  # noqa: F821
        "Suggestion",
        back_populates="block_analysis",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_blockanalysis_session_block",
            "intake_session_id",
            "block_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BlockAnalysis id={self.id} block_id={self.block_id} "
            f"status={self.status}>"
        )
