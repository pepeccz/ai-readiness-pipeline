"""
tests/integration/test_client_report_viewer — T8.2

Integration tests for the public client report viewer endpoints (Batch 8).

Endpoints under test:
  GET /api/client/report/{signed_token}          — check report status
  GET /api/client/report/{signed_token}/download — download report PDF

Token type: signed URL with payload {lead_id, purpose="report_view"}
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.session_row import SessionRow
from app.models.user import User

pytestmark = pytest.mark.asyncio


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
    client: AsyncClient,
    db: AsyncSession,
    sid: str,
    user_id: str,
    lead_email: str,
) -> tuple[str, str]:
    """Return (lead_id, session_id)."""
    from sqlalchemy import select

    payload = {
        "answers": {
            "full_name": "Report Viewer",
            "email": lead_email,
            "company_name": "RV Corp",
            "phone": None,
            **_VALID_TRIAGE,
        },
        "consents": [
            {"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}
        ],
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

    result = await db.execute(
        select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    )
    session = result.scalar_one()
    return lead_id, session.id


def _make_report_token(lead_id: str, ttl_seconds: int = 86400 * 90) -> str:
    from app.signed_urls import sign_payload

    return sign_payload(
        {"lead_id": lead_id, "purpose": "report_view"},
        ttl_seconds=ttl_seconds,
    )


def _make_expired_report_token(lead_id: str) -> str:
    from app.signed_urls import sign_payload

    return sign_payload(
        {"lead_id": lead_id, "purpose": "report_view"},
        ttl_seconds=-1,
    )


# ---------------------------------------------------------------------------
# GET /api/client/report/{token} — status check
# ---------------------------------------------------------------------------


class TestClientReportStatus:
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/client/report/not-a-real-token")
        assert resp.status_code == 401

    async def test_expired_token_returns_401(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "rpt.exp@t.com", "rpt-sid-expired01"
        )
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "rpt.exp.lead@t.com"
        )
        token = _make_expired_report_token(lead_id)
        resp = await client.get(f"/api/client/report/{token}")
        assert resp.status_code == 401

    async def test_report_not_ready_returns_202(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "rpt.pending@t.com", "rpt-sid-pend0001"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "rpt.pending.lead@t.com"
        )
        token = _make_report_token(lead_id)

        resp = await client.get(f"/api/client/report/{token}")
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "pending"

    async def test_report_ready_returns_200(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        from sqlalchemy import select, update

        user, sid = await _create_admin_session(
            test_db, "rpt.ready@t.com", "rpt-sid-ready001"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "rpt.ready.lead@t.com"
        )
        # Mark session as deep_received so report would be "ready"
        await test_db.execute(
            update(IntakeSession)
            .where(IntakeSession.id == session_id)
            .values(state="deep_received")
        )
        # Also store report content in session
        await test_db.execute(
            update(IntakeSession)
            .where(IntakeSession.id == session_id)
            .values(report_content="PDF content placeholder")
        )
        await test_db.commit()

        token = _make_report_token(lead_id)
        resp = await client.get(f"/api/client/report/{token}")
        # 200 when report is ready
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"


# ---------------------------------------------------------------------------
# GET /api/client/report/{token}/download
# ---------------------------------------------------------------------------


class TestClientReportDownload:
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/client/report/bad-token/download")
        assert resp.status_code == 401

    async def test_report_not_ready_returns_202(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        user, sid = await _create_admin_session(
            test_db, "rptdl.pend@t.com", "rptdl-sid-pend001"
        )
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "rptdl.pend.lead@t.com"
        )
        token = _make_report_token(lead_id)

        resp = await client.get(f"/api/client/report/{token}/download")
        assert resp.status_code == 202
        assert resp.json()["status"] == "pending"
