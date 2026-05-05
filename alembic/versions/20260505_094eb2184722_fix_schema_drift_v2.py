"""fix schema drift v2

Revision ID: 094eb2184722
Revises: 0002
Create Date: 2026-05-05 17:34:09.809247+00:00

Changes:
  - intake_sessions: add report_content column
  - leads: change assigned_consultant_id from VARCHAR(36) to Uuid
  - users: rename index idx_users_email → ix_users_email
  - assessments/sessions: anonymous FK constraints dropped via batch rebuild
    (SQLite doesn't support named FKs; batch_alter_table handles this transparently)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '094eb2184722'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add report_content to intake_sessions
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('report_content', sa.String(length=10000), nullable=True))

    # Change assigned_consultant_id type from VARCHAR(36) to Uuid
    # batch_alter_table rebuilds the table — anonymous FK constraints are
    # not preserved (matching the model which has no explicit ForeignKey here)
    with op.batch_alter_table('leads', schema=None) as batch_op:
        batch_op.alter_column(
            'assigned_consultant_id',
            existing_type=sa.VARCHAR(length=36),
            type_=sa.Uuid(),
            existing_nullable=True,
        )

    # Rename email index on users
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('idx_users_email')
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)


def downgrade() -> None:
    # Rename email index back
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.create_index('idx_users_email', ['email'], unique=True)

    # Revert assigned_consultant_id type
    with op.batch_alter_table('leads', schema=None) as batch_op:
        batch_op.alter_column(
            'assigned_consultant_id',
            existing_type=sa.Uuid(),
            type_=sa.VARCHAR(length=36),
            existing_nullable=True,
        )

    # Remove report_content from intake_sessions
    with op.batch_alter_table('intake_sessions', schema=None) as batch_op:
        batch_op.drop_column('report_content')
