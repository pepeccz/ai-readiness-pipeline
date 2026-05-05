"""
app/models/consent — Consent model.

Stores GDPR consent records. Retention: 5 years minimum.

ondelete="RESTRICT" on lead_id FK: deleting a Lead with associated Consent
rows is blocked at DB level (IntegrityError). This is intentional per GDPR —
consent audit trail must outlive the lead record.

ip_hash: sha256(ip + SALT) — plain IP is never stored.
policy_version: maps to a file in schemas/questionnaire-v2/consents/.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # ondelete=RESTRICT: Lead cannot be deleted while consents exist.
    lead_id: Mapped[str] = mapped_column(
        ForeignKey("leads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Values: privacy | marketing | data_processing
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # e.g. "v1.0-2025-05" — maps to consents/privacy-v1.0.md on disk
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # sha256(ip + SALT) — 64 hex chars
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    lead: Mapped["Lead"] = relationship("Lead", back_populates="consents")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Consent id={self.id} lead_id={self.lead_id} "
            f"type={self.type} accepted={self.accepted}>"
        )
