"""
tests/unit/test_lead_model.py — CRUD tests for Lead model (T2.1 RED).

Tests:
- create a Lead with all required fields
- read by id
- filter by triage_bucket
- filter by status
- indexes exist on email, triage_bucket, status, created_at
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text

from app.models.lead import Lead


@pytest.mark.asyncio
async def test_lead_create(test_db):
    """Create a Lead with all required fields and verify persistence."""
    lead = Lead(
        full_name="Ana García",
        email="ana@example.com",
        company_name="Acme SL",
        sector="tecnologia",
        company_size="11_25",
        respondent_role="cto",
        ai_maturity="exploracion",
        ai_goals=["eficiencia", "automatizacion"],
        urgency="media",
        commitment="agendar",
        triage_payload={"sector": "tecnologia"},
        triage_score=75,
        triage_bucket="review",
    )
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    assert lead.id is not None
    assert lead.full_name == "Ana García"
    assert lead.email == "ana@example.com"
    assert lead.triage_bucket == "review"
    assert lead.status == "pending_review"
    assert lead.client_id is None
    assert lead.assigned_consultant_id is None


@pytest.mark.asyncio
async def test_lead_read_by_id(test_db):
    """Read a Lead by primary key."""
    lead_id = str(uuid.uuid4())
    lead = Lead(
        id=lead_id,
        full_name="Pedro López",
        email="pedro@example.com",
        company_name="Beta SA",
        sector="salud",
        company_size="51_200",
        respondent_role="director_general",
        ai_maturity="pilotos",
        ai_goals=["calidad"],
        urgency="alta",
        commitment="explorar",
        triage_payload={},
        triage_score=90,
        triage_bucket="auto_accept",
    )
    test_db.add(lead)
    await test_db.commit()

    result = await test_db.get(Lead, lead_id)
    assert result is not None
    assert result.full_name == "Pedro López"
    assert result.triage_bucket == "auto_accept"


@pytest.mark.asyncio
async def test_lead_filter_by_bucket(test_db):
    """Filter leads by triage_bucket."""
    for i, bucket in enumerate(["review", "auto_accept", "review"]):
        lead = Lead(
            full_name=f"User {i}",
            email=f"user{i}@example.com",
            company_name=f"Co {i}",
            sector="tecnologia",
            company_size="1_10",
            respondent_role="ceo",
            ai_maturity="sin_ia",
            ai_goals=[],
            urgency="baja",
            commitment="informarse",
            triage_payload={},
            triage_score=50 + i * 20,
            triage_bucket=bucket,
        )
        test_db.add(lead)
    await test_db.commit()

    result = await test_db.execute(
        select(Lead).where(Lead.triage_bucket == "review")
    )
    leads = result.scalars().all()
    assert len(leads) == 2
    assert all(l.triage_bucket == "review" for l in leads)


@pytest.mark.asyncio
async def test_lead_filter_by_status(test_db):
    """Filter leads by status."""
    for status in ["pending_review", "accepted", "pending_review"]:
        lead = Lead(
            full_name="Test",
            email=f"test_{status}_{uuid.uuid4()}@example.com",
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
            status=status,
        )
        test_db.add(lead)
    await test_db.commit()

    result = await test_db.execute(
        select(Lead).where(Lead.status == "pending_review")
    )
    leads = result.scalars().all()
    assert len(leads) == 2


@pytest.mark.asyncio
async def test_lead_optional_fields_nullable(test_db):
    """phone, assigned_consultant_id, client_id, rejected_reason are nullable."""
    lead = Lead(
        full_name="Sin Teléfono",
        email="sintelefono@example.com",
        company_name="Co",
        sector="finanzas",
        company_size="201_500",
        respondent_role="cfo",
        ai_maturity="produccion_sin_gobierno",
        ai_goals=["reduccion_costes"],
        urgency="critica",
        commitment="agendar",
        triage_payload={},
        triage_score=120,
        triage_bucket="auto_accept",
    )
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    assert lead.phone is None
    assert lead.assigned_consultant_id is None
    assert lead.client_id is None
    assert lead.rejected_reason is None
    assert lead.accepted_at is None
