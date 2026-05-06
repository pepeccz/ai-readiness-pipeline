"""
app/models/suggestion — Suggestion model.

Suggestions extracted from LLM block analysis output.
Each suggestion is a follow_up, contradiction, clarification, or gap.

consultant_action lifecycle:
  pending → done | discarded | irrelevant
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    block_analysis_id: Mapped[str] = mapped_column(
        ForeignKey("block_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Values: follow_up | contradiction | clarification | gap
    type: Mapped[str] = mapped_column(String(30), nullable=False)

    text: Mapped[str] = mapped_column(String(500), nullable=False)
    rationale: Mapped[str | None] = mapped_column(String(500), nullable=True)

    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Values: high | med | low
    priority: Mapped[str] = mapped_column(String(10), nullable=False)

    # Values: pending | done | discarded | irrelevant
    consultant_action: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # REQ-4: consultant annotation per suggestion; nullable, no backfill
    consultant_note_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    block_analysis: Mapped["BlockAnalysis"] = relationship(  # noqa: F821
        "BlockAnalysis", back_populates="suggestions"
    )

    def __repr__(self) -> str:
        return (
            f"<Suggestion id={self.id} type={self.type} "
            f"priority={self.priority} action={self.consultant_action}>"
        )
