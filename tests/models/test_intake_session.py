"""
tests/models/test_intake_session.py — TA.2

Unit test: IntakeSession has session1_synthesis attribute mapped to JSON nullable column.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake_session import IntakeSession


pytestmark = pytest.mark.asyncio


async def test_intake_session_has_session1_synthesis_attribute():
    """IntakeSession model has session1_synthesis attribute."""
    assert hasattr(IntakeSession, "session1_synthesis"), (
        "IntakeSession must have a 'session1_synthesis' attribute"
    )


async def test_session1_synthesis_defaults_to_none(test_db: AsyncSession):
    """A newly created IntakeSession has session1_synthesis == None."""
    from app.models.lead import Lead

    lead = Lead(
        full_name="Test User",
        email="test@example.com",
        company_name="TestCo",
        sector="tecnologia",
        company_size="1_10",
        respondent_role="ceo_fundador",
        ai_maturity="exploracion",
        ai_goals=["automatizar_procesos"],
        urgency="media",
        commitment="agendar",
        triage_payload={},
        triage_score=50,
        triage_bucket="review",
        status="accepted",
    )
    test_db.add(lead)
    await test_db.flush()

    session = IntakeSession(
        lead_id=lead.id,
        primary_area="operaciones",
        state="in_progress",
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    assert session.session1_synthesis is None


async def test_session1_synthesis_persists_dict(test_db: AsyncSession):
    """session1_synthesis can be set to a dict and is persisted correctly."""
    from app.models.lead import Lead

    lead = Lead(
        full_name="Synth User",
        email="synth@example.com",
        company_name="SynthCo",
        sector="tecnologia",
        company_size="1_10",
        respondent_role="ceo_fundador",
        ai_maturity="exploracion",
        ai_goals=["automatizar_procesos"],
        urgency="media",
        commitment="agendar",
        triage_payload={},
        triage_score=60,
        triage_bucket="auto_accept",
        status="accepted",
    )
    test_db.add(lead)
    await test_db.flush()

    synth_data = {
        "summary": "Global synthesis text",
        "key_insights": ["Insight 1"],
        "recommendations": ["Rec 1"],
        "hypothesis": "Main hypothesis",
        "generated_at": "2026-05-06T00:00:00Z",
        "model": "claude-sonnet-4-6",
    }

    session = IntakeSession(
        lead_id=lead.id,
        primary_area="operaciones",
        state="deep_pending",
        session1_synthesis=synth_data,
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    assert session.session1_synthesis == synth_data
    assert session.session1_synthesis["summary"] == "Global synthesis text"


# ---------------------------------------------------------------------------
# E.5 — REQ-09: session2_pending state transitions (PR5a TDD)
# ---------------------------------------------------------------------------


async def test_session_can_write_session2_pending_state(test_db: AsyncSession):
    """
    E.5a: IntakeSession can persist state='session2_pending'.
    This is the new terminal state after session1/close (replaces deep_pending).
    """
    from app.models.lead import Lead

    lead = Lead(
        full_name="S2P User",
        email="s2p@example.com",
        company_name="S2PCo",
        sector="tecnologia",
        company_size="1_10",
        respondent_role="ceo_fundador",
        ai_maturity="exploracion",
        ai_goals=["automatizar_procesos"],
        urgency="media",
        commitment="agendar",
        triage_payload={},
        triage_score=60,
        triage_bucket="auto_accept",
        status="accepted",
    )
    test_db.add(lead)
    await test_db.flush()

    session = IntakeSession(
        lead_id=lead.id,
        primary_area="operaciones",
        state="session2_pending",
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    assert session.state == "session2_pending", (
        f"Expected state 'session2_pending', got {session.state!r}."
    )


async def test_session_state_constant_session2_pending_is_defined():
    """
    E.5b: STATE_SESSION2_PENDING constant is exported from the model module.
    """
    from app.models.intake_session import STATE_SESSION2_PENDING

    assert STATE_SESSION2_PENDING == "session2_pending"


async def test_session_legacy_state_constants_available():
    """
    E.5c: Backwards-compat state aliases are still importable (one-release retention).
    Deep_pending / deep_received aliases must remain but code must NOT set them.
    """
    from app.models.intake_session import STATE_DEEP_PENDING, STATE_DEEP_RECEIVED

    assert STATE_DEEP_PENDING == "deep_pending"
    assert STATE_DEEP_RECEIVED == "deep_received"


# ---------------------------------------------------------------------------
# TA.3 — REQ-5: primary_area must have DB-level server_default='not_set'
# ---------------------------------------------------------------------------

async def test_primary_area_server_default_at_db_level(test_db: AsyncSession):
    """
    TA.3: Row inserted via raw SQL without primary_area gets 'not_set' from DB server_default.

    Bypasses SQLAlchemy ORM defaults to verify the server_default constraint.
    """
    from sqlalchemy import text
    from app.models.lead import Lead

    lead = Lead(
        full_name="Default Tester",
        email="default_area@example.com",
        company_name="DefaultCo",
        sector="tecnologia",
        company_size="1_10",
        respondent_role="ceo_fundador",
        ai_maturity="exploracion",
        ai_goals=["automatizar_procesos"],
        urgency="media",
        commitment="agendar",
        triage_payload={},
        triage_score=50,
        triage_bucket="review",
        status="accepted",
    )
    test_db.add(lead)
    await test_db.flush()

    # Insert via raw SQL without specifying primary_area — DB must supply 'not_set'
    await test_db.execute(
        text(
            "INSERT INTO intake_sessions (id, lead_id, state, blocks_completed, areas_involved, created_at) "
            "VALUES (:id, :lead_id, 'in_progress', '[]', '[]', datetime('now'))"
        ),
        {"id": "test-server-default-id-001", "lead_id": lead.id},
    )
    await test_db.commit()

    result = await test_db.execute(
        text("SELECT primary_area FROM intake_sessions WHERE id = :id"),
        {"id": "test-server-default-id-001"},
    )
    row = result.fetchone()
    assert row is not None
    assert row[0] == "not_set", (
        f"Expected DB server_default 'not_set' for primary_area, got {row[0]!r}. "
        "Add server_default='not_set' to the IntakeSession.primary_area column + Alembic migration."
    )
