"""
app/models/block_draft — BlockDraft model.

Stores a transient partial block payload (draft) per (lead, block) pair.
Draft rows are deleted when the block is successfully submitted (BlockAnswer created).

Lifecycle: created/updated on PUT /intake/{lead}/blocks/{block}/draft
           deleted on POST /intake/{lead}/blocks/{block}/submit
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


class BlockDraft(Base):
    __tablename__ = "block_drafts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    lead_id: Mapped[str] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )

    block_id: Mapped[str] = mapped_column(String(100), nullable=False)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_now_utc,
        onupdate=_now_utc,
    )

    __table_args__ = (
        UniqueConstraint("lead_id", "block_id", name="uq_block_drafts_lead_block"),
        Index("ix_block_drafts_lead_id", "lead_id"),
    )

    def __repr__(self) -> str:
        return f"<BlockDraft lead_id={self.lead_id} block_id={self.block_id}>"
