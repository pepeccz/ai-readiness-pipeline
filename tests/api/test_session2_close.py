"""
tests/api/test_session2_close.py — E.9 (TDD RED)

Tests for the legacy POST /intake/{lead_id}/close endpoint after PR5a changes.

Scenarios (REQ-24):
  1. POST /close on closed session → 200 idempotent (no state change)
  2. POST /close on session2_pending → 422 with "session2/close" reference in body
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake_session import IntakeSession
from app.models.lead import Lead
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


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


async def _create_admin_session(db: AsyncSession, email: str, sid: str) -> tuple[User, str]:
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
    email: str,
) -> str:
    """Create a lead via triage, accept it, and return the lead_id."""
    payload = {
        "answers": {
            "full_name": "Close Test",
            "email": email,
            "company_name": "Close Corp",
            "phone": None,
            **_VALID_TRIAGE,
        },
        "consents": [{"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}],
    }
    r = await client.post("/api/public/triage/submit", json=payload)
    assert r.status_code == 201, r.text
    lead_id = r.json()["lead_id"]

    r2 = await client.patch(
        f"/api/admin/leads/{lead_id}",
        json={"action": "accept", "consultant_id": str(user_id)},
        cookies={"admin_sid": sid},
    )
    assert r2.status_code == 200, r2.text
    return lead_id


async def _set_session_state(db: AsyncSession, lead_id: str, state: str) -> None:
    """Directly set session state in the DB (test helper)."""
    result = await db.execute(
        select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    )
    session = result.scalar_one()
    session.state = state
    await db.commit()


# ---------------------------------------------------------------------------
# E.9 Tests — RED (legacy /close endpoint needs PR5a guard)
# ---------------------------------------------------------------------------


class TestLegacyCloseIdempotentOnClosed:
    """
    REQ-24 Scenario 1: POST /intake/{lead_id}/close on a closed session returns 200.
    """

    async def test_legacy_close_on_closed_session_returns_200(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """
        POST /intake/{lead_id}/close on a session already in 'closed' state
        must return 200 (idempotent) without changing any state.
        """
        user, sid = await _create_admin_session(
            test_db, "cls.idem@t.com", "cls-sid-idem001"
        )
        lead_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "cls.idem.lead@t.com"
        )
        await _set_session_state(test_db, lead_id, "closed")

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, (
            f"Expected 200 idempotent on closed session, got {resp.status_code}: {resp.text}"
        )

        # State must still be closed
        test_db.expire_all()
        result = await test_db.execute(
            select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        )
        session = result.scalar_one()
        assert session.state == "closed", (
            f"State should remain 'closed', got {session.state!r}."
        )


class TestLegacyCloseRejectsSession2Pending:
    """
    REQ-24 Scenario 2: POST /intake/{lead_id}/close on session2_pending returns 422.
    The response body must reference 'session2/close'.
    """

    async def test_legacy_close_on_session2_pending_returns_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """
        POST /intake/{lead_id}/close on session in 'session2_pending' state
        must return 422 with a body that references 'session2/close'.
        """
        user, sid = await _create_admin_session(
            test_db, "cls.s2p@t.com", "cls-sid-s2p0001"
        )
        lead_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "cls.s2p.lead@t.com"
        )
        await _set_session_state(test_db, lead_id, "session2_pending")

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for session2_pending state, got {resp.status_code}: {resp.text}"
        )

        body = resp.json()
        detail = body.get("detail", "")
        detail_str = str(detail)
        assert "session2/close" in detail_str, (
            f"Expected response body to reference 'session2/close', got: {detail_str!r}"
        )

    async def test_legacy_close_on_session2_pending_body_has_next_endpoint(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """
        E.9 triangulation: The 422 response for session2_pending MUST include
        a 'next_endpoint' key directing caller to 'session2/close'.
        """
        user, sid = await _create_admin_session(
            test_db, "cls.s2p2@t.com", "cls-sid-s2p0002"
        )
        lead_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "cls.s2p2.lead@t.com"
        )
        await _set_session_state(test_db, lead_id, "session2_pending")

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422

        body = resp.json()
        detail = body.get("detail", {})
        if isinstance(detail, dict):
            assert "next_endpoint" in detail, (
                f"Expected 'next_endpoint' in detail dict, got: {detail!r}"
            )
            assert "session2/close" in detail.get("next_endpoint", ""), (
                f"next_endpoint should reference 'session2/close', got: {detail.get('next_endpoint')!r}"
            )
        else:
            # If detail is a string, it must contain 'session2/close'
            assert "session2/close" in str(detail), (
                f"Expected 'session2/close' in detail, got: {detail!r}"
            )


# ---------------------------------------------------------------------------
# F.5 RED/GREEN — Regression: intake_routes must not import app.services.deep
# ---------------------------------------------------------------------------


class TestIntakeRoutesHasNoDeepImports:
    """
    PR5b regression-prevention: after F.3 deletes app/services/deep/,
    intake_routes.py must not reference it. This test would have been RED
    before F.3 (TriggerDetector was imported at line 1562).

    Method: read the source file and assert no deep-service import strings.
    This catches future accidental re-introduction without requiring a running
    server (static analysis via file content check).
    """

    def test_intake_routes_has_no_deep_service_import(self):
        """
        F.5 GREEN (would have been RED before F.3).

        REQ-14: no new rows on deep_branches, and the deep service module must
        be entirely removed from the import surface of intake_routes.py.
        """
        import importlib.util
        import pathlib

        src_path = pathlib.Path(__file__).parent.parent.parent / "app" / "api" / "intake_routes.py"
        content = src_path.read_text(encoding="utf-8")

        assert "app.services.deep" not in content, (
            "intake_routes.py still references 'app.services.deep'. "
            "This import must be removed in PR5b (F.3)."
        )
        assert "from app.services.deep" not in content, (
            "intake_routes.py contains a 'from app.services.deep' import. "
            "All deep service imports must be removed in PR5b."
        )

    def test_client_routes_has_no_deep_service_import(self):
        """
        F.5 companion: client_routes.py must also be free of deep service imports.
        """
        import pathlib

        src_path = pathlib.Path(__file__).parent.parent.parent / "app" / "api" / "client_routes.py"
        content = src_path.read_text(encoding="utf-8")

        assert "app.services.deep" not in content, (
            "client_routes.py still references 'app.services.deep'."
        )

    def test_deep_service_module_does_not_exist(self):
        """
        F.5 hard guard: app/services/deep/ directory must not exist after PR5b.

        If someone accidentally recreates it, this test fails immediately.
        """
        import pathlib

        deep_dir = pathlib.Path(__file__).parent.parent.parent / "app" / "services" / "deep"
        assert not deep_dir.exists(), (
            f"app/services/deep/ directory exists at {deep_dir}. "
            "It must be deleted in PR5b (F.3). Do not re-create it."
        )
