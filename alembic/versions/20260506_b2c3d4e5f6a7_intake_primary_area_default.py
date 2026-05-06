"""intake_primary_area_server_default

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-06 00:00:00.000000+00:00

REQ-5: Add server_default='not_set' to intake_sessions.primary_area.
Idempotent on existing rows — no data mutation, only default change.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.alter_column(
            'primary_area',
            existing_type=sa.String(length=50),
            server_default='not_set',
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.alter_column(
            'primary_area',
            existing_type=sa.String(length=50),
            server_default=None,
            existing_nullable=False,
        )
