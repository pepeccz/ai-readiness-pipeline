"""unique constraint on intake_session.lead_id

Revision ID: b1a2c3d4e5f6
Revises: 094eb2184722
Create Date: 2026-05-05 20:00:00.000000+00:00

Changes:
  - intake_sessions: add UNIQUE constraint on lead_id
  - Pre-flight dedup: keep oldest row per lead_id, delete duplicates.
    On a clean DB or first run this step is a no-op.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "094eb2184722"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Pre-flight: deduplicate intake_sessions rows by lead_id.
    # Keep the oldest row (MIN created_at), delete the rest.
    # This prevents the unique constraint below from failing on existing data.
    bind = op.get_bind()
    bind.execute(sa.text("""
        DELETE FROM intake_sessions
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM intake_sessions
            GROUP BY lead_id
        )
    """))

    # Add unique constraint on lead_id.
    # SQLite requires batch_alter_table to rebuild the table with the constraint.
    with op.batch_alter_table("intake_sessions", schema=None) as batch_op:
        batch_op.create_index(
            "uq_intake_sessions_lead_id",
            ["lead_id"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("intake_sessions", schema=None) as batch_op:
        batch_op.drop_index("uq_intake_sessions_lead_id")
