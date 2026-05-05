"""
tests/integration/test_block_draft.py — TDD RED phase for BlockDraft endpoint.

Tests TB.1 — all scenarios per spec REQ-4.
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

BLOCK_ID = "block-1-strategic"


async def _create_admin_session(db: AsyncSession, email: str, sid: str) -> tuple[User, str]:
    from app.auth.password import hash_password
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
            "full_name": "Draft Tester",
            "email": email,
            "company_name": "DraftCo",
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


class TestBlockDraftPut:
    async def test_put_draft_creates_row_when_none_exists(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """PUT draft → 200 + stored payload when no prior draft exists."""
        user, sid = await _create_admin_session(test_db, "draft.tc1@t.com", "dft-sid-11111111")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.lead1@t.com")

        resp = await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["payload"]["q1_2_sponsor"] == "ceo_total"
        assert "updated_at" in data

    async def test_put_draft_upserts_existing_and_advances_updated_at(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """PUT draft twice → second call updates row, updated_at advances."""
        user, sid = await _create_admin_session(test_db, "draft.tc2@t.com", "dft-sid-22222222")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.lead2@t.com")

        r1 = await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        assert r1.status_code == 200
        ts1 = r1.json()["updated_at"]

        r2 = await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "director_cto"}},
            cookies={"admin_sid": sid},
        )
        assert r2.status_code == 200
        ts2 = r2.json()["updated_at"]
        assert r2.json()["payload"]["q1_2_sponsor"] == "director_cto"
        # updated_at must be >= ts1 (same second is ok in tests)
        assert ts2 >= ts1

    async def test_put_draft_requires_accepted_lead_404(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """PUT draft for unknown lead → 404."""
        user, sid = await _create_admin_session(test_db, "draft.tc5@t.com", "dft-sid-55555555")
        resp = await client.put(
            "/api/intake/nonexistent-lead-id/blocks/block-1-strategic/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404

    async def test_put_draft_requires_admin_auth_401(self, client: AsyncClient):
        """PUT draft without auth cookie → 401."""
        resp = await client.put(
            "/api/intake/some-lead-id/blocks/block-1-strategic/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
        )
        assert resp.status_code == 401


class TestBlockDraftGet:
    async def test_get_payload_returns_draft_when_no_submitted_answer(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """GET payload → source='draft' when only a draft exists."""
        user, sid = await _create_admin_session(test_db, "draft.tc3a@t.com", "dft-sid-33333331")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.lead3a@t.com")

        await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )

        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/payload",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["payload"]["q1_2_sponsor"] == "ceo_total"
        assert data["source"] == "draft"

    async def test_get_payload_returns_submitted_when_both_exist(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """GET payload → source='submitted' when submitted answer exists, even with draft."""
        user, sid = await _create_admin_session(test_db, "draft.tc3b@t.com", "dft-sid-33333332")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.lead3b@t.com")

        # Save a draft
        await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )

        # Also submit the block
        await client.post(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/submit",
            json={"payload": {"q1_2_sponsor": "director_cto"}},
            cookies={"admin_sid": sid},
        )

        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/payload",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "submitted"
        assert data["payload"]["q1_2_sponsor"] == "director_cto"


class TestBlockDraftPayloadValidation:
    async def test_put_draft_unknown_key_returns_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """PUT draft with a key not in the block schema → 422 with offending key listed."""
        user, sid = await _create_admin_session(test_db, "draft.val1@t.com", "dft-sid-val11111")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.leadval1@t.com")

        resp = await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"unknown_garbage_key": "some_value"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422, resp.text
        detail = resp.json().get("detail", "")
        assert "unknown_garbage_key" in str(detail)

    async def test_put_draft_unknown_block_id_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """PUT draft with a block_id that doesn't exist in schema → 404."""
        user, sid = await _create_admin_session(test_db, "draft.val2@t.com", "dft-sid-val22222")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.leadval2@t.com")

        resp = await client.put(
            f"/api/intake/{lead_id}/blocks/block-999-nonexistent/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 404, resp.text

    async def test_put_draft_other_text_suffix_accepted(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """PUT draft with a valid _other_text sibling key → 200 (not rejected)."""
        user, sid = await _create_admin_session(test_db, "draft.val3@t.com", "dft-sid-val33333")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.leadval3@t.com")

        # q1_3b_failure_cause has options — none are in the "other" set, so
        # we use q1_2_sponsor which also has options (none are "otro/other" either),
        # but the _other_text suffix rule allows it for ANY question.
        # Use a payload where we include a base key + its _other_text companion.
        resp = await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total", "q1_2_sponsor_other_text": "custom note"}},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text


class TestBlockDraftDeleteOnSubmit:
    async def test_post_submit_deletes_draft_for_that_block(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Submitting a block deletes its draft; subsequent GET returns source='submitted'."""
        user, sid = await _create_admin_session(test_db, "draft.tc4@t.com", "dft-sid-44444444")
        lead_id = await _create_accepted_lead(client, sid, user.id, "draft.lead4@t.com")

        # Save draft
        await client.put(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/draft",
            json={"payload": {"q1_2_sponsor": "ceo_total"}},
            cookies={"admin_sid": sid},
        )

        # Submit block
        await client.post(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/submit",
            json={"payload": {"q1_2_sponsor": "director_cto"}},
            cookies={"admin_sid": sid},
        )

        # Draft should be gone; payload returns submitted
        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/{BLOCK_ID}/payload",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "submitted"
        # Confirm the draft value is not returned
        assert data["payload"]["q1_2_sponsor"] == "director_cto"
