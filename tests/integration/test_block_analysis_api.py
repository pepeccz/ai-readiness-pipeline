"""
tests/integration/test_block_analysis_api.py — T6.7

Tests for:
  POST /api/intake/{lead_id}/analyze     → 202 + BackgroundTask encolado
  GET  /api/intake/{lead_id}/blocks/{block_id}/analysis → polling status
  404 if analysis not found
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password
from app.models.block_analysis import BlockAnalysis
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.session_row import SessionRow
from app.models.user import User


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


async def _create_accepted_lead(client: AsyncClient, db: AsyncSession, sid: str, user_id: str, email: str) -> str:
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


async def _create_block_analysis(db: AsyncSession, lead_id: str) -> tuple[str, str]:
    """Creates IntakeSession + BlockAnalysis and returns (session_id, ba_id)."""
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
        payload={"q1": "Automatizar procesos de ventas"},
        status="pending_analysis",
    )
    db.add(ba)
    await db.flush()
    await db.commit()

    return session.id, ba.id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    """T6.7 — POST /api/intake/{lead_id}/analyze returns 202."""

    async def test_analyze_returns_202(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin_ana1@test.com", "sid-ana1")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "lead_ana1@test.com")
        session_id, ba_id = await _create_block_analysis(test_db, lead_id)

        with patch("app.api.intake_routes.BlockAnalyzer") as mock_class:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock()
            mock_class.return_value = mock_instance

            resp = await client.post(
                f"/api/intake/{lead_id}/analyze",
                json={"block_id": "block-1-strategic"},
                cookies={"admin_sid": sid},
            )

        assert resp.status_code == 202

    async def test_analyze_response_contains_block_analysis_id(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin_ana2@test.com", "sid-ana2")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "lead_ana2@test.com")
        session_id, ba_id = await _create_block_analysis(test_db, lead_id)

        with patch("app.api.intake_routes.BlockAnalyzer") as mock_class:
            mock_instance = MagicMock()
            mock_instance.analyze = AsyncMock()
            mock_class.return_value = mock_instance

            resp = await client.post(
                f"/api/intake/{lead_id}/analyze",
                json={"block_id": "block-1-strategic"},
                cookies={"admin_sid": sid},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert "block_analysis_id" in body
        assert "status" in body


class TestAnalysisPollingEndpoint:
    """T6.7 — GET /api/intake/{lead_id}/blocks/{block_id}/analysis returns correct status."""

    async def test_polling_returns_analysis_when_ready(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin_poll1@test.com", "sid-poll1")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "lead_poll1@test.com")
        session_id, ba_id = await _create_block_analysis(test_db, lead_id)

        # Mark analysis as ready
        stmt = select(BlockAnalysis).where(BlockAnalysis.id == ba_id)
        result = await test_db.execute(stmt)
        ba = result.scalar_one()
        ba.status = "ready"
        ba.llm_output = {"synthesis": "Test synthesis", "contradictions": [], "follow_ups": []}
        await test_db.commit()

        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/analysis",
            cookies={"admin_sid": sid},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert body["llm_output"] is not None

    async def test_polling_returns_404_if_no_analysis(self, client: AsyncClient, test_db: AsyncSession):
        user, sid = await _create_admin_session(test_db, "admin_poll2@test.com", "sid-poll2")
        lead_id = await _create_accepted_lead(client, test_db, sid, str(user.id), "lead_poll2@test.com")

        resp = await client.get(
            f"/api/intake/{lead_id}/blocks/block-99-nonexistent/analysis",
            cookies={"admin_sid": sid},
        )

        assert resp.status_code == 404
