"""
app/models/deep_branch — DeepBranch model.

Represents an AI-generated set of deep-dive questions for a specific branch
(e.g. strategic, data, talent) that the consultant reviews before sending
to the client.

Status lifecycle:
  pending_review → approved → sent → received → closed
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class DeepBranch(Base):
    __tablename__ = "deep_branches"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    intake_session_id: Mapped[str] = mapped_column(
        ForeignKey("intake_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # e.g. strategic | data | talent | infrastructure | compliance | governance
    branch_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # LLM-generated questions: [{text: str, rationale: str}, ...]
    generated_questions: Mapped[list] = mapped_column(JSON, nullable=False)

    # Consultant edits to generated_questions (optional)
    consultant_edits: Mapped[list | None] = mapped_column(JSON, nullable=True)

    consultant_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_to_client_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Client's responses: {question_index: answer_str, ...}
    client_responses: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # pending_review | approved | sent | received | closed
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review"
    )

    # Signed URL token for client access (TTL = DEEP_SESSION_TTL_DAYS)
    signed_token: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    session: Mapped["IntakeSession"] = relationship(  # noqa: F821
        "IntakeSession", back_populates="deep_branches"
    )

    def __repr__(self) -> str:
        return (
            f"<DeepBranch id={self.id} branch_id={self.branch_id} "
            f"status={self.status}>"
        )
