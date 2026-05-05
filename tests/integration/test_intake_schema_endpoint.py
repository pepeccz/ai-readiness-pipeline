"""
tests/integration/test_intake_schema_endpoint.py — T5.3

Integration tests for GET /api/intake/{lead_id}/schema + state
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_row import SessionRow
from app.models.user import User


pytestmark = pytest.mark.asyncio

_VALID_TRIAGE = {
    "sector": "tecnologia",
    "company_size": "26_100",
    "respondent_role": "ceo_fundador",
    "ai_maturity": "exploracion",
    "urgency": "alta",
    "ai_goals": ["automatizar_procesos"],
    "commitment": "agendar",
}


async def _create_admin_session(db: AsyncSession, email: str = "admin.schema@test.com", sid: str = "schema-session-12345678") -> tuple[User, str]:
    from app.auth.password import hash_password
    user = User(email=email, password_hash=hash_password("pass123"), is_active=True)
    db.add(user)
    await db.flush()
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


async def _create_accepted_lead(client: AsyncClient, sid: str, user_id: str, email: str = "consultor.schema@test.com") -> str:
    payload = {
        "answers": {"full_name": "Test Consultor", "email": email, "company_name": "TestCorp", "phone": None, **_VALID_TRIAGE},
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


class TestIntakeSchemaEndpoint:
    async def test_schema_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/intake/nonexistent/schema")
        assert resp.status_code == 401

    async def test_schema_404_for_unknown_lead(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db)
        resp = await client.get("/api/intake/nonexistent-lead-id/schema", cookies={"admin_sid": sid})
        assert resp.status_code == 404

    async def test_schema_403_for_pending_lead(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin2.schema@test.com", "schema-session-22222222")
        payload = {
            "answers": {"full_name": "Pending", "email": "pending.schema@test.com", "company_name": "P", "phone": None, **_VALID_TRIAGE},
            "consents": [{"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}],
        }
        resp = await client.post("/api/public/triage/submit", json=payload)
        assert resp.status_code == 201
        lead_id = resp.json()["lead_id"]
        resp2 = await client.get(f"/api/intake/{lead_id}/schema", cookies={"admin_sid": sid})
        assert resp2.status_code == 403

    async def test_schema_returns_core_for_accepted_lead(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin3.schema@test.com", "schema-session-33333333")
        lead_id = await _create_accepted_lead(client, sid, user.id, "schema3@test.com")
        resp = await client.get(f"/api/intake/{lead_id}/schema", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert "blocks_order" in data
        assert "area_selector" in data

    async def test_schema_with_area_param_returns_personalized(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin4.schema@test.com", "schema-session-44444444")
        lead_id = await _create_accepted_lead(client, sid, user.id, "schema4@test.com")
        resp = await client.get(f"/api/intake/{lead_id}/schema?area=marketing", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert "blocks" in data


class TestIntakeStateEndpoint:
    async def test_state_returns_session_info(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin5.schema@test.com", "schema-session-55555555")
        lead_id = await _create_accepted_lead(client, sid, user.id, "schema5@test.com")
        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data
        assert "blocks_completed" in data
