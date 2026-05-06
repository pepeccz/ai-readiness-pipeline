"""
tests/integration/test_skip_analysis.py — A-4 (REQ-2)

Integration tests for skip_analysis=true path in submit_block handler.

Acceptance criteria:
  - skip_analysis=true → no Anthropic/LLM call, BlockAnalysis.status='skipped',
    blocks_completed incremented, 202 response, no error field
  - skip_analysis=false (default) → existing flow (background task scheduled)
  - blocks_completed always increments regardless of skip flag
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.block_analysis import BlockAnalysis
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


async def _create_admin_session(db: AsyncSession, email: str, sid: str):
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
            "full_name": "Skip Tester",
            "email": email,
            "company_name": "SkipCo",
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


class TestSkipAnalysisTrue:
    """A-4: skip_analysis=true path."""

    async def test_skip_analysis_returns_202(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "skip.a1@t.com", "skip-sid-a0000001")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.lead1@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}, "skip_analysis": True},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, resp.text

    async def test_skip_analysis_creates_skipped_block_analysis(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "skip.a2@t.com", "skip-sid-a0000002")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.lead2@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}, "skip_analysis": True},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, resp.text
        ba_id = resp.json()["block_analysis_id"]

        # Verify in DB
        stmt = select(BlockAnalysis).where(BlockAnalysis.id == ba_id)
        result = await test_db.execute(stmt)
        ba = result.scalar_one_or_none()
        assert ba is not None
        assert ba.status == "skipped"
        assert ba.llm_output is None

    async def test_skip_analysis_increments_blocks_completed(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "skip.a3@t.com", "skip-sid-a0000003")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.lead3@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}, "skip_analysis": True},
            cookies={"admin_sid": sid},
        )

        state_resp = await client.get(
            f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid}
        )
        assert state_resp.status_code == 200
        assert "block-1-strategic" in state_resp.json()["blocks_completed"]

    async def test_skip_analysis_does_not_call_llm(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """A-4: skip_analysis=true must NOT schedule or call the LLM analyzer."""
        user, sid = await _create_admin_session(test_db, "skip.a4@t.com", "skip-sid-a0000004")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.lead4@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        with patch("app.api.intake_routes.BlockAnalyzer") as mock_analyzer_cls:
            mock_analyzer_cls.return_value.analyze = AsyncMock()
            resp = await client.post(
                f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
                json={"payload": {"q1_2_sponsor": "ceo_total"}, "skip_analysis": True},
                cookies={"admin_sid": sid},
            )
            assert resp.status_code == 202
            # BlockAnalyzer.analyze must NOT have been called
            mock_analyzer_cls.return_value.analyze.assert_not_called()

    async def test_skip_analysis_response_has_no_error_field(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "skip.a5@t.com", "skip-sid-a0000005")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.lead5@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}, "skip_analysis": True},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202
        assert "error" not in resp.json()


class TestSkipAnalysisFalse:
    """A-4: skip_analysis=false (default) → existing flow unchanged."""

    async def test_skip_analysis_false_is_default(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Submitting without skip_analysis field behaves like skip_analysis=false."""
        user, sid = await _create_admin_session(test_db, "skip.b1@t.com", "skip-sid-b0000001")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.leadb1@t.com")
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
        data = resp.json()
        assert data["status"] == "pending_analysis"

    async def test_skip_analysis_false_creates_pending_analysis_row(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(test_db, "skip.b2@t.com", "skip-sid-b0000002")
        lead_id = await _create_accepted_lead(client, sid, user.id, "skip.leadb2@t.com")
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "marketing"},
            cookies={"admin_sid": sid},
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_2_sponsor": "ceo_total"}, "skip_analysis": False},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202
        ba_id = resp.json()["block_analysis_id"]

        stmt = select(BlockAnalysis).where(BlockAnalysis.id == ba_id)
        result = await test_db.execute(stmt)
        ba = result.scalar_one_or_none()
        assert ba is not None
        assert ba.status == "pending_analysis"
