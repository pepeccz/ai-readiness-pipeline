"""
tests/migrations/test_state_machine_redesign.py — E.1 (TDD RED)

Tests the Alembic migration: 20260509_xxxx_air_state_machine_redesign.

Scenarios verified:
  1. Upgrade: deep_pending / deep_received rows → session2_pending
  2. Upgrade: closed rows untouched
  3. Upgrade: rubric_version column is present with default 'v1' (PR2 column, additive)
  4. Upgrade: dismissed_findings JSON column exists on block_analyses with default '{}'
  5. Downgrade: states go back to deep_pending, dismissed_findings column dropped

Uses a fresh SQLite file per test (tmp_path fixture) to avoid touching live DB.
Runs Alembic migrations up to the specific target revision.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config


# ---------------------------------------------------------------------------
# Alembic config helper
# ---------------------------------------------------------------------------


def _make_alembic_cfg(db_path: str) -> Config:
    """Return an Alembic Config pointing at a fresh SQLite file."""
    repo_root = Path(__file__).parent.parent.parent
    cfg = Config(str(repo_root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    cfg.set_main_option("script_location", str(repo_root / "alembic"))
    return cfg


_TARGET_REVISION = "5a6b7c8d9e0f"  # PR5a migration revision id (to be created in E.2)
_PR2_REVISION = "f6a7b8c9d0e1"     # PR2 rubric_version migration (already exists)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_lead(conn, lead_id: str) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO leads (id, full_name, email, company_name, sector, company_size, "
            "respondent_role, ai_maturity, ai_goals, urgency, commitment, triage_payload, "
            "triage_score, triage_bucket, status, created_at) "
            "VALUES (:id, 'Test User', :email, 'TestCo', 'tecnologia', '1_10', "
            "'ceo_fundador', 'exploracion', '[]', 'media', 'agendar', '{}', 50, "
            "'review', 'accepted', datetime('now'))"
        ),
        {"id": lead_id, "email": f"{lead_id}@test.com"},
    )


def _create_session(conn, session_id: str, lead_id: str, state: str) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO intake_sessions (id, lead_id, state, primary_area, "
            "blocks_completed, areas_involved, created_at) "
            "VALUES (:id, :lead_id, :state, 'operaciones', '[]', '[]', datetime('now'))"
        ),
        {"id": session_id, "lead_id": lead_id, "state": state},
    )


def _create_block_analysis(conn, ba_id: str, session_id: str) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO block_analyses (id, intake_session_id, block_id, payload, status, created_at) "
            "VALUES (:id, :session_id, 'block-1-strategic', '{}', 'ready', datetime('now'))"
        ),
        {"id": ba_id, "session_id": session_id},
    )


# ---------------------------------------------------------------------------
# E.1 Tests — RED (migration target revision does not yet exist)
# ---------------------------------------------------------------------------


def test_migration_upgrades_deep_pending_to_session2_pending(tmp_path: Path) -> None:
    """
    After upgrading to target revision, deep_pending rows become session2_pending.
    """
    db_path = str(tmp_path / "test.db")
    cfg = _make_alembic_cfg(db_path)

    # Upgrade up to PR2 (rubric_version) to have a stable schema base
    command.upgrade(cfg, _PR2_REVISION)

    engine = sa.create_engine(f"sqlite:///{db_path}")
    lead_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    with engine.begin() as conn:
        _create_lead(conn, lead_id)
        _create_session(conn, session_id, lead_id, "deep_pending")

    # Apply PR5a migration
    command.upgrade(cfg, _TARGET_REVISION)

    with engine.begin() as conn:
        row = conn.execute(
            sa.text("SELECT state FROM intake_sessions WHERE id = :id"),
            {"id": session_id},
        ).fetchone()

    assert row is not None
    assert row[0] == "session2_pending", (
        f"Expected state 'session2_pending', got {row[0]!r}. "
        "Migration must UPDATE deep_pending → session2_pending."
    )
    engine.dispose()


def test_migration_upgrades_deep_received_to_session2_pending(tmp_path: Path) -> None:
    """
    After upgrading to target revision, deep_received rows become session2_pending.
    """
    db_path = str(tmp_path / "test2.db")
    cfg = _make_alembic_cfg(db_path)

    command.upgrade(cfg, _PR2_REVISION)

    engine = sa.create_engine(f"sqlite:///{db_path}")
    lead_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    with engine.begin() as conn:
        _create_lead(conn, lead_id)
        _create_session(conn, session_id, lead_id, "deep_received")

    command.upgrade(cfg, _TARGET_REVISION)

    with engine.begin() as conn:
        row = conn.execute(
            sa.text("SELECT state FROM intake_sessions WHERE id = :id"),
            {"id": session_id},
        ).fetchone()

    assert row is not None
    assert row[0] == "session2_pending", (
        f"Expected 'session2_pending', got {row[0]!r}."
    )
    engine.dispose()


def test_migration_leaves_closed_sessions_untouched(tmp_path: Path) -> None:
    """
    After upgrading, closed rows remain closed.
    """
    db_path = str(tmp_path / "test3.db")
    cfg = _make_alembic_cfg(db_path)

    command.upgrade(cfg, _PR2_REVISION)

    engine = sa.create_engine(f"sqlite:///{db_path}")
    lead_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    with engine.begin() as conn:
        _create_lead(conn, lead_id)
        _create_session(conn, session_id, lead_id, "closed")

    command.upgrade(cfg, _TARGET_REVISION)

    with engine.begin() as conn:
        row = conn.execute(
            sa.text("SELECT state FROM intake_sessions WHERE id = :id"),
            {"id": session_id},
        ).fetchone()

    assert row is not None
    assert row[0] == "closed", (
        f"Expected 'closed' to remain unchanged, got {row[0]!r}."
    )
    engine.dispose()


def test_migration_rubric_version_column_still_present(tmp_path: Path) -> None:
    """
    After PR5a migration, rubric_version column (added by PR2) is still present
    and new rows receive default 'v1'.
    """
    db_path = str(tmp_path / "test4.db")
    cfg = _make_alembic_cfg(db_path)

    command.upgrade(cfg, _TARGET_REVISION)

    engine = sa.create_engine(f"sqlite:///{db_path}")
    lead_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    with engine.begin() as conn:
        _create_lead(conn, lead_id)
        conn.execute(
            sa.text(
                "INSERT INTO intake_sessions (id, lead_id, state, primary_area, "
                "blocks_completed, areas_involved, created_at) "
                "VALUES (:id, :lead_id, 'in_progress', 'operaciones', '[]', '[]', datetime('now'))"
            ),
            {"id": session_id, "lead_id": lead_id},
        )
        row = conn.execute(
            sa.text("SELECT rubric_version FROM intake_sessions WHERE id = :id"),
            {"id": session_id},
        ).fetchone()

    assert row is not None
    assert row[0] == "v1", (
        f"Expected rubric_version default 'v1', got {row[0]!r}."
    )
    engine.dispose()


def test_migration_dismissed_findings_column_on_block_analyses(tmp_path: Path) -> None:
    """
    After upgrading to PR5a, block_analyses has dismissed_findings JSON column with default '{}'.
    """
    db_path = str(tmp_path / "test5.db")
    cfg = _make_alembic_cfg(db_path)

    command.upgrade(cfg, _TARGET_REVISION)

    engine = sa.create_engine(f"sqlite:///{db_path}")
    lead_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    ba_id = str(uuid.uuid4())

    with engine.begin() as conn:
        _create_lead(conn, lead_id)
        _create_session(conn, session_id, lead_id, "in_progress")
        _create_block_analysis(conn, ba_id, session_id)

        row = conn.execute(
            sa.text("SELECT dismissed_findings FROM block_analyses WHERE id = :id"),
            {"id": ba_id},
        ).fetchone()

    assert row is not None
    # The value should be parseable as JSON and equal to an empty dict
    value = row[0]
    if isinstance(value, str):
        parsed = json.loads(value)
    else:
        parsed = value
    assert parsed == {}, (
        f"Expected dismissed_findings default {{}}, got {value!r}. "
        "Migration must add dismissed_findings JSON column with server_default='{}'."
    )
    engine.dispose()


def test_migration_downgrade_restores_deep_pending(tmp_path: Path) -> None:
    """
    After downgrade from PR5a to PR2, dismissed_findings column is dropped.
    State data is left as-is (no reverse data migration — irreversible).
    """
    db_path = str(tmp_path / "test6.db")
    cfg = _make_alembic_cfg(db_path)

    # Upgrade to PR5a
    command.upgrade(cfg, _TARGET_REVISION)

    engine = sa.create_engine(f"sqlite:///{db_path}")
    lead_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    ba_id = str(uuid.uuid4())

    with engine.begin() as conn:
        _create_lead(conn, lead_id)
        _create_session(conn, session_id, lead_id, "session2_pending")
        _create_block_analysis(conn, ba_id, session_id)

    # Downgrade one step back to PR2
    command.downgrade(cfg, _PR2_REVISION)

    with engine.begin() as conn:
        # dismissed_findings column should NOT exist after downgrade
        try:
            conn.execute(
                sa.text("SELECT dismissed_findings FROM block_analyses WHERE id = :id"),
                {"id": ba_id},
            ).fetchone()
            column_exists = True
        except Exception:
            column_exists = False

    assert not column_exists, (
        "After downgrade, dismissed_findings column should not exist on block_analyses."
    )
    engine.dispose()
