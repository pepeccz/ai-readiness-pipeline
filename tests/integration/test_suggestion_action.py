"""
tests/integration/test_suggestion_action.py — T6.9

Tests for POST /api/intake/{lead_id}/suggestions/{suggestion_id}/action:
  - Valid action (done/discarded/irrelevant) persists consultant_action
  - Invalid action → 422
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
from app.models.lead import Lead
from app.models.session_row import SessionRow
from app.models.suggestion import Suggestion
from app.models.user import User


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
        id=sid, user_id=user.id,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
        last_seen_at=datetime.now(tz=timezone.utc),
        revoked_at=None,
    )
    db.add(s)
    await db.commit()
    return user, sid


async def _create_accepted_lead(client: AsyncClient, sid: str, user_id: str, email: str) -> str:
    payload = {
        "answers": {"full_name": "Sug Tester", "email": email, "company_name": "SC", "phone": None, **_VALID_TRIAGE},
        "consents": [{"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}],
    }
    resp = await client.post("/api/public/triage/submit", json=payload)
    assert resp.status_code == 201, resp.text
    lead_id = resp.json()["lead_id"]
    resp2 = await client.patch(
        f"/api/admin/leads/{lead_id}",
        json={"action": "accept", "consultant_id": user_id},
        cookies={"admin_sid": sid},
    )
    assert resp2.status_code == 200, resp2.text
    return lead_id


async def _create_suggestion(db: AsyncSession, lead_id: str) -> str:
    session_stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    result = await db.execute(session_stmt)
    session = result.scalar_one_or_none()
    if session is None:
        session = IntakeSession(
            lead_id=lead_id,
            primary_area="ventas",
            state="in_progress",
            blocks_completed=[],
        )
        db.add(session)
        await db.flush()

    ba = BlockAnalysis(
        intake_session_id=session.id,
        block_id="block-1-strategic",
        payload={"q1": "Automatizar"},
        status="ready",
        llm_output={"synthesis": "Test"},
    )
    db.add(ba)
    await db.flush()

    suggestion = Suggestion(
        block_analysis_id=ba.id,
        type="follow_up",
        text="¿Quién tiene autoridad presupuestaria para el piloto?",
        rationale="No hay sponsor claro en las respuestas",
        confidence=0.85,
        priority="high",
        consultant_action="pending",
    )
    db.add(suggestion)
    await db.flush()
    await db.commit()

    return suggestion.id


class TestSuggestionAction:
    """T6.9 — consultant action persists correctly."""

    async def test_valid_action_done_persists(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin_sug1@test.com", "sid-sug1")
        lead_id = await _create_accepted_lead(client, sid, str(user.id), "lead_sug1@test.com")
        sug_id = await _create_suggestion(test_db, lead_id)

        resp = await client.post(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/action",
            json={"action": "done"},
            cookies={"admin_sid": sid},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["consultant_action"] == "done"

    async def test_invalid_action_returns_422(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin_sug2@test.com", "sid-sug2")
        lead_id = await _create_accepted_lead(client, sid, str(user.id), "lead_sug2@test.com")
        sug_id = await _create_suggestion(test_db, lead_id)

        resp = await client.post(
            f"/api/intake/{lead_id}/suggestions/{sug_id}/action",
            json={"action": "invalid_action"},
            cookies={"admin_sid": sid},
        )

        assert resp.status_code == 422
