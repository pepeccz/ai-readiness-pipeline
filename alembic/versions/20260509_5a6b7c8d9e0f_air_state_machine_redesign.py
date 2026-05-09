"""air_state_machine_redesign

Revision ID: 5a6b7c8d9e0f
Revises: f6a7b8c9d0e1
Create Date: 2026-05-09 00:00:00.000000+00:00

PR5a: State machine migration + new columns.

Changes:
  1. Add dismissed_findings JSON NOT NULL DEFAULT '{}' to block_analyses.
     Stores consultant-dismissed contradictions/follow_ups per block analysis.
     Shape: {"contradictions": ["sha1...", ...], "follow_ups": ["sha1..."]}

  2. Data migration: UPDATE intake_sessions SET state = 'session2_pending'
     WHERE state IN ('deep_pending', 'deep_received').
     Existing closed sessions are untouched (REQ-23).

  3. The deep_branches table is NOT dropped (soft-deprecated, REQ-14/REQ-15).
     Backend code paths creating DeepBranch rows are removed in PR5b.

  4. rubric_version column (added in f6a7b8c9d0e1 / PR2) is untouched.
     This migration is purely ADDITIVE on top of PR2.

Downgrade:
  - DROP dismissed_findings from block_analyses.
  - State data is NOT reversed (irreversible data migration; safe because
    deep_pending/deep_received no longer represent valid states post-deploy).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a6b7c8d9e0f'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add dismissed_findings column to block_analyses
    with op.batch_alter_table("block_analyses", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "dismissed_findings",
                sa.JSON(),
                nullable=False,
                server_default="{}",
            )
        )

    # 2. Migrate state values: deep_pending / deep_received → session2_pending
    op.execute(
        sa.text(
            "UPDATE intake_sessions SET state = 'session2_pending' "
            "WHERE state IN ('deep_pending', 'deep_received')"
        )
    )


def downgrade() -> None:
    # Drop dismissed_findings column from block_analyses
    with op.batch_alter_table("block_analyses", schema=None) as batch_op:
        batch_op.drop_column("dismissed_findings")

    # NOTE: state data is NOT reversed.
    # session2_pending rows are left as-is. Rolling back to a state where
    # deep_pending/deep_received exist would require knowing which rows
    # had which original state — that information is not stored.
    # Treat the state migration as irreversible (standard practice for data migrations).
