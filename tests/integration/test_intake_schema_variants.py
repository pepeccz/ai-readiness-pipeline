"""
tests/integration/test_intake_schema_variants.py — T1.8

Tests for REQ-10: intake schema endpoint does NOT return b2_id or block_2_variants keys;
area-based variant selection is applied correctly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password
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


async def _create_accepted_lead(client: AsyncClient, sid: str, user_id: str, email: str) -> str:
    payload = {
        "answers": {
            "full_name": "Variant Tester",
            "email": email,
            "company_name": "VarCo",
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


class TestIntakeSchemaVariants:
    async def test_response_does_not_contain_b2_id(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Response must NOT contain raw b2_id key."""
        import app.email.sender as email_sender

        async def _noop(to: str, subject: str, body: str) -> bool:
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)
        user, sid = await _create_admin_session(test_db, "var1@test.com", "var-sid-11111111")
        lead_id = await _create_accepted_lead(client, sid, str(user.id), "varleada@test.com")

        resp = await client.get(
            f"/api/intake/{lead_id}/schema?area=marketing",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "b2_id" not in body, f"Response must not contain b2_id. Got: {list(body.keys())}"

    async def test_response_does_not_contain_block_2_variants(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Response must NOT contain raw block_2_variants key."""
        import app.email.sender as email_sender

        async def _noop(to: str, subject: str, body: str) -> bool:
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)
        user, sid = await _create_admin_session(test_db, "var2@test.com", "var-sid-22222222")
        lead_id = await _create_accepted_lead(client, sid, str(user.id), "varleadb@test.com")

        resp = await client.get(
            f"/api/intake/{lead_id}/schema?area=operations",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "block_2_variants" not in body, (
            f"Response must not contain block_2_variants. Got: {list(body.keys())}"
        )

    async def test_blocks_included_when_area_provided(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When area is provided, response must include blocks list."""
        import app.email.sender as email_sender

        async def _noop(to: str, subject: str, body: str) -> bool:
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)
        user, sid = await _create_admin_session(test_db, "var3@test.com", "var-sid-33333333")
        lead_id = await _create_accepted_lead(client, sid, str(user.id), "varleadc@test.com")

        resp = await client.get(
            f"/api/intake/{lead_id}/schema?area=sales",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # blocks key should be present when area is given
        assert "blocks" in body or "blocks_order" in body

    async def test_no_area_returns_area_selector(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without area param, only blocks_order and area_selector are returned."""
        import app.email.sender as email_sender

        async def _noop(to: str, subject: str, body: str) -> bool:
            return True

        monkeypatch.setattr(email_sender, "send_email", _noop)
        user, sid = await _create_admin_session(test_db, "var4@test.com", "var-sid-44444444")
        lead_id = await _create_accepted_lead(client, sid, str(user.id), "varleadd@test.com")

        resp = await client.get(
            f"/api/intake/{lead_id}/schema",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "area_selector" in body
        assert "b2_id" not in body
        assert "block_2_variants" not in body
