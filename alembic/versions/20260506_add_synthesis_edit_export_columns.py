"""add_synthesis_edit_export_columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-06 00:00:00.000000+00:00

Adds 4 columns to intake_sessions to support synthesis editing,
PDF export tracking, and staleness detection.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('synthesis_edited_json', sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column('synthesis_edited_at', sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column('synthesis_last_exported_at', sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                'synthesis_export_count',
                sa.Integer(),
                nullable=False,
                server_default='0',
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.drop_column('synthesis_export_count')
        batch_op.drop_column('synthesis_last_exported_at')
        batch_op.drop_column('synthesis_edited_at')
        batch_op.drop_column('synthesis_edited_json')
