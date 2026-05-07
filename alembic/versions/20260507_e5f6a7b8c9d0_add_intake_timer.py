"""add_intake_timer

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-07 00:00:00.000000+00:00

REQ-1: Add three timer columns to intake_sessions:
  - timer_started_at: DATETIME nullable (NULL = timer paused / never started)
  - timer_paused_at:  DATETIME nullable (informational: when last paused)
  - timer_accumulated_seconds: INTEGER NOT NULL default 0 (prior run intervals)

Existing rows receive NULL/NULL/0 which is the correct initial state.
The next GET /intake/{lead_id}/state on any in_progress session will auto-start them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("intake_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("timer_started_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("timer_paused_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "timer_accumulated_seconds",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("intake_sessions", schema=None) as batch_op:
        batch_op.drop_column("timer_accumulated_seconds")
        batch_op.drop_column("timer_paused_at")
        batch_op.drop_column("timer_started_at")
