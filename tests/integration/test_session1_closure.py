"""
tests/integration/test_session1_closure.py — TA.8, TA.10, TB.1, TB.2

Integration tests for:
  - TA.8:  zero-branch short-circuit → state=deep_received
  - TA.10: GET /intake/{lead_id}/state includes session1_synthesis + session1_synthesis_status
  - TB.1:  POST /intake/{lead_id}/close normal path (deep_received → closed)
  - TB.2:  POST /intake/{lead_id}/close force path + rejection cases
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake_session import IntakeSession
from app.models.lead import Lead

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
    from app.models.session_row import SessionRow
    from app.models.user import User

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


async def _accepted_lead_id(client: AsyncClient, sid: str, user_id: str, email: str) -> str:
    payload = {
        "answers": {
            "full_name": "Close Tester",
            "email": email,
            "company_name": "CloseCo",
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


async def _submit_block1(client: AsyncClient, lead_id: str, sid: str) -> None:
    """Submit area selection and block-1-strategic so the session is closeable."""
    resp = await client.post(
        f"/api/intake/{lead_id}/area-selection",
        json={"primary_area": "operations"},
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200, resp.text

    resp2 = await client.post(
        f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
        json={"payload": {"q1_1_previous_ai": "no_intentos"}},
        cookies={"admin_sid": sid},
    )
    assert resp2.status_code == 202, resp2.text


# ---------------------------------------------------------------------------
# TA.8 — zero-branch short-circuit
# ---------------------------------------------------------------------------


class TestZeroBranchShortCircuit:
    async def test_zero_branches_transitions_to_session2_pending(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        PR5a: session1/close always transitions to session2_pending regardless of branch count.
        deep_received is a retired state — no longer reachable.
        """
        from app.services.deep import trigger_detector as td_module
        import app.db.session as db_session_module
        from contextlib import asynccontextmanager

        monkeypatch.setattr(
            td_module.TriggerDetector, "detect_from_all_blocks", staticmethod(lambda payloads: set())
        )

        # Prevent BG task from using real DB — patch async_session_factory to return test_db
        @asynccontextmanager
        async def _fake_session_factory():
            yield test_db

        monkeypatch.setattr(db_session_module, "async_session_factory", _fake_session_factory)

        user, sid = await _create_admin_session(test_db, "zb.t1@t.com", "zb-sid-00000001")
        lead_id = await _accepted_lead_id(client, sid, user.id, "zb.lead1@t.com")
        await _submit_block1(client, lead_id, sid)

        resp = await client.post(
            f"/api/intake/{lead_id}/session1/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()
        # PR5a: state is always session2_pending (deep_received is retired)
        assert data["state"] == "session2_pending", (
            f"Expected session2_pending (PR5a), got {data['state']!r}. "
            "deep_received is a retired state."
        )
        assert data["deep_branches_created"] == 0

    async def test_nonzero_branches_still_transitions_to_session2_pending(
        self, client: AsyncClient, test_db: AsyncSession, monkeypatch
    ):
        """
        PR5a: session1/close transitions to session2_pending even when branches were detected.
        deep_pending is a retired state — no longer reachable from session1/close.
        """
        from app.services.deep import trigger_detector as td_module
        import app.db.session as db_session_module
        from contextlib import asynccontextmanager

        monkeypatch.setattr(
            td_module.TriggerDetector,
            "detect_from_all_blocks",
            staticmethod(lambda payloads: {"governance_previo_ia"}),
        )

        @asynccontextmanager
        async def _fake_session_factory():
            yield test_db

        monkeypatch.setattr(db_session_module, "async_session_factory", _fake_session_factory)

        user, sid = await _create_admin_session(test_db, "zb.t2@t.com", "zb-sid-00000002")
        lead_id = await _accepted_lead_id(client, sid, user.id, "zb.lead2@t.com")
        await _submit_block1(client, lead_id, sid)

        resp = await client.post(
            f"/api/intake/{lead_id}/session1/close",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()
        # PR5a: state is session2_pending regardless of branch count
        assert data["state"] == "session2_pending", (
            f"Expected session2_pending (PR5a), got {data['state']!r}. "
            "deep_pending is a retired state."
        )


# ---------------------------------------------------------------------------
# TA.10 — GET /state synthesis extension
# ---------------------------------------------------------------------------


class TestGetStateSynthesisExtension:
    async def test_state_includes_synthesis_fields(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """GET /state response includes session1_synthesis and session1_synthesis_status."""
        user, sid = await _create_admin_session(test_db, "st.t1@t.com", "st-sid-00000001")
        lead_id = await _accepted_lead_id(client, sid, user.id, "st.lead1@t.com")

        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert "session1_synthesis" in data, "session1_synthesis missing from state response"
        assert "session1_synthesis_status" in data, "session1_synthesis_status missing from state response"

    async def test_state_synthesis_status_not_started_initially(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """When state is in_progress, synthesis_status is not_started."""
        user, sid = await _create_admin_session(test_db, "st.t2@t.com", "st-sid-00000002")
        lead_id = await _accepted_lead_id(client, sid, user.id, "st.lead2@t.com")

        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["session1_synthesis_status"] == "not_started"
        assert data["session1_synthesis"] is None

    async def test_state_synthesis_status_ready_when_populated(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """When session has synthesis data, status is ready."""
        user, sid = await _create_admin_session(test_db, "st.t3@t.com", "st-sid-00000003")
        lead_id = await _accepted_lead_id(client, sid, user.id, "st.lead3@t.com")

        # Manually set synthesis on the session
        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "deep_pending"
        session.session1_synthesis = {
            "summary": "Test synthesis",
            "key_insights": ["insight"],
            "recommendations": ["rec"],
            "hypothesis": "hyp",
            "generated_at": "2026-05-06T00:00:00Z",
            "model": "claude-sonnet-4-6",
        }
        await test_db.commit()

        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["session1_synthesis_status"] == "ready"
        assert data["session1_synthesis"] is not None
        assert data["session1_synthesis"]["summary"] == "Test synthesis"

    async def test_state_synthesis_status_failed_when_error_key(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """When synthesis has error key, status is failed."""
        user, sid = await _create_admin_session(test_db, "st.t4@t.com", "st-sid-00000004")
        lead_id = await _accepted_lead_id(client, sid, user.id, "st.lead4@t.com")

        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "deep_pending"
        session.session1_synthesis = {
            "error": "LLM timed out",
            "generated_at": "2026-05-06T00:00:00Z",
            "model": "claude-sonnet-4-6",
        }
        await test_db.commit()

        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["session1_synthesis_status"] == "failed"

    async def test_state_includes_deep_branches_count(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """GET /state includes deep_branches_count field."""
        user, sid = await _create_admin_session(test_db, "st.t5@t.com", "st-sid-00000005")
        lead_id = await _accepted_lead_id(client, sid, user.id, "st.lead5@t.com")

        resp = await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert "deep_branches_count" in data


# ---------------------------------------------------------------------------
# TB.1 — POST /intake/{lead_id}/close — normal path
# ---------------------------------------------------------------------------


class TestFinalCloseNormalPath:
    async def test_close_deep_received_returns_422_with_redirect(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """
        PR5a: state=deep_received is a legacy/retired state.
        POST /close on deep_received → 422 with next_endpoint='session2/close'.
        """
        user, sid = await _create_admin_session(test_db, "fc.t1@t.com", "fc-sid-00000001")
        lead_id = await _accepted_lead_id(client, sid, user.id, "fc.lead1@t.com")

        # Set session to legacy deep_received (defensive: should not exist after migration)
        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "deep_received"
        await test_db.commit()

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={},
            cookies={"admin_sid": sid},
        )
        # PR5a: deep_received is a retired legacy state → 422 redirect
        assert resp.status_code == 422, (
            f"Expected 422 for legacy deep_received state (PR5a), got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "session2/close" in str(body.get("detail", "")), (
            f"Expected next_endpoint reference in response, got: {body!r}"
        )

    async def test_close_without_auth_returns_401_or_403(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """No admin credentials → 401 or 403."""
        user, sid = await _create_admin_session(test_db, "fc.t2@t.com", "fc-sid-00000002")
        lead_id = await _accepted_lead_id(client, sid, user.id, "fc.lead2@t.com")

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={},
            # no cookies
        )
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    async def test_close_already_closed_is_idempotent(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Already closed → 200 with state=closed (idempotent)."""
        user, sid = await _create_admin_session(test_db, "fc.t3@t.com", "fc-sid-00000003")
        lead_id = await _accepted_lead_id(client, sid, user.id, "fc.lead3@t.com")

        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "closed"
        await test_db.commit()

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["state"] == "closed"


# ---------------------------------------------------------------------------
# TB.2 — POST /intake/{lead_id}/close — force path + rejection
# ---------------------------------------------------------------------------


class TestFinalCloseForceAndRejection:
    async def test_deep_pending_with_force_true_now_returns_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """
        PR5a: state=deep_pending is a retired legacy state.
        POST /close with force=true on deep_pending → 422 with next_endpoint='session2/close'.
        The force-close path is no longer supported; use session2/close instead.
        """
        user, sid = await _create_admin_session(test_db, "ff.t1@t.com", "ff-sid-00000001")
        lead_id = await _accepted_lead_id(client, sid, user.id, "ff.lead1@t.com")

        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "deep_pending"
        await test_db.commit()

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={"force": True},
            cookies={"admin_sid": sid},
        )
        # PR5a: deep_pending is a retired state → 422 redirect to session2/close
        assert resp.status_code == 422, (
            f"Expected 422 for legacy deep_pending state (PR5a), got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert "session2/close" in str(body.get("detail", "")), (
            f"Expected next_endpoint reference in response, got: {body!r}"
        )

    async def test_force_false_with_non_deep_received_returns_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """state=deep_pending, force=false → 422 with detail."""
        user, sid = await _create_admin_session(test_db, "ff.t2@t.com", "ff-sid-00000002")
        lead_id = await _accepted_lead_id(client, sid, user.id, "ff.lead2@t.com")

        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "deep_pending"
        await test_db.commit()

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={"force": False},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "detail" in data or "error" in data

    async def test_no_force_with_in_progress_returns_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """state=in_progress, no force → 422."""
        user, sid = await _create_admin_session(test_db, "ff.t3@t.com", "ff-sid-00000003")
        lead_id = await _accepted_lead_id(client, sid, user.id, "ff.lead3@t.com")

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422, resp.text

    async def test_force_with_branches_present_still_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """state=deep_pending + branches exist + force=true — design says 422 because branches != 0."""
        from app.models.deep_branch import DeepBranch

        user, sid = await _create_admin_session(test_db, "ff.t4@t.com", "ff-sid-00000004")
        lead_id = await _accepted_lead_id(client, sid, user.id, "ff.lead4@t.com")

        stmt = select(IntakeSession).where(IntakeSession.lead_id == lead_id)
        result = await test_db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            from app.api._intake_helpers import get_or_create_session as goc
            session = await goc(test_db, lead_id)

        session.state = "deep_pending"
        await test_db.flush()

        branch = DeepBranch(
            intake_session_id=session.id,
            branch_id="governance_previo_ia",
            generated_questions=[],
            status="pending_generation",
        )
        test_db.add(branch)
        await test_db.commit()

        resp = await client.post(
            f"/api/intake/{lead_id}/close",
            json={"force": True},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422, resp.text
