"""
tests/integration/test_client_deep_form — T8.1

Integration tests for public client DEEP form endpoints (Batch 8).

Endpoints under test:
  GET  /api/client/deep/{signed_token}          — fetch DEEP questions
  POST /api/client/deep/{signed_token}/submit   — submit branch responses

Token type: signed URL with payload {lead_id, branch_ids, purpose="deep_form"}
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.session_row import SessionRow
from app.models.user import User

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_TRIAGE = {
    "sector": "tecnologia",
    "company_size": "26_100",
    "respondent_role": "ceo_fundador",
    "ai_maturity": "pilotos",
    "urgency": "alta",
    "ai_goals": ["automatizar_procesos"],
    "commitment": "agendar",
}


async def _create_admin_session(
    db: AsyncSession, email: str, sid: str
) -> tuple[User, str]:
    from app.auth.password import hash_password

    user = User(email=email, password_hash=hash_password("pass123"), is_active=True)
    db.add(user)
    await db.flush()
    s = SessionRow(
        id=sid,
        user_id=user.id,
        expires_at=datetime.now(tz=timezone.utc).replace(year=2028),
        last_seen_at=datetime.now(tz=timezone.utc),
        revoked_at=None,
    )
    db.add(s)
    await db.commit()
    return user, sid


async def _create_accepted_lead_with_session(
    client: AsyncClient,
    db: AsyncSession,
    sid: str,
    user_id: str,
    lead_email: str,
) -> tuple[str, str]:
    """Create a triage lead, accept it, and return (lead_id, session_id)."""
    payload = {
        "answers": {
            "full_name": "Deep Client",
            "email": lead_email,
            "company_name": "DEEP Corp",
            "phone": None,
            **_VALID_TRIAGE,
        },
        "consents": [
            {"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}
        ],
    }
    resp = await client.post("/api/public/triage/submit", json=payload)
    assert resp.status_code == 201, resp.text
    lead_id = resp.json()["lead_id"]

    resp2 = await client.patch(
        f"/api/admin/leads/{lead_id}",
        json={"action": "accept", "consultant_id": str(user_id)},
        cookies={"admin_sid": sid},
    )
    assert resp2.status_code == 200, resp2.text

    # Get the intake session
    result = await db.execute(
        select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    )
    session = result.scalar_one()
    return lead_id, session.id


async def _create_deep_branch(
    db: AsyncSession, session_id: str, branch_id: str, status: str = "sent_to_client"
) -> DeepBranch:
    """Insert a DeepBranch row with the given status."""
    branch = DeepBranch(
        intake_session_id=session_id,
        branch_id=branch_id,
        generated_questions=[
            {"id": "q1", "text": "¿Cuál es tu mayor reto IA?", "rationale": "strategic"},
            {"id": "q2", "text": "¿Tienes datos estructurados?", "rationale": "data"},
        ],
        status=status,
    )
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


def _make_deep_token(lead_id: str, branch_ids: list[str], ttl_seconds: int = 86400 * 90) -> str:
    """Generate a valid signed token for the DEEP form."""
    from app.signed_urls import sign_payload

    return sign_payload(
        {"lead_id": lead_id, "branch_ids": branch_ids, "purpose": "deep_form"},
        ttl_seconds=ttl_seconds,
    )


def _make_expired_deep_token(lead_id: str, branch_ids: list[str]) -> str:
    """Generate an already-expired token."""
    from app.signed_urls import sign_payload

    return sign_payload(
        {"lead_id": lead_id, "branch_ids": branch_ids, "purpose": "deep_form"},
        ttl_seconds=-1,  # already in the past
    )


# ---------------------------------------------------------------------------
# GET /api/client/deep/{token} — fetch questions
# ---------------------------------------------------------------------------


class TestClientDeepGet:
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/client/deep/not-a-real-token")
        assert resp.status_code == 401

    async def test_tampered_token_returns_401(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.tamper@t.com", "deep-sid-tamper01"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.tamper.lead@t.com"
        )
        token = _make_deep_token(lead_id, [])
        # tamper last character
        tampered = token[:-1] + ("x" if token[-1] != "x" else "y")
        resp = await client.get(f"/api/client/deep/{tampered}")
        assert resp.status_code == 401

    async def test_expired_token_returns_401(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.exp@t.com", "deep-sid-expired01"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.exp.lead@t.com"
        )
        token = _make_expired_deep_token(lead_id, [])
        resp = await client.get(f"/api/client/deep/{token}")
        assert resp.status_code == 401

    async def test_valid_token_returns_branches(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.valid@t.com", "deep-sid-valid001"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.valid.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "strategic")
        token = _make_deep_token(lead_id, [branch.id])

        resp = await client.get(f"/api/client/deep/{token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["lead_id"] == lead_id
        assert len(data["deep_branches"]) == 1
        b = data["deep_branches"][0]
        assert b["branch_id"] == "strategic"
        assert len(b["generated_questions"]) == 2

    async def test_valid_token_returns_status(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.status@t.com", "deep-sid-status01"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.status.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "data")
        token = _make_deep_token(lead_id, [branch.id])

        resp = await client.get(f"/api/client/deep/{token}")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data


# ---------------------------------------------------------------------------
# POST /api/client/deep/{token}/submit — submit responses
# ---------------------------------------------------------------------------


class TestClientDeepSubmit:
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/client/deep/bad-token/submit",
            json={"branch_id": "x", "responses": {}},
        )
        assert resp.status_code == 401

    async def test_submit_persists_client_responses(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.sub@t.com", "deep-sid-sub00001"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.sub.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "strategic")
        token = _make_deep_token(lead_id, [branch.id])

        responses = {"q1": "Automatizar procesos repetitivos", "q2": "Sí, tenemos un data lake"}
        resp = await client.post(
            f"/api/client/deep/{token}/submit",
            json={"branch_id": branch.id, "responses": responses},
        )
        assert resp.status_code == 200

        # Verify DB state
        await test_db.refresh(branch)
        assert branch.client_responses == responses
        assert branch.status == "received"
        assert branch.received_at is not None

    async def test_submit_last_branch_transitions_session_state(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.last@t.com", "deep-sid-last0001"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.last.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "governance")
        token = _make_deep_token(lead_id, [branch.id])

        resp = await client.post(
            f"/api/client/deep/{token}/submit",
            json={"branch_id": branch.id, "responses": {"q1": "Respuesta"}},
        )
        assert resp.status_code == 200

        # Session state must transition to deep_received
        await test_db.refresh(branch)
        result = await test_db.execute(
            select(IntakeSession).where(IntakeSession.id == session_id)
        )
        session = result.scalar_one()
        assert session.state == "deep_received"

    async def test_submit_partial_branches_does_not_transition(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "deep.part@t.com", "deep-sid-part0001"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.part.lead@t.com"
        )
        branch1 = await _create_deep_branch(test_db, session_id, "strategic")
        branch2 = await _create_deep_branch(test_db, session_id, "data")
        token = _make_deep_token(lead_id, [branch1.id, branch2.id])

        # Submit only branch1
        resp = await client.post(
            f"/api/client/deep/{token}/submit",
            json={"branch_id": branch1.id, "responses": {"q1": "Answer1"}},
        )
        assert resp.status_code == 200

        # Session state should NOT be deep_received yet
        result = await test_db.execute(
            select(IntakeSession).where(IntakeSession.id == session_id)
        )
        session = result.scalar_one()
        assert session.state != "deep_received"

    async def test_submit_sends_confirmation_email(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        sent = []

        async def mock_send_email(to, subject, body):
            sent.append({"to": to, "subject": subject})
            return True

        from app.email import sender
        monkeypatch.setattr(sender, "send_email", mock_send_email)

        user, sid = await _create_admin_session(
            test_db, "deep.email@t.com", "deep-sid-email001"
        )
        lead_id, session_id = await _create_accepted_lead_with_session(
            client, test_db, sid, user.id, "deep.email.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "strategic")
        token = _make_deep_token(lead_id, [branch.id])

        await client.post(
            f"/api/client/deep/{token}/submit",
            json={"branch_id": branch.id, "responses": {"q1": "Answer"}},
        )

        # Email to lead must be queued (BackgroundTask executes inline in test)
        assert any("deep.email.lead@t.com" in m["to"] for m in sent)
