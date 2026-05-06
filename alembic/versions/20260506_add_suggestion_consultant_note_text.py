"""add suggestion consultant_note_text

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-06

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'suggestions',
        sa.Column('consultant_note_text', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('suggestions', 'consultant_note_text')
