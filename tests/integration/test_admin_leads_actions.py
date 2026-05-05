"""
tests/integration/test_admin_leads_actions.py

Integration tests for PATCH /api/admin/leads/{id} actions.

Covers:
- 401 without auth
- 404 for nonexistent lead
- action=accept: changes status, requires consultant_id
- action=accept: dispatches email (mocked)
- action=reject: requires reason, changes status
- action=reject: dispatches email (mocked)
- action=request_extra_info: keeps status=pending_review
- action=assign_consultant: sets assigned_consultant_id
- 409 when action is invalid for current status
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.session_row import SessionRow
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_lead(
    *,
    status: str = "pending_review",
    triage_bucket: str = "review",
) -> Lead:
    return Lead(
        full_name="Test Lead",
        email="lead@test.com",
        company_name="TestCo",
        phone=None,
        sector="tecnologia",
        company_size="10_25",
        respondent_role="ceo",
        ai_maturity="exploracion",
        ai_goals=["eficiencia"],
        urgency="normal",
        commitment="explorar",
        triage_payload={"answers": {}},
        triage_score=65,
        triage_bucket=triage_bucket,
        status=status,
        created_at=datetime.now(tz=timezone.utc),
    )


async def _create_admin_session(db: AsyncSession) -> tuple[User, str]:
    from app.auth.password import hash_password

    user = User(
        email="admin@test.com",
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    sid = "test-session-id-12345678"
    session = SessionRow(
        id=sid,
        user_id=user.id,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
        last_seen_at=datetime.now(tz=timezone.utc),
        revoked_at=None,
    )
    db.add(session)
    await db.commit()
    return user, sid


# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_lead_requires_auth(client: AsyncClient) -> None:
    """PATCH without session cookie returns 401."""
    resp = await client.patch(
        "/api/admin/leads/some-id",
        json={"action": "accept", "consultant_id": "abc"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_patch_lead_not_found(client: AsyncClient, test_db: AsyncSession) -> None:
    """PATCH for nonexistent lead returns 404."""
    _, sid = await _create_admin_session(test_db)

    resp = await client.patch(
        "/api/admin/leads/nonexistent",
        json={"action": "accept", "consultant_id": "abc"},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# T4.4 - action=accept
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_accept_lead(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """action=accept changes status to accepted."""
    user, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    # Mock email sender so we don't need SMTP
    import app.email.sender as email_sender
    emails_sent: list[dict] = []

    async def mock_send(to: str, subject: str, body: str) -> bool:
        emails_sent.append({"to": to, "subject": subject})
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "accept", "consultant_id": str(user.id)},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead"]["status"] == "accepted"

    # Reload from DB
    await test_db.refresh(lead)
    assert lead.status == "accepted"
    assert lead.accepted_at is not None


@pytest.mark.asyncio
async def test_accept_lead_sends_email(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """action=accept dispatches acceptance email."""
    user, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    import app.email.sender as email_sender
    emails_sent: list[dict] = []

    async def mock_send(to: str, subject: str, body: str) -> bool:
        emails_sent.append({"to": to, "subject": subject})
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "accept", "consultant_id": str(user.id)},
        cookies={"admin_sid": sid},
    )

    assert len(emails_sent) == 1
    assert emails_sent[0]["to"] == lead.email


@pytest.mark.asyncio
async def test_accept_lead_requires_consultant_id(
    client: AsyncClient, test_db: AsyncSession
) -> None:
    """action=accept without consultant_id returns 422."""
    _, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "accept"},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# T4.5 - action=reject
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_lead(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """action=reject changes status to rejected with predefined reason."""
    _, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    import app.email.sender as email_sender

    async def mock_send(to: str, subject: str, body: str) -> bool:
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "reject", "reason": "not_qualified_size"},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead"]["status"] == "rejected"

    await test_db.refresh(lead)
    assert lead.status == "rejected"
    assert lead.rejected_reason == "not_qualified_size"


@pytest.mark.asyncio
async def test_reject_lead_requires_reason(
    client: AsyncClient, test_db: AsyncSession
) -> None:
    """action=reject without reason returns 422."""
    _, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "reject"},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_lead_sends_email(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """action=reject dispatches rejection email."""
    _, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    import app.email.sender as email_sender
    emails_sent: list[dict] = []

    async def mock_send(to: str, subject: str, body: str) -> bool:
        emails_sent.append({"to": to, "subject": subject})
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "reject", "reason": "out_of_sector"},
        cookies={"admin_sid": sid},
    )

    assert len(emails_sent) == 1
    assert emails_sent[0]["to"] == lead.email


# ---------------------------------------------------------------------------
# T4.3 - action=request_extra_info
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_extra_info(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """action=request_extra_info keeps status=pending_review."""
    _, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    import app.email.sender as email_sender

    async def mock_send(to: str, subject: str, body: str) -> bool:
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "request_extra_info"},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead"]["status"] == "pending_review"


# ---------------------------------------------------------------------------
# T4.6 - action=assign_consultant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assign_consultant(
    client: AsyncClient, test_db: AsyncSession
) -> None:
    """action=assign_consultant sets assigned_consultant_id."""
    user, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="pending_review")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "assign_consultant", "consultant_id": str(user.id)},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lead"]["assigned_consultant_id"] == str(user.id)

    await test_db.refresh(lead)
    # assigned_consultant_id may come back as UUID object from SQLAlchemy
    assert str(lead.assigned_consultant_id) == str(user.id)


# ---------------------------------------------------------------------------
# 409 - Invalid action for current status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_accept_already_accepted_lead_returns_409(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accepting an already-accepted lead returns 409."""
    user, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="accepted")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    import app.email.sender as email_sender

    async def mock_send(to: str, subject: str, body: str) -> bool:
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "accept", "consultant_id": str(user.id)},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_accept_rejected_lead_returns_409(
    client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accepting a rejected lead returns 409."""
    user, sid = await _create_admin_session(test_db)

    lead = _make_lead(status="rejected")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    import app.email.sender as email_sender

    async def mock_send(to: str, subject: str, body: str) -> bool:
        return True

    monkeypatch.setattr(email_sender, "send_email", mock_send)

    resp = await client.patch(
        f"/api/admin/leads/{lead.id}",
        json={"action": "accept", "consultant_id": str(user.id)},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 409
