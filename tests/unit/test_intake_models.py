"""
tests/unit/test_intake_models.py — CRUD + FK tests for IntakeSession,
BlockAnalysis (UNIQUE), Suggestion, DeepBranch (T2.5 RED).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.block_analysis import BlockAnalysis
from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.suggestion import Suggestion


def _make_lead(email: str) -> Lead:
    return Lead(
        full_name="Test",
        email=email,
        company_name="Co",
        sector="tecnologia",
        company_size="1_10",
        respondent_role="ceo",
        ai_maturity="sin_ia",
        ai_goals=[],
        urgency="baja",
        commitment="informarse",
        triage_payload={},
        triage_score=40,
        triage_bucket="cold_cool",
    )


async def _setup_lead_and_session(test_db, email: str):
    lead = _make_lead(email)
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    session = IntakeSession(
        lead_id=lead.id,
        primary_area="ventas",
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return lead, session


@pytest.mark.asyncio
async def test_intake_session_create(test_db):
    """Create IntakeSession with defaults."""
    _, session = await _setup_lead_and_session(test_db, "intake@example.com")

    assert session.id is not None
    assert session.state == "in_progress"
    assert session.secondary_area is None
    assert session.blocks_completed == []
    assert session.session1_completed_at is None


@pytest.mark.asyncio
async def test_block_analysis_create(test_db):
    """Create BlockAnalysis linked to IntakeSession."""
    _, session = await _setup_lead_and_session(test_db, "ba@example.com")

    ba = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={"q1": "yes"},
    )
    test_db.add(ba)
    await test_db.commit()
    await test_db.refresh(ba)

    assert ba.id is not None
    assert ba.status == "in_progress"
    assert ba.llm_output is None
    assert ba.payload == {"q1": "yes"}


@pytest.mark.asyncio
async def test_block_analysis_unique_session_block(test_db):
    """UNIQUE constraint on (intake_session_id, block_id) must be enforced."""
    _, session = await _setup_lead_and_session(test_db, "unique@example.com")

    ba1 = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={"q1": "first"},
    )
    test_db.add(ba1)
    await test_db.commit()

    ba2 = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={"q1": "second"},
    )
    test_db.add(ba2)
    with pytest.raises((IntegrityError, Exception)):
        await test_db.commit()


@pytest.mark.asyncio
async def test_suggestion_create(test_db):
    """Create Suggestion linked to BlockAnalysis."""
    _, session = await _setup_lead_and_session(test_db, "suggestion@example.com")

    ba = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={},
    )
    test_db.add(ba)
    await test_db.commit()
    await test_db.refresh(ba)

    suggestion = Suggestion(
        block_analysis_id=ba.id,
        type="follow_up",
        text="¿Qué herramientas IA ya usan?",
        confidence=0.85,
        priority="high",
    )
    test_db.add(suggestion)
    await test_db.commit()
    await test_db.refresh(suggestion)

    assert suggestion.id is not None
    assert suggestion.consultant_action == "pending"
    assert suggestion.rationale is None


@pytest.mark.asyncio
async def test_deep_branch_create(test_db):
    """Create DeepBranch linked to IntakeSession."""
    _, session = await _setup_lead_and_session(test_db, "deep@example.com")

    branch = DeepBranch(
        intake_session_id=session.id,
        branch_id="strategic",
        generated_questions=[{"text": "¿Cuál es su mayor reto?"}],
    )
    test_db.add(branch)
    await test_db.commit()
    await test_db.refresh(branch)

    assert branch.id is not None
    assert branch.status == "pending_review"
    assert branch.client_responses is None
    assert branch.signed_token is None
    assert len(branch.generated_questions) == 1


@pytest.mark.asyncio
async def test_intake_session_cascade_deletes_block_analyses(test_db):
    """Deleting IntakeSession cascades to BlockAnalysis rows."""
    lead, session = await _setup_lead_and_session(test_db, "cascade@example.com")

    ba = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-3-data",
        payload={},
    )
    test_db.add(ba)
    await test_db.commit()

    await test_db.delete(session)
    await test_db.commit()

    result = await test_db.execute(
        select(BlockAnalysis).where(BlockAnalysis.intake_session_id == session.id)
    )
    assert result.scalars().all() == []
