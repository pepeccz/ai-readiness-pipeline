"""
tests/integration/test_intake_area_selection.py — T5.5

Integration tests for area selection + schema personalization flow.
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
    "ai_maturity": "pilotos",
    "urgency": "alta",
    "ai_goals": ["automatizar_procesos"],
    "commitment": "agendar",
}


async def _create_admin_session(db: AsyncSession, email: str, sid: str) -> tuple[User, str]:
    from app.auth.password import hash_password
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


async def _accepted_lead_id(client: AsyncClient, sid: str, user_id: str, email: str) -> str:
    payload = {
        "answers": {"full_name": "Area Tester", "email": email, "company_name": "AC", "phone": None, **_VALID_TRIAGE},
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


class TestAreaSelectionFlow:
    async def test_full_area_selection_flow(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.af1@t.com", "af-sid-11111111")
        lead_id = await _accepted_lead_id(client, sid, user.id, "af.lead1@t.com")
        resp = await client.post(f"/api/intake/{lead_id}/area-selection", json={"primary_area": "sales"}, cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["primary_area"] == "sales"
        assert data.get("secondary_area") is None

    async def test_secondary_area_stored(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.af2@t.com", "af-sid-22222222")
        lead_id = await _accepted_lead_id(client, sid, user.id, "af.lead2@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing", "secondary_area": "sales"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        assert resp.json()["secondary_area"] == "sales"

    async def test_schema_reflects_area_selection(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.af3@t.com", "af-sid-33333333")
        lead_id = await _accepted_lead_id(client, sid, user.id, "af.lead3@t.com")
        await client.post(f"/api/intake/{lead_id}/area-selection", json={"primary_area": "finance"}, cookies={"admin_sid": sid})
        resp = await client.get(f"/api/intake/{lead_id}/schema", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert "blocks_order" in data or "blocks" in data

    async def test_cross_area_disables_secondary(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.af4@t.com", "af-sid-44444444")
        lead_id = await _accepted_lead_id(client, sid, user.id, "af.lead4@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "cross_area_communication", "areas_involved": ["sales", "marketing", "operations"]},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("secondary_area") is None
        assert data.get("areas_involved") == ["sales", "marketing", "operations"]

    async def test_area_selection_invalid_primary_area(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.af5@t.com", "af-sid-55555555")
        lead_id = await _accepted_lead_id(client, sid, user.id, "af.lead5@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "nonexistent_area"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422
