"""
tests/unit/test_triage_emails.py — T3.4

Unit tests for TRIAGE email template functions (5 buckets + consultant notification).
"""

from app.services.email.triage_emails import (
    triage_email_for_bucket,
    triage_consultant_notification,
)


ALL_BUCKETS = ["auto_accept", "review", "cold_warm", "cold_cool", "reject_soft"]


def test_all_buckets_return_subject_and_body():
    for bucket in ALL_BUCKETS:
        subject, body = triage_email_for_bucket(bucket, full_name="Juan", company_name="Acme")
        assert isinstance(subject, str) and len(subject) > 0
        assert isinstance(body, str) and len(body) > 0


def test_auto_accept_mentions_call():
    subject, body = triage_email_for_bucket("auto_accept", full_name="María", company_name="X")
    # Should mention a consultant will call
    assert any(word in body.lower() for word in ["consultor", "llamar", "llamará", "contactar"])


def test_review_mentions_days():
    subject, body = triage_email_for_bucket("review", full_name="Pedro", company_name="X")
    assert any(word in body.lower() for word in ["día", "días", "plazo", "revisión", "revisar"])


def test_cold_warm_mentions_webinar_or_resources():
    subject, body = triage_email_for_bucket("cold_warm", full_name="X", company_name="X")
    assert any(word in body.lower() for word in ["webinar", "recurso", "recursos", "gratuito", "gratis"])


def test_cold_cool_mentions_checklist_or_nurturing():
    subject, body = triage_email_for_bucket("cold_cool", full_name="X", company_name="X")
    assert any(word in body.lower() for word in ["checklist", "madurez", "recursos", "preparar"])


def test_reject_soft_soft_language():
    subject, body = triage_email_for_bucket("reject_soft", full_name="X", company_name="X")
    assert any(word in body.lower() for word in ["momento", "futuro", "formativo", "contacto"])


def test_unknown_bucket_raises():
    import pytest
    with pytest.raises(ValueError):
        triage_email_for_bucket("invalid_bucket", full_name="X", company_name="X")


def test_consultant_notification_returns_tuple():
    subject, body = triage_consultant_notification(
        full_name="Ana", company_name="Acme SL", bucket="auto_accept", lead_id="uuid-123"
    )
    assert isinstance(subject, str)
    assert "auto_accept" in body or "Acme SL" in body
