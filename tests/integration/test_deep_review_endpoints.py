"""
tests/integration/test_deep_review_endpoints — T7.6

Integration tests for consultant DEEP review endpoints.

Endpoints:
  GET   /api/intake/{lead_id}/deep               — list DeepBranch rows
  PATCH /api/intake/{lead_id}/deep/{branch_id}   — edit questions
  POST  /api/intake/{lead_id}/deep/{branch_id}/send — send to client

Auth: admin session cookie (same as all intake endpoints).
"""

from __future__ import annotations

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
# Fixtures / helpers
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


async def _create_accepted_lead(
    client: AsyncClient, db: AsyncSession, sid: str, user_id: str, email: str
) -> tuple[str, str]:
    """Create lead via triage, accept it. Returns (lead_id, session_id)."""
    payload = {
        "answers": {
            "full_name": "Test User",
            "email": email,
            "company_name": "DEEP Inc",
            "phone": None,
            **_VALID_TRIAGE,
        },
        "consents": [
            {"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}
        ],
    }
    r = await client.post("/api/public/triage/submit", json=payload)
    assert r.status_code == 201, r.text
    lead_id = r.json()["lead_id"]

    r2 = await client.patch(
        f"/api/admin/leads/{lead_id}",
        json={"action": "accept", "consultant_id": str(user_id)},
        cookies={"admin_sid": sid},
    )
    assert r2.status_code == 200, r2.text

    result = await db.execute(
        select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    )
    session = result.scalar_one()
    return lead_id, session.id


async def _create_deep_branch(
    db: AsyncSession,
    session_id: str,
    branch_id: str = "strategic",
    status: str = "pending_review",
) -> DeepBranch:
    branch = DeepBranch(
        intake_session_id=session_id,
        branch_id=branch_id,
        generated_questions=[
            {"id": "dq1", "text": "¿Cuál es el objetivo principal?", "rationale": "r1"},
            {"id": "dq2", "text": "¿Qué datos disponés?", "rationale": "r2"},
        ],
        status=status,
    )
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


# ---------------------------------------------------------------------------
# GET /api/intake/{lead_id}/deep
# ---------------------------------------------------------------------------


class TestDeepList:
    async def test_returns_empty_list_when_no_branches(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "dl.empty@t.com", "dl-sid-empty01")
        lead_id, _ = await _create_accepted_lead(client, test_db, sid, user.id, "dl.empty.lead@t.com")

        resp = await client.get(
            f"/api/intake/{lead_id}/deep",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["branches"] == []

    async def test_returns_all_branches(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "dl.all@t.com", "dl-sid-all001")
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "dl.all.lead@t.com"
        )
        await _create_deep_branch(test_db, session_id, "strategic")
        await _create_deep_branch(test_db, session_id, "governance")

        resp = await client.get(
            f"/api/intake/{lead_id}/deep",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["branches"]) == 2

    async def test_returns_branch_fields(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "dl.fields@t.com", "dl-sid-fields1")
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "dl.fields.lead@t.com"
        )
        await _create_deep_branch(test_db, session_id, "data")

        resp = await client.get(
            f"/api/intake/{lead_id}/deep",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        branch = resp.json()["branches"][0]
        assert "branch_id" in branch
        assert "status" in branch
        assert "generated_questions" in branch
        assert branch["branch_id"] == "data"

    async def test_requires_auth(self, client: AsyncClient, test_db: AsyncSession):
        resp = await client.get("/api/intake/nonexistent/deep")
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# PATCH /api/intake/{lead_id}/deep/{branch_id}
# ---------------------------------------------------------------------------


class TestDeepPatch:
    async def test_updates_questions(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "dp.upd@t.com", "dp-sid-upd001")
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "dp.upd.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "strategic")

        new_questions = [
            {"id": "dq1", "text": "Pregunta editada 1", "rationale": "r-edited"},
            {"id": "dq2", "text": "Pregunta editada 2", "rationale": "r-edited-2"},
        ]
        resp = await client.patch(
            f"/api/intake/{lead_id}/deep/{branch.id}",
            json={"questions": new_questions},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["generated_questions"]) == 2
        assert data["generated_questions"][0]["text"] == "Pregunta editada 1"

    async def test_returns_404_for_unknown_branch(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "dp.404@t.com", "dp-sid-4040001")
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "dp.404.lead@t.com"
        )

        resp = await client.patch(
            f"/api/intake/{lead_id}/deep/nonexistent-branch-uuid",
            json={"questions": []},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404

    async def test_persists_original_questions_as_edits(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "dp.orig@t.com", "dp-sid-orig01")
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "dp.orig.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "governance")
        original_questions = branch.generated_questions[:]

        await client.patch(
            f"/api/intake/{lead_id}/deep/{branch.id}",
            json={"questions": [{"id": "dq1", "text": "Nueva pregunta"}]},
            cookies={"admin_sid": sid},
        )

        await test_db.refresh(branch)
        assert branch.consultant_edits == original_questions


# ---------------------------------------------------------------------------
# POST /api/intake/{lead_id}/deep/{branch_id}/send
# ---------------------------------------------------------------------------


class TestDeepSend:
    async def test_send_returns_200_with_signed_url(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        sent = []

        async def mock_send_email(to, subject, body):
            sent.append({"to": to})

        from app.email import sender
        monkeypatch.setattr(sender, "send_email", mock_send_email)

        user, sid = await _create_admin_session(test_db, "ds.ok@t.com", "ds-sid-ok0001")
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "ds.ok.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "strategic")

        resp = await client.post(
            f"/api/intake/{lead_id}/deep/{branch.id}/send",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "signed_url" in data
        assert "sent_to" in data
        assert "expires_at" in data

    async def test_send_marks_branch_status(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        async def mock_send_email(to, subject, body):
            pass

        from app.email import sender
        monkeypatch.setattr(sender, "send_email", mock_send_email)

        user, sid = await _create_admin_session(test_db, "ds.st@t.com", "ds-sid-st0001")
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "ds.st.lead@t.com"
        )
        branch = await _create_deep_branch(test_db, session_id, "governance")

        await client.post(
            f"/api/intake/{lead_id}/deep/{branch.id}/send",
            cookies={"admin_sid": sid},
        )

        await test_db.refresh(branch)
        assert branch.status == "sent_to_client"
        assert branch.sent_to_client_at is not None
        assert branch.signed_token is not None

    async def test_send_returns_404_for_unknown_branch(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "ds.404@t.com", "ds-sid-404001")
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "ds.404.lead@t.com"
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/deep/nonexistent-uuid/send",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404
