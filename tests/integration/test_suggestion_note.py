"""
tests/integration/test_suggestion_note.py — C-2 (REQ-4)

Tests for PATCH /api/intake/{lead_id}/suggestions/{suggestion_id}/note
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password
from app.models.block_analysis import BlockAnalysis
from app.models.intake_session import IntakeSession
from app.models.session_row import SessionRow
from app.models.suggestion import Suggestion
from app.models.user import User

pytestmark = pytest.mark.asyncio

_VALID_TRIAGE = {
    "sector": "tecnologia",
    "company_size": "26_100",
    "respondent_role": "ceo_fundador",
    "ai_maturity": "pilotos",
    "urgency": "alta",
    "ai_goals": ["automatizar_procesos"],
    "commitment": "agendar",
}


async def _create_admin_session(db: AsyncSession, email: str, sid: str) -> tuple[User, str]:
    user = User(email=email, password_hash=hash_password("pass123"), is_active=True)
    db.add(user)
    await db.flush()
    s = SessionRow(
        id=sid,
        user_id=user.id,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
        last_seen_at=datetime.now(tz=timezone.utc),
        revoked_at=None,
    )
    db.add(s)
    await db.commit()
    return user, sid


async def _create_accepted_lead(client: AsyncClient, db: AsyncSession, sid: str, user_id: str, email: str) -> str:
    payload = {
        "answers": {
            "full_name": "Note Tester",
            "email": email,
            "company_name": "NoteCo",
            "phone": None,
            **_VALID_TRIAGE,
        },
        "consents": [{"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}],
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
    return lead_id


async def _seed_suggestion(db: AsyncSession, lead_id: str) -> tuple[str, str]:
    """Create IntakeSession + BlockAnalysis + 1 Suggestion. Returns (lead_id, suggestion_id)."""
    stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        session = IntakeSession(
            lead_id=lead_id,
            primary_area="operations",
            state="in_progress",
            blocks_completed=["block-1-strategic"],
        )
        db.add(session)
        await db.flush()

    ba = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={"q1": "value"},
        status="ready",
        llm_output={"synthesis": "synthesis text"},
    )
    db.add(ba)
    await db.flush()

    sug = Suggestion(
        block_analysis_id=ba.id,
        type="follow_up",
        text="¿Cuál es el mayor bloqueante?",
        rationale="Tensión detectada en datos",
        confidence=0.9,
        priority="high",
        consultant_action="pending",
    )
    db.add(sug)
    await db.commit()
    return sug.id


class TestSuggestionNoteEndpoint:
    """C-2 — REQ-4: PATCH /intake/{lead_id}/suggestions/{suggestion_id}/note"""

    async def test_happy_path_saves_note(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import app.email.sender as email_sender

        async def _noop(to, subject, body):
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)

        user, sid = await _create_admin_session(test_db, "note_c2_1@test.com", "note-sid-11111111")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "note.lead1@test.com")
        sug_id = await _seed_suggestion(test_db, lead_id)

        resp = await client.patch(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/note",
            json={"note": "Client mentioned budget constraints"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"] == sug_id
        assert body["consultant_note_text"] == "Client mentioned budget constraints"

    async def test_clear_note_sets_null(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import app.email.sender as email_sender

        async def _noop(to, subject, body):
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)

        user, sid = await _create_admin_session(test_db, "note_c2_2@test.com", "note-sid-22222222")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "note.lead2@test.com")
        sug_id = await _seed_suggestion(test_db, lead_id)

        # First, set a note
        await client.patch(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/note",
            json={"note": "some note"},
            cookies={"admin_sid": sid},
        )
        # Then clear it
        resp = await client.patch(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/note",
            json={"note": None},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["consultant_note_text"] is None

    async def test_unknown_fields_do_not_corrupt_suggestion(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import app.email.sender as email_sender

        async def _noop(to, subject, body):
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)

        user, sid = await _create_admin_session(test_db, "note_c2_3@test.com", "note-sid-33333333")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "note.lead3@test.com")
        sug_id = await _seed_suggestion(test_db, lead_id)

        # Include unknown fields in the payload
        resp = await client.patch(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/note",
            json={"note": "valid note", "consultant_action": "hacked", "priority": "pwned"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Only note should change; consultant_action and priority must remain untouched
        assert body["consultant_note_text"] == "valid note"
        assert body["consultant_action"] == "pending"  # not 'hacked'
        assert body["priority"] == "high"  # not 'pwned'

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import app.email.sender as email_sender

        async def _noop(to, subject, body):
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)

        user, sid = await _create_admin_session(test_db, "note_c2_4@test.com", "note-sid-44444444")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "note.lead4@test.com")
        sug_id = await _seed_suggestion(test_db, lead_id)

        # No auth cookie
        resp = await client.patch(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/note",
            json={"note": "should fail"},
        )
        assert resp.status_code in (401, 403)
