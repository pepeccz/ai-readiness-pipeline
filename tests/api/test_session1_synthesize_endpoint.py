"""
tests/api/test_session1_synthesize_endpoint — C-1 (TDD RED → GREEN)

Tests for POST /api/intake/{lead_id}/session1/synthesize (REQ-3).

Scenarios:
  - Happy path → 202
  - Session not closed (state < deep_pending) → 409
  - Already in-flight synthesis (synthesis=None AND error flag in synthesis) — guard
  - No DEEP branch mutation after retry
  - Admin auth required → 401/403
  - Clears failure flag on retry
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deep_branch import DeepBranch
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


async def _create_accepted_lead_with_closed_session(
    client: AsyncClient,
    db: AsyncSession,
    sid: str,
    user_id: str,
    email: str,
    state: str = "deep_pending",
) -> tuple[str, str]:
    """Create lead, accept it, then directly set session state to given value."""
    payload = {
        "answers": {
            "full_name": "Retry Test",
            "email": email,
            "company_name": "Retry Corp",
            "phone": None,
            **_VALID_TRIAGE,
        },
        "consents": [
            {"type": "privacy", "accepted": True, "policy_version": "v1.0-2026-05"}
        ],
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

    result = await db.execute(
        select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    )
    session = result.scalar_one()

    # Directly set session state to simulate post-close state
    session.state = state
    if state in ("deep_pending", "deep_received"):
        # Mark synthesis as failed so retry is valid
        session.session1_synthesis = {
            "error": "previous attempt failed",
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "model": "claude-sonnet-4-6",
        }
    await db.commit()

    return lead_id, session.id


# ---------------------------------------------------------------------------
# C-1 tests
# ---------------------------------------------------------------------------


class TestSession1SynthesizeEndpoint:

    async def test_happy_path_returns_202(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Lead with deep_pending state → 202 with synthesis_started."""
        user, sid = await _create_admin_session(
            test_db, "syn.happy@t.com", "syn-sid-happy01"
        )
        lead_id, session_id = await _create_accepted_lead_with_closed_session(
            client, test_db, sid, user.id, "syn.happy.lead@t.com", state="deep_pending"
        )

        # Mock the background task to avoid actual LLM call
        with patch(
            "app.api.intake_routes.run_session1_synthesis",
            new_callable=lambda: lambda *a, **kw: AsyncMock(),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/synthesize",
                cookies={"admin_sid": sid},
            )

        assert resp.status_code == 202, resp.text
        assert resp.json().get("message") == "synthesis_started"

    async def test_refused_if_session_not_closed(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Session with state=in_progress (not closed) → 409."""
        user, sid = await _create_admin_session(
            test_db, "syn.notclosed@t.com", "syn-sid-notclosed1"
        )
        lead_id, _ = await _create_accepted_lead_with_closed_session(
            client, test_db, sid, user.id, "syn.notclosed.lead@t.com", state="in_progress"
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/session1/synthesize",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code in (409, 422), resp.text

    async def test_requires_admin_auth(self, client: AsyncClient, test_db: AsyncSession):
        """No auth cookie → 401 or 403."""
        user, sid = await _create_admin_session(
            test_db, "syn.noauth@t.com", "syn-sid-noauth001"
        )
        lead_id, _ = await _create_accepted_lead_with_closed_session(
            client, test_db, sid, user.id, "syn.noauth.lead@t.com", state="deep_pending"
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/session1/synthesize"
            # no cookies
        )
        assert resp.status_code in (401, 403), resp.text

    async def test_no_deep_branch_mutation(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """DEEP branch count must be unchanged after retry."""
        user, sid = await _create_admin_session(
            test_db, "syn.nobranch@t.com", "syn-sid-nobranch1"
        )
        lead_id, session_id = await _create_accepted_lead_with_closed_session(
            client, test_db, sid, user.id, "syn.nobranch.lead@t.com", state="deep_pending"
        )

        # Add a DEEP branch manually
        branch = DeepBranch(
            intake_session_id=session_id,
            branch_id="governance",
            generated_questions=[],
            status="pending_review",
        )
        test_db.add(branch)
        await test_db.commit()

        # Count branches before
        branches_before = await test_db.execute(
            select(DeepBranch).where(DeepBranch.intake_session_id == session_id)
        )
        count_before = len(branches_before.scalars().all())

        with patch(
            "app.api.intake_routes.run_session1_synthesis",
            new_callable=lambda: lambda *a, **kw: AsyncMock(),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/synthesize",
                cookies={"admin_sid": sid},
            )
        assert resp.status_code == 202, resp.text

        # Count branches after
        branches_after = await test_db.execute(
            select(DeepBranch).where(DeepBranch.intake_session_id == session_id)
        )
        count_after = len(branches_after.scalars().all())
        assert count_before == count_after, "DEEP branch count must not change on retry"

    async def test_clears_synthesis_on_retry(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """After calling retry endpoint, session1_synthesis should be reset to None."""
        user, sid = await _create_admin_session(
            test_db, "syn.clear@t.com", "syn-sid-clear001"
        )
        lead_id, session_id = await _create_accepted_lead_with_closed_session(
            client, test_db, sid, user.id, "syn.clear.lead@t.com", state="deep_pending"
        )

        with patch(
            "app.api.intake_routes.run_session1_synthesis",
            new_callable=lambda: lambda *a, **kw: AsyncMock(),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/synthesize",
                cookies={"admin_sid": sid},
            )
        assert resp.status_code == 202, resp.text

        # Reload session from DB
        test_db.expire_all()
        result = await test_db.execute(
            select(IntakeSession).where(IntakeSession.id == session_id)
        )
        session = result.scalar_one()
        # session1_synthesis should be None (reset) — background task not actually run
        assert session.session1_synthesis is None


# ---------------------------------------------------------------------------
# C.6 — REQ-13: session1/close MUST NOT generate a PDF
# ---------------------------------------------------------------------------


class TestSession1CloseNoPDFGeneration:
    """
    Regression-prevention tests: POST /intake/{lead_id}/session1/close
    must NEVER generate a PDF.

    REQ-13: PDF generation is deferred to session2/close.
    This test documents the contract and prevents accidental regression.
    """

    async def test_session1_close_does_not_set_report_content(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        After POST /intake/{lead_id}/session1/close completes,
        IntakeSession.report_content must remain None.

        PR5b: TriggerDetector removed from close_session1. No patch needed.
        """
        import app.db.session as db_session_module
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_session_factory():
            yield test_db

        monkeypatch.setattr(db_session_module, "async_session_factory", _fake_session_factory)

        user, sid = await _create_admin_session(test_db, "nopdf1@t.com", "nopdf-sid-0000001")

        # Create lead + accepted session
        payload = {
            "answers": {
                "full_name": "No PDF Test",
                "email": "nopdf.lead1@t.com",
                "company_name": "NoPDF Corp",
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
            json={"action": "accept", "consultant_id": str(user.id)},
            cookies={"admin_sid": sid},
        )
        assert r2.status_code == 200, r2.text

        # Submit block-1-strategic (needed for session to be closeable)
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "operations"},
            cookies={"admin_sid": sid},
        )
        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_1_previous_ai": "no_intentos"}},
            cookies={"admin_sid": sid},
        )

        # Call session1/close
        resp = await client.post(
            f"/api/intake/{lead_id}/session1/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"

        # Check that no PDF was generated
        test_db.expire_all()
        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        assert session is not None

        assert session.report_content is None, (
            "REQ-13 violation: session1/close must NOT generate a PDF. "
            f"report_content is not None: {type(session.report_content)}"
        )


# ---------------------------------------------------------------------------
# E.7 — REQ-09: session1/close MUST set state to session2_pending (PR5a)
# ---------------------------------------------------------------------------


class TestSession1CloseTransitionsToSession2Pending:
    """
    E.7 TDD RED: POST /intake/{lead_id}/session1/close must transition state to
    session2_pending, NOT deep_pending or deep_received.

    REQ-09: The states deep_pending and deep_received must NOT be reachable from
    session1/close after the PR5a migration.
    """

    async def test_session1_close_sets_state_to_session2_pending(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        After POST /intake/{lead_id}/session1/close, state must be session2_pending.

        PR5b: TriggerDetector removed from close_session1. No patch needed.
        """
        import app.db.session as db_session_module
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_session_factory():
            yield test_db

        monkeypatch.setattr(db_session_module, "async_session_factory", _fake_session_factory)

        user, sid = await _create_admin_session(
            test_db, "s2p.close1@t.com", "s2p-sid-0000001"
        )

        # Create lead + accept
        payload = {
            "answers": {
                "full_name": "S2P Close Test",
                "email": "s2p.close.lead1@t.com",
                "company_name": "S2P Corp",
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
            json={"action": "accept", "consultant_id": str(user.id)},
            cookies={"admin_sid": sid},
        )
        assert r2.status_code == 200, r2.text

        # Submit block-1-strategic (precondition for close)
        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "operations"},
            cookies={"admin_sid": sid},
        )
        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_1_previous_ai": "no_intentos"}},
            cookies={"admin_sid": sid},
        )

        # Call session1/close
        resp = await client.post(
            f"/api/intake/{lead_id}/session1/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"

        # Verify state is session2_pending (NOT deep_pending or deep_received)
        test_db.expire_all()
        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        assert session is not None

        assert session.state == "session2_pending", (
            f"REQ-09 violation: session1/close must set state to 'session2_pending', "
            f"got {session.state!r}. deep_pending/deep_received are retired states."
        )

    async def test_session1_close_never_sets_deep_states(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        E.7 triangulation: After session1/close, state must NOT be deep_pending
        or deep_received under any condition.

        PR5b: TriggerDetector removed entirely. This test verifies the state
        machine constraint is preserved — session always goes to session2_pending.
        """
        import app.db.session as db_session_module
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_session_factory():
            yield test_db

        monkeypatch.setattr(db_session_module, "async_session_factory", _fake_session_factory)

        user, sid = await _create_admin_session(
            test_db, "s2p.nobranch@t.com", "s2p-sid-0000002"
        )

        payload = {
            "answers": {
                "full_name": "S2P NoBranch Test",
                "email": "s2p.nobranch.lead@t.com",
                "company_name": "NoBranch Corp",
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
            json={"action": "accept", "consultant_id": str(user.id)},
            cookies={"admin_sid": sid},
        )
        assert r2.status_code == 200, r2.text

        await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "operations"},
            cookies={"admin_sid": sid},
        )
        await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"q1_1_previous_ai": "no_intentos"}},
            cookies={"admin_sid": sid},
        )

        resp = await client.post(
            f"/api/intake/{lead_id}/session1/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"

        test_db.expire_all()
        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        assert session is not None

        assert session.state not in ("deep_pending", "deep_received"), (
            f"REQ-09 violation: state must never be deep_pending/deep_received after PR5a. "
            f"Got {session.state!r}."
        )
        assert session.state == "session2_pending", (
            f"Expected 'session2_pending', got {session.state!r}."
        )
