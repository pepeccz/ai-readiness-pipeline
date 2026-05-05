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
