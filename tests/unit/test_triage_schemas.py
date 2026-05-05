"""
tests/unit/test_triage_schemas.py — T3.1

Unit tests for TriagePayload and TriageResponse Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from app.schemas.triage import (
    ConsentEntry,
    TriageAnswers,
    TriagePayload,
    TriageResponse,
)


# ---------------------------------------------------------------------------
# ConsentEntry
# ---------------------------------------------------------------------------


def test_consent_entry_privacy_valid():
    c = ConsentEntry(type="privacy", accepted=True, policy_version="v1.0-2025-05")
    assert c.type == "privacy"
    assert c.accepted is True


def test_consent_entry_marketing_optional_false():
    c = ConsentEntry(type="marketing", accepted=False, policy_version="v1.0-2025-05")
    assert c.accepted is False


def test_consent_entry_invalid_type():
    with pytest.raises(ValidationError):
        ConsentEntry(type="unknown_type", accepted=True, policy_version="v1.0-2025-05")


# ---------------------------------------------------------------------------
# TriageAnswers
# ---------------------------------------------------------------------------


def test_triage_answers_valid_minimal():
    a = TriageAnswers(
        full_name="Ana García",
        email="ana@example.com",
        company_name="Acme SL",
        sector="tecnologia",
        company_size="26_100",
        respondent_role="ceo_fundador",
        ai_maturity="exploracion",
        urgency="alta",
        ai_goals=["reducir_costes"],
        commitment="agendar",
    )
    assert a.full_name == "Ana García"
    assert a.phone is None


def test_triage_answers_invalid_email():
    with pytest.raises(ValidationError):
        TriageAnswers(
            full_name="X",
            email="not-an-email",
            company_name="X",
            sector="tecnologia",
            company_size="26_100",
            respondent_role="ceo_fundador",
            ai_maturity="exploracion",
            urgency="alta",
            ai_goals=["reducir_costes"],
            commitment="agendar",
        )


def test_triage_answers_ai_goals_max_two():
    with pytest.raises(ValidationError):
        TriageAnswers(
            full_name="X",
            email="x@x.com",
            company_name="X",
            sector="tecnologia",
            company_size="26_100",
            respondent_role="ceo_fundador",
            ai_maturity="exploracion",
            urgency="alta",
            ai_goals=["reducir_costes", "mejorar_clientes", "aumentar_ventas"],
            commitment="agendar",
        )


# ---------------------------------------------------------------------------
# TriagePayload — privacy consent required
# ---------------------------------------------------------------------------


_VALID_ANSWERS = dict(
    full_name="Test User",
    email="test@example.com",
    company_name="TestCorp",
    sector="tecnologia",
    company_size="26_100",
    respondent_role="ceo_fundador",
    ai_maturity="exploracion",
    urgency="alta",
    ai_goals=["reducir_costes"],
    commitment="agendar",
)


def test_triage_payload_valid():
    payload = TriagePayload(
        answers=TriageAnswers(**_VALID_ANSWERS),
        consents=[
            ConsentEntry(type="privacy", accepted=True, policy_version="v1.0-2025-05"),
        ],
    )
    assert payload.answers.email == "test@example.com"


def test_triage_payload_missing_privacy_raises():
    with pytest.raises(ValidationError, match="privacy"):
        TriagePayload(
            answers=TriageAnswers(**_VALID_ANSWERS),
            consents=[
                ConsentEntry(type="marketing", accepted=True, policy_version="v1.0-2025-05"),
            ],
        )


def test_triage_payload_privacy_not_accepted_raises():
    with pytest.raises(ValidationError, match="privacy"):
        TriagePayload(
            answers=TriageAnswers(**_VALID_ANSWERS),
            consents=[
                ConsentEntry(type="privacy", accepted=False, policy_version="v1.0-2025-05"),
            ],
        )


# ---------------------------------------------------------------------------
# TriageResponse
# ---------------------------------------------------------------------------


def test_triage_response_valid():
    r = TriageResponse(lead_id="uuid-1234", bucket="auto_accept", message="OK")
    assert r.lead_id == "uuid-1234"
    assert r.bucket == "auto_accept"
