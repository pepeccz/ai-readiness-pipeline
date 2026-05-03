"""Baseline — create all four tables in one shot.

This is the initial migration for the assessment-admin-platform. It creates:
  - users
  - sessions
  - login_attempts
  - assessments

All tables are created in a single revision because the database is empty at
first deploy (MVP, no existing data to migrate). No prior revisions exist.

See design §2.2 for the migration strategy and first-deploy checklist.

Revision ID: 0001
Revises: None (this is the baseline)
Create Date: 2026-05-02 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "password_reset_token_hash", sa.Text(), nullable=True
        ),
        sa.Column(
            "password_reset_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # ── sessions ──────────────────────────────────────────────────────────────
    # id = uuid4().hex (32 hex chars) — the raw cookie value.
    # Stored as Text, not UUID, to avoid any driver coercion on the cookie string.
    op.create_table(
        "sessions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])
    # Partial index: only non-revoked sessions are checked for validity.
    # SQLite supports partial indexes via the 'sqlite_where' keyword.
    op.create_index(
        "idx_sessions_expires_at",
        "sessions",
        ["expires_at"],
        postgresql_where=sa.text("revoked_at IS NULL"),
        sqlite_where=sa.text("revoked_at IS NULL"),
    )

    # ── login_attempts ────────────────────────────────────────────────────────
    # Serves as rate-limiting log for:
    #   - login attempts:           email=<email>, ip=<ip>, attempt_type='login'
    #   - password reset attempts:  email=<email>, ip=<ip>, attempt_type='reset'
    #   - public form submissions:  email=NULL,    ip=<ip>, attempt_type='public_submission'
    # email is NULLABLE to support IP-only scopes (TASK-A-16 + TASK-C-09 addendum).
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.Text(), nullable=True),  # NULL for IP-only scopes
        sa.Column("ip", sa.Text(), nullable=False),
        sa.Column(
            "attempt_type",
            sa.Text(),
            nullable=False,
            server_default="login",  # 'login' | 'reset' | 'public_submission'
        ),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_login_attempts_lookup",
        "login_attempts",
        ["email", "ip", "attempt_type", "attempted_at"],
    )

    # ── assessments ───────────────────────────────────────────────────────────
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), nullable=False),

        # Status & lifecycle
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="draft",
            # Values: 'draft' | 'pending_review' | 'approved' | 'archived'
        ),
        sa.Column(
            "auto_publish",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),

        # Ownership — SET NULL when user is deleted (enforced in app layer;
        # SQLite supports ON DELETE SET NULL via ForeignKeyConstraint).
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("last_edited_by_id", sa.Uuid(), nullable=True),

        # Flat identity columns
        sa.Column("company_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("sector", sa.Text(), nullable=False, server_default=""),
        sa.Column("employee_range", sa.Text(), nullable=False, server_default=""),
        sa.Column("revenue_range", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "respondent_name_role", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column("respondent_email", sa.Text(), nullable=True),
        sa.Column("who_decides", sa.Text(), nullable=False, server_default=""),
        sa.Column("budget", sa.Text(), nullable=False, server_default=""),
        sa.Column("priority_text", sa.Text(), nullable=False, server_default=""),

        # Scoring — flat for queryable score range filter
        sa.Column("maturity_score", sa.Float(), nullable=True),
        sa.Column("maturity_level", sa.String(64), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(64), nullable=True),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.Column("priority_level", sa.String(64), nullable=True),

        # Sub-scores from scoring_engine
        sa.Column("pts_tools", sa.Float(), nullable=True),
        sa.Column("pts_automation", sa.Float(), nullable=True),
        sa.Column("pts_area_usage", sa.Float(), nullable=True),
        sa.Column("pts_governance", sa.Float(), nullable=True),
        sa.Column("pts_goal_clarity", sa.Float(), nullable=True),
        sa.Column("pts_data_risk", sa.Float(), nullable=True),
        sa.Column("pts_ai_personal_data", sa.Float(), nullable=True),
        sa.Column("pts_dpa", sa.Float(), nullable=True),
        sa.Column("pts_dpia", sa.Float(), nullable=True),
        sa.Column("pts_automated_decisions", sa.Float(), nullable=True),
        sa.Column("pts_sector", sa.Float(), nullable=True),
        sa.Column("pts_incident", sa.Float(), nullable=True),

        # PDF & email
        sa.Column("pdf_path", sa.Text(), nullable=True),
        sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "email_status",
            sa.String(16),
            nullable=False,
            server_default="not_sent",
            # Values: 'not_sent' | 'sent' | 'failed'
        ),
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_error", sa.Text(), nullable=True),

        # Legacy
        sa.Column("task_id", sa.Text(), nullable=True),

        # JSON blobs
        sa.Column("form_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("llm_enriched_data", sa.JSON(), nullable=True),
        sa.Column("recommendation_data", sa.JSON(), nullable=True),
        sa.Column("field_sources", sa.JSON(), nullable=False, server_default="{}"),

        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["last_edited_by_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_assessments_status", "assessments", ["status"])
    op.create_index("idx_assessments_created_at", "assessments", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order (assessments references users).
    op.drop_index("idx_assessments_created_at", table_name="assessments")
    op.drop_index("idx_assessments_status", table_name="assessments")
    op.drop_table("assessments")

    op.drop_index("idx_login_attempts_lookup", table_name="login_attempts")
    op.drop_table("login_attempts")

    op.drop_index("idx_sessions_expires_at", table_name="sessions")
    op.drop_index("idx_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
