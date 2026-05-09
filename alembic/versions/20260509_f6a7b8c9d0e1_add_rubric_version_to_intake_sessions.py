"""add_rubric_version_to_intake_sessions

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-09 00:00:00.000000+00:00

Adds rubric_version column to intake_sessions.
This column anchors which rubric registry snapshot was used for scoring,
enabling reproducible re-scoring of historical sessions.

- Column: rubric_version VARCHAR(16) NOT NULL DEFAULT 'v1'
- All pre-existing rows receive 'v1' via server_default.
- This is a column-add only (NOT a state migration).
  The state machine migration (deep_pending → session2_pending) is PR5a.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("intake_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "rubric_version",
                sa.String(length=16),
                nullable=False,
                server_default="v1",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("intake_sessions", schema=None) as batch_op:
        batch_op.drop_column("rubric_version")
