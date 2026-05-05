"""add_session1_synthesis

Revision ID: a1b2c3d4e5f6
Revises: 79516c7c7d4f
Create Date: 2026-05-06 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '79516c7c7d4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session1_synthesis', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.drop_column('session1_synthesis')
