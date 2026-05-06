"""
tests/integration/test_intake_block_submit.py — T5.4

Integration tests for block submit, payload retrieval, and area selection.
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


async def _create_accepted_lead(client: AsyncClient, sid: str, user_id: str, email: str) -> str:
    payload = {
        "answers": {"full_name": "Block Tester", "email": email, "company_name": "BC", "phone": None, **_VALID_TRIAGE},
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


class TestAreaSelection:
    async def test_area_selection_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/intake/x/area-selection", json={})
        assert resp.status_code == 401

    async def test_area_selection_stores_primary_area(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.bs1@t.com", "bs-sid-11111111")
        lead_id = await _create_accepted_lead(client, sid, user.id, "bs.lead1@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        assert resp.json()["primary_area"] == "marketing"

    async def test_area_selection_cross_area_requires_areas_involved(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.bs2@t.com", "bs-sid-22222222")
        lead_id = await _create_accepted_lead(client, sid, user.id, "bs.lead2@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "cross_area_communication"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422

    async def test_area_selection_cross_area_with_areas_involved(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "area.bs3@t.com", "bs-sid-33333333")
        lead_id = await _create_accepted_lead(client, sid, user.id, "bs.lead3@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "cross_area_communication", "areas_involved": ["sales", "marketing"]},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200


class TestBlockSubmit:
    async def test_block_submit_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/intake/x/blocks/block-1-strategic/submit", json={"payload": {}})
        assert resp.status_code == 401

    async def test_block_submit_creates_block_analysis(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "sub.bs1@t.com", "bs-sub-11111111")
        lead_id = await _create_accepted_lead(client, sid, user.id, "sub.lead1@t.com")
        await client.post(f"/api/intake/{lead_id}/area-selection", json={"primary_area": "marketing"}, cookies={"admin_sid": sid})
        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total", "q1_3_previous": "first_time"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()
        assert "block_analysis_id" in data
        assert data["status"] in ("submitted", "pending_analysis")

    async def test_block_submit_stores_payload(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "sub.bs2@t.com", "bs-sub-22222222")
        lead_id = await _create_accepted_lead(client, sid, user.id, "sub.lead2@t.com")
        await client.post(f"/api/intake/{lead_id}/area-selection", json={"primary_area": "operations"}, cookies={"admin_sid": sid})
        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        resp = await client.get(f"/api/intake/{lead_id}/blocks/block-1-strategic/payload", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        assert resp.json()["payload"]["q1_2_sponsor"] == "ceo_total"

    async def test_block_resubmit_replaces_previous(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "sub.bs3@t.com", "bs-sub-33333333")
        lead_id = await _create_accepted_lead(client, sid, user.id, "sub.lead3@t.com")
        await client.post(f"/api/intake/{lead_id}/area-selection", json={"primary_area": "marketing"}, cookies={"admin_sid": sid})
        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "director_cto"}},
            cookies={"admin_sid": sid},
        )
        resp = await client.get(f"/api/intake/{lead_id}/blocks/block-1-strategic/payload", cookies={"admin_sid": sid})
        assert resp.json()["payload"]["q1_2_sponsor"] == "director_cto"

    async def test_session_created_on_accept(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "sub.bs4@t.com", "bs-sub-44444444")
        lead_id = await _create_accepted_lead(client, sid, user.id, "sub.lead4@t.com")
        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        assert resp.json()["state"] in ("not_started", "in_progress")


# ---------------------------------------------------------------------------
# TA.1 — REQ-3: _delete_draft raises after commit; 202 + completion persists
# ---------------------------------------------------------------------------

class TestSubmitDeleteDraftBestEffort:
    """REQ-3: draft cleanup is best-effort; block completion must survive _delete_draft failure."""

    async def test_submit_returns_202_even_if_delete_draft_raises(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        TA.1: If _delete_draft raises AFTER mark_block_completed is committed,
        the submit handler must still return 202.
        """
        import app.api.intake_routes as intake_module

        async def _failing_delete_draft(db, lead_id, block_id):
            raise RuntimeError("simulated draft delete failure")

        monkeypatch.setattr(intake_module, "_delete_draft", _failing_delete_draft)

        user, sid = await _create_admin_session(test_db, "req3.a@t.com", "req3-sid-aaaa0001")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req3.lead.a@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, resp.text

    async def test_blocks_completed_persists_even_if_delete_draft_raises(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        TA.1: blocks_completed row must be durable in DB even if _delete_draft raises.
        """
        import app.api.intake_routes as intake_module

        async def _failing_delete_draft(db, lead_id, block_id):
            raise RuntimeError("simulated draft delete failure")

        monkeypatch.setattr(intake_module, "_delete_draft", _failing_delete_draft)

        user, sid = await _create_admin_session(test_db, "req3.b@t.com", "req3-sid-bbbb0002")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req3.lead.b@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )

        state_resp = await client.get(
            f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid}
        )
        assert state_resp.status_code == 200
        assert "block-1-strategic" in state_resp.json()["blocks_completed"]


# ---------------------------------------------------------------------------
# TA.5 — REQ-6: unknown block_id returns 404 on all four routes
# ---------------------------------------------------------------------------

class TestBlockIdValidation:
    """REQ-6: all block-scoped routes must 404 on unknown block_id."""

    async def test_submit_unknown_block_id_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "req6.a@t.com", "req6-sid-aaaa0001")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req6.lead.a@t.com")
        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-nonexistent/submit",
            json={"payload": {}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404

    async def test_draft_put_unknown_block_id_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "req6.b@t.com", "req6-sid-bbbb0002")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req6.lead.b@t.com")
        resp = await client.put(
            f"/api/intake/{lead_id}/blocks/block-nonexistent/draft",
            json={"payload": {}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404

    async def test_payload_get_unknown_block_id_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "req6.c@t.com", "req6-sid-cccc0003")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req6.lead.c@t.com")
        # First create a session (area-selection) so we don't get session_not_found
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )
        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/block-nonexistent/payload",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404

    async def test_analysis_get_unknown_block_id_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "req6.d@t.com", "req6-sid-dddd0004")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req6.lead.d@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )
        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/block-nonexistent/analysis",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404

    async def test_submit_valid_block_id_still_works(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Regression: valid block_id must not be blocked by the new validation."""
        user, sid = await _create_admin_session(test_db, "req6.e@t.com", "req6-sid-eeee0005")
        lead_id = await _create_accepted_lead(client, sid, user.id, "req6.lead.e@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )
        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202
