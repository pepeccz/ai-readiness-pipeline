"""
app/models/lead — Lead model.

Represents a potential client who completed the TRIAGE questionnaire.

Lifecycle (Lead.status):
  pending_review → accepted | rejected
  accepted → converted (when Assessment is created with lead_id FK)

Indexes:
  email           — fast lookup / dedup
  triage_bucket   — admin filtering
  status          — admin filtering
  created_at      — date range filtering
  bucket + status — compound for common admin query

client_id is a nullable String (no FK yet). Future evolution: add FK to clients
table once that table exists and backfill existing rows.

assigned_consultant_id is a nullable FK to users.id. Set when admin accepts lead.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── TRIAGE answers (flat, for admin filtering) ────────────────────────────
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    company_size: Mapped[str] = mapped_column(String(50), nullable=False)
    respondent_role: Mapped[str] = mapped_column(String(100), nullable=False)
    ai_maturity: Mapped[str] = mapped_column(String(50), nullable=False)
    ai_goals: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    urgency: Mapped[str] = mapped_column(String(50), nullable=False)
    commitment: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── TRIAGE results ────────────────────────────────────────────────────────
    triage_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    triage_score: Mapped[int] = mapped_column(Integer, nullable=False)
    triage_bucket: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )

    # ── Status & review ───────────────────────────────────────────────────────
    # Values: pending_review | accepted | rejected | converted
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    rejected_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Ownership ─────────────────────────────────────────────────────────────
    # FK to users.id — nullable; set when admin accepts and assigns consultant.
    assigned_consultant_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # FK to future clients table — nullable String, no FK constraint yet.
    client_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    consents: Mapped[list["Consent"]] = relationship(  # noqa: F821
        "Consent", back_populates="lead"
    )
    intake_sessions: Mapped[list["IntakeSession"]] = relationship(  # noqa: F821
        "IntakeSession", back_populates="lead"
    )

    __table_args__ = (
        Index("ix_leads_bucket_status", "triage_bucket", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Lead id={self.id} email={self.email!r} "
            f"bucket={self.triage_bucket} status={self.status}>"
        )
