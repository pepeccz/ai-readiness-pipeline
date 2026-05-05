"""questionnaire_v2 — create v2 tables + modify assessments + clean testing data.

Creates tables:
  leads, consents, intake_sessions, block_analyses, suggestions, deep_branches

Modifies:
  assessments: add lead_id (FK to leads, SET NULL) + client_id (nullable String)

Cleans:
  DELETE FROM assessments (testing data only, no real clients yet)
  DELETE FROM jobs if the table exists (v1 job queue data)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Clean testing data BEFORE adding FKs ───────────────────────────────
    op.execute("DELETE FROM assessments")

    # Delete from jobs if the table exists (v1 job queue)
    conn = op.get_bind()
    inspector = inspect(conn)
    if "jobs" in inspector.get_table_names():
        op.execute("DELETE FROM jobs")

    # ── 2. leads ──────────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("sector", sa.String(100), nullable=False),
        sa.Column("company_size", sa.String(50), nullable=False),
        sa.Column("respondent_role", sa.String(100), nullable=False),
        sa.Column("ai_maturity", sa.String(50), nullable=False),
        sa.Column("ai_goals", sa.JSON(), nullable=False),
        sa.Column("urgency", sa.String(50), nullable=False),
        sa.Column("commitment", sa.String(50), nullable=False),
        sa.Column("triage_payload", sa.JSON(), nullable=False),
        sa.Column("triage_score", sa.Integer(), nullable=False),
        sa.Column("triage_bucket", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_review"),
        sa.Column("rejected_reason", sa.String(500), nullable=True),
        sa.Column(
            "assigned_consultant_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("client_id", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_email", "leads", ["email"])
    op.create_index("ix_leads_triage_bucket", "leads", ["triage_bucket"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])
    op.create_index("ix_leads_client_id", "leads", ["client_id"])
    op.create_index(
        "ix_leads_bucket_status", "leads", ["triage_bucket", "status"]
    )

    # ── 3. consents ───────────────────────────────────────────────────────────
    op.create_table(
        "consents",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "lead_id",
            sa.String(36),
            sa.ForeignKey("leads.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("policy_version", sa.String(20), nullable=False),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consents_lead_id", "consents", ["lead_id"])

    # ── 4. intake_sessions ────────────────────────────────────────────────────
    op.create_table(
        "intake_sessions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "lead_id",
            sa.String(36),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("primary_area", sa.String(50), nullable=False),
        sa.Column("secondary_area", sa.String(50), nullable=True),
        sa.Column("areas_involved", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(40), nullable=False, server_default="in_progress"),
        sa.Column("blocks_completed", sa.JSON(), nullable=False),
        sa.Column("session1_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session2_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intake_sessions_lead_id", "intake_sessions", ["lead_id"])

    # ── 5. block_analyses ─────────────────────────────────────────────────────
    op.create_table(
        "block_analyses",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "intake_session_id",
            sa.String(36),
            sa.ForeignKey("intake_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("block_id", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("llm_output", sa.JSON(), nullable=True),
        sa.Column("llm_model_used", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_blockanalysis_session_block",
        "block_analyses",
        ["intake_session_id", "block_id"],
        unique=True,
    )
    op.create_index(
        "ix_block_analyses_intake_session_id", "block_analyses", ["intake_session_id"]
    )
    op.create_index("ix_block_analyses_block_id", "block_analyses", ["block_id"])

    # ── 6. suggestions ────────────────────────────────────────────────────────
    op.create_table(
        "suggestions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "block_analysis_id",
            sa.String(36),
            sa.ForeignKey("block_analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("rationale", sa.String(500), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("consultant_action", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_suggestions_block_analysis_id", "suggestions", ["block_analysis_id"]
    )

    # ── 7. deep_branches ──────────────────────────────────────────────────────
    op.create_table(
        "deep_branches",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column(
            "intake_session_id",
            sa.String(36),
            sa.ForeignKey("intake_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_id", sa.String(50), nullable=False),
        sa.Column("generated_questions", sa.JSON(), nullable=False),
        sa.Column("consultant_edits", sa.JSON(), nullable=True),
        sa.Column("consultant_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_to_client_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_responses", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(30), nullable=False, server_default="pending_review"
        ),
        sa.Column("signed_token", sa.String(200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deep_branches_intake_session_id", "deep_branches", ["intake_session_id"]
    )
    op.create_index("ix_deep_branches_signed_token", "deep_branches", ["signed_token"])

    # ── 8. Alter assessments: add lead_id + client_id ─────────────────────────
    # SQLite doesn't support ALTER TABLE ADD COLUMN with FK constraints directly.
    # Use batch mode (copy-and-move) to recreate the table with the new columns.
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.add_column(
            sa.Column("lead_id", sa.String(36), nullable=True),
        )
        batch_op.add_column(
            sa.Column("client_id", sa.String(36), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_assessments_lead_id",
            "leads",
            ["lead_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_index("ix_assessments_lead_id", "assessments", ["lead_id"])
    op.create_index("ix_assessments_client_id", "assessments", ["client_id"])


def downgrade() -> None:
    # ── Reverse: assessments columns ──────────────────────────────────────────
    op.drop_index("ix_assessments_client_id", table_name="assessments")
    op.drop_index("ix_assessments_lead_id", table_name="assessments")
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.drop_constraint("fk_assessments_lead_id", type_="foreignkey")
        batch_op.drop_column("client_id")
        batch_op.drop_column("lead_id")

    # ── Drop tables in reverse FK dependency order ────────────────────────────
    op.drop_index("ix_deep_branches_signed_token", table_name="deep_branches")
    op.drop_index("ix_deep_branches_intake_session_id", table_name="deep_branches")
    op.drop_table("deep_branches")

    op.drop_index("ix_suggestions_block_analysis_id", table_name="suggestions")
    op.drop_table("suggestions")

    op.drop_index("ix_block_analyses_block_id", table_name="block_analyses")
    op.drop_index(
        "ix_block_analyses_intake_session_id", table_name="block_analyses"
    )
    op.drop_index("ix_blockanalysis_session_block", table_name="block_analyses")
    op.drop_table("block_analyses")

    op.drop_index("ix_intake_sessions_lead_id", table_name="intake_sessions")
    op.drop_table("intake_sessions")

    op.drop_index("ix_consents_lead_id", table_name="consents")
    op.drop_table("consents")

    op.drop_index("ix_leads_bucket_status", table_name="leads")
    op.drop_index("ix_leads_client_id", table_name="leads")
    op.drop_index("ix_leads_created_at", table_name="leads")
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_index("ix_leads_triage_bucket", table_name="leads")
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_table("leads")
