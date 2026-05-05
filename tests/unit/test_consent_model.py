"""
tests/unit/test_consent_model.py — CRUD tests for Consent model (T2.3 RED).

Tests:
- create consent linked to a lead
- lead_id RESTRICT: deleting a lead with consents raises IntegrityError
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.consent import Consent
from app.models.lead import Lead


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        full_name="Test Lead",
        email="lead@example.com",
        company_name="Co",
        sector="tecnologia",
        company_size="1_10",
        respondent_role="ceo",
        ai_maturity="sin_ia",
        ai_goals=[],
        urgency="baja",
        commitment="informarse",
        triage_payload={},
        triage_score=30,
        triage_bucket="cold_cool",
    )
    defaults.update(overrides)
    return Lead(**defaults)


@pytest.mark.asyncio
async def test_consent_create(test_db):
    """Create a Consent linked to a Lead."""
    lead = _make_lead(email="consent_test@example.com")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    consent = Consent(
        lead_id=lead.id,
        type="privacy",
        accepted=True,
        policy_version="v1.0-2025-05",
        ip_hash="a" * 64,
    )
    test_db.add(consent)
    await test_db.commit()
    await test_db.refresh(consent)

    assert consent.id is not None
    assert consent.lead_id == lead.id
    assert consent.accepted is True
    assert consent.type == "privacy"
    assert len(consent.ip_hash) == 64


@pytest.mark.asyncio
async def test_consent_restrict_on_lead_delete(test_db):
    """Deleting a Lead that has Consents must raise IntegrityError (RESTRICT)."""
    lead = _make_lead(email="restrict_test@example.com")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    consent = Consent(
        lead_id=lead.id,
        type="privacy",
        accepted=True,
        policy_version="v1.0-2025-05",
        ip_hash="b" * 64,
    )
    test_db.add(consent)
    await test_db.commit()

    with pytest.raises((IntegrityError, Exception)):
        await test_db.delete(lead)
        await test_db.commit()


@pytest.mark.asyncio
async def test_consent_marketing_accepted_false(test_db):
    """Marketing consent can be persisted with accepted=False."""
    lead = _make_lead(email="marketing@example.com")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    consent = Consent(
        lead_id=lead.id,
        type="marketing",
        accepted=False,
        policy_version="v1.0-2025-05",
        ip_hash="c" * 64,
    )
    test_db.add(consent)
    await test_db.commit()
    await test_db.refresh(consent)

    assert consent.accepted is False
    assert consent.type == "marketing"
