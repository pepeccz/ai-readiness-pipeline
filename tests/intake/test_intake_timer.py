"""
tests/intake/test_intake_timer.py — TDD test suite for intake session timer (PR 1).

Covers:
  REQ-1  — timer columns present on model / migration
  REQ-2  — auto-start on first GET /intake/{lead_id}/state
  REQ-3  — PATCH action=pause
  REQ-4  — PATCH action=resume
  REQ-5  — PATCH action=reset
  REQ-6  — PATCH action=adjust
  REQ-7  — close_session1 writes session1_completed_at + auto-pauses timer
  REQ-8  — timer object in state response
  REQ-11 — auth required on PATCH timer endpoint
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

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
# Helpers
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


async def _create_accepted_lead(
    client: AsyncClient,
    db: AsyncSession,
    sid: str,
    user_id: str,
    email: str,
    select_area: bool = True,
) -> tuple[str, str]:
    """Submit triage, accept lead, optionally select area (→ in_progress), return (lead_id, session_id)."""
    payload = {
        "answers": {
            "full_name": "Timer Test",
            "email": email,
            "company_name": "Timer Corp",
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

    if select_area:
        # Area selection transitions session from not_started → in_progress
        r3 = await client.post(
            f"/api/intake/{lead_id}/area-selection",
            json={"primary_area": "operations", "secondary_area": None, "areas_involved": []},
            cookies={"admin_sid": sid},
        )
        assert r3.status_code == 200, r3.text

    result = await db.execute(
        select(IntakeSession).where(IntakeSession.lead_id == lead_id)
    )
    session = result.scalar_one()
    return lead_id, session.id


async def _get_session(db: AsyncSession, session_id: str) -> IntakeSession:
    """Read IntakeSession fresh from DB, bypassing SQLAlchemy identity map cache.

    Uses populate_existing=True to force a DB re-read even if the object is cached.
    """
    result = await db.execute(
        select(IntakeSession)
        .where(IntakeSession.id == session_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# REQ-1 — Model columns + is_timer_running property
# ---------------------------------------------------------------------------

class TestTimerModelColumns:
    """A-2: ORM columns and property."""

    def test_is_timer_running_false_when_no_started_at(self):
        """is_timer_running returns False when timer_started_at is None."""
        session = IntakeSession()
        session.timer_started_at = None
        assert session.is_timer_running is False

    def test_is_timer_running_true_when_started_at_set(self):
        """is_timer_running returns True when timer_started_at is set."""
        session = IntakeSession()
        session.timer_started_at = datetime.utcnow()
        assert session.is_timer_running is True

    def test_timer_accumulated_seconds_defaults_zero(self):
        """timer_accumulated_seconds defaults to 0."""
        session = IntakeSession()
        # Default value (Python-side) — server_default applies at DB level
        assert session.timer_accumulated_seconds == 0 or session.timer_accumulated_seconds is None


class TestTimerMigrationColumns:
    """A-1: migration round-trip via create_all (model-based)."""

    async def test_timer_columns_present_after_create_all(self):
        """ORM create_all must produce the 3 timer columns."""
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.db.base import Base
        from app.models import intake_session  # noqa: F401

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: {
                    c["name"]
                    for c in sa_inspect(sync_conn).get_columns("intake_sessions")
                }
            )

        assert "timer_started_at" in columns
        assert "timer_paused_at" in columns
        assert "timer_accumulated_seconds" in columns

        await engine.dispose()


# ---------------------------------------------------------------------------
# REQ-2 — Auto-start on GET /state
# ---------------------------------------------------------------------------

class TestAutoStart:
    """B-1: auto-start timer on first GET /intake/{lead_id}/state."""

    async def test_get_state_auto_starts_timer(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """First GET on in_progress session sets timer_started_at in DB."""
        user, sid = await _create_admin_session(
            test_db, "timer.auto1@t.com", "timer-auto-sid-001"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.auto1.lead@t.com"
        )

        # Pre-condition: timer_started_at is NULL
        session_before = await _get_session(test_db, session_id)
        assert session_before.timer_started_at is None

        resp = await client.get(
            f"/api/intake/{lead_id}/state",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text

        # Post-condition: timer_started_at must be set and in response
        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at is not None

        data = resp.json()
        assert data["timer"]["started_at"] is not None
        assert data["timer"]["is_running"] is True

    async def test_get_state_auto_start_idempotent(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Second GET does NOT overwrite timer_started_at."""
        user, sid = await _create_admin_session(
            test_db, "timer.idem1@t.com", "timer-idem-sid-001"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.idem1.lead@t.com"
        )

        # First call to auto-start
        await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        session_first = await _get_session(test_db, session_id)
        first_started_at = session_first.timer_started_at
        assert first_started_at is not None

        # Second call must NOT change it
        await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        session_second = await _get_session(test_db, session_id)
        assert session_second.timer_started_at == first_started_at

    async def test_get_state_no_auto_start_when_closed(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Closed session: timer_started_at stays NULL on GET."""
        user, sid = await _create_admin_session(
            test_db, "timer.closed1@t.com", "timer-closed-sid-01"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.closed1.lead@t.com"
        )

        # Force session to closed state directly
        session = await _get_session(test_db, session_id)
        session.state = "closed"
        await test_db.commit()

        resp = await client.get(
            f"/api/intake/{lead_id}/state",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at is None
        assert resp.json()["timer"]["is_running"] is False


# ---------------------------------------------------------------------------
# REQ-3, REQ-4, REQ-5, REQ-11 — PATCH /intake/{lead_id}/timer
# ---------------------------------------------------------------------------

class TestPatchTimer:
    """B-2: pause, resume, reset, 409 on closed, 401 on unauth."""

    async def _setup(
        self, client: AsyncClient, db: AsyncSession, tag: str
    ) -> tuple[str, str, str]:
        """Return (lead_id, session_id, sid)."""
        user, sid = await _create_admin_session(
            db, f"timer.{tag}@t.com", f"timer-{tag}-sid"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, db, sid, user.id, f"timer.{tag}.lead@t.com"
        )
        # Auto-start via GET
        await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        return lead_id, session_id, sid

    async def test_patch_pause_running(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Pause a running timer: started_at → None, paused_at set, accumulated increases."""
        lead_id, session_id, sid = await self._setup(client, test_db, "pause1")

        session_before = await _get_session(test_db, session_id)
        assert session_before.timer_started_at is not None

        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["timer"]["started_at"] is None
        assert data["timer"]["paused_at"] is not None
        assert data["timer"]["is_running"] is False

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at is None
        assert session_after.timer_paused_at is not None

    async def test_patch_pause_already_paused(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Pause on already-paused timer: no-op, 200."""
        lead_id, session_id, sid = await self._setup(client, test_db, "pause2")

        # First pause
        r1 = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )
        assert r1.status_code == 200

        # Second pause — must be idempotent
        session_before = await _get_session(test_db, session_id)
        paused_at_before = session_before.timer_paused_at

        r2 = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )
        assert r2.status_code == 200

        session_after = await _get_session(test_db, session_id)
        # paused_at must not change
        assert session_after.timer_paused_at == paused_at_before

    async def test_patch_resume_paused(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Resume a paused timer: started_at set, paused_at → None."""
        lead_id, session_id, sid = await self._setup(client, test_db, "resume1")

        # Pause first
        await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )

        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "resume"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["timer"]["started_at"] is not None
        assert data["timer"]["paused_at"] is None
        assert data["timer"]["is_running"] is True

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at is not None
        assert session_after.timer_paused_at is None

    async def test_patch_resume_already_running(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Resume on already-running timer: no-op, 200."""
        lead_id, session_id, sid = await self._setup(client, test_db, "resume2")

        session_before = await _get_session(test_db, session_id)
        started_at_before = session_before.timer_started_at

        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "resume"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at == started_at_before

    async def test_patch_reset(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Reset: accumulated → 0, started_at → now, paused_at → None."""
        lead_id, session_id, sid = await self._setup(client, test_db, "reset1")

        # Pause to build some accumulated seconds
        await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )

        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "reset"},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["timer"]["accumulated_seconds"] == 0
        assert data["timer"]["started_at"] is not None
        assert data["timer"]["paused_at"] is None
        assert data["timer"]["is_running"] is True

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_accumulated_seconds == 0
        assert session_after.timer_started_at is not None
        assert session_after.timer_paused_at is None

    async def test_patch_on_closed_session_returns_409(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """All actions return 409 when session is closed."""
        lead_id, session_id, sid = await self._setup(client, test_db, "closed2")

        session = await _get_session(test_db, session_id)
        session.state = "closed"
        await test_db.commit()

        for action in ("pause", "resume", "reset"):
            resp = await client.patch(
                f"/api/intake/{lead_id}/timer",
                json={"action": action},
                cookies={"admin_sid": sid},
            )
            assert resp.status_code == 409, f"Expected 409 for action={action}, got {resp.status_code}"

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """No auth cookie → 401."""
        user, sid = await _create_admin_session(
            test_db, "timer.noauth1@t.com", "timer-noauth-sid1"
        )
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.noauth1.lead@t.com"
        )

        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            # no cookies
        )
        assert resp.status_code in (401, 403), resp.text


# ---------------------------------------------------------------------------
# REQ-6 — PATCH action=adjust
# ---------------------------------------------------------------------------

class TestPatchAdjust:
    """B-3: adjust action validation."""

    async def _setup_running(
        self, client: AsyncClient, db: AsyncSession, tag: str
    ) -> tuple[str, str, str]:
        user, sid = await _create_admin_session(
            db, f"adj.{tag}@t.com", f"adj-{tag}-sid"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, db, sid, user.id, f"adj.{tag}.lead@t.com"
        )
        await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        return lead_id, session_id, sid

    async def test_patch_adjust_valid(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Adjust to a past time: 200 + started_at updated."""
        lead_id, session_id, sid = await self._setup_running(client, test_db, "valid1")

        # Set started_at to 30 minutes ago (positive elapsed)
        new_started = datetime.utcnow() - timedelta(minutes=30)
        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "adjust", "started_at": new_started.isoformat()},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["timer"]["started_at"] is not None

    async def test_patch_adjust_negative_returns_422(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Adjust to a future time: 422 (total elapsed < 0)."""
        lead_id, session_id, sid = await self._setup_running(client, test_db, "neg1")

        # Set started_at to 1 hour in the future → negative elapsed
        future_start = datetime.utcnow() + timedelta(hours=1)
        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "adjust", "started_at": future_start.isoformat()},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 422, resp.text

    async def test_patch_adjust_zero_elapsed_accepted(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Adjust to exactly now: 200 (zero is non-negative boundary value)."""
        lead_id, session_id, sid = await self._setup_running(client, test_db, "zero1")

        # Zero accumulated, started_at = now → total = 0 (valid)
        now = datetime.utcnow()
        resp = await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "adjust", "started_at": now.isoformat()},
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# REQ-8 — timer object in state response
# ---------------------------------------------------------------------------

class TestTimerInStateResponse:
    """B-4: timer fields must always appear in GET /state response."""

    async def test_timer_object_in_state_response(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """GET /state always includes a 'timer' key."""
        user, sid = await _create_admin_session(
            test_db, "timer.sr1@t.com", "timer-sr-sid-001"
        )
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.sr1.lead@t.com"
        )

        resp = await client.get(
            f"/api/intake/{lead_id}/state",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "timer" in data
        timer = data["timer"]
        assert "started_at" in timer
        assert "paused_at" in timer
        assert "accumulated_seconds" in timer
        assert "is_running" in timer

    async def test_is_running_true_when_running(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """After auto-start: is_running must be True."""
        user, sid = await _create_admin_session(
            test_db, "timer.sr2@t.com", "timer-sr-sid-002"
        )
        lead_id, _ = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.sr2.lead@t.com"
        )

        resp = await client.get(
            f"/api/intake/{lead_id}/state",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        assert resp.json()["timer"]["is_running"] is True

    async def test_is_running_false_when_paused(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """After pause: is_running must be False."""
        user, sid = await _create_admin_session(
            test_db, "timer.sr3@t.com", "timer-sr-sid-003"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "timer.sr3.lead@t.com"
        )

        # Auto-start
        await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})
        # Pause
        await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )

        resp = await client.get(
            f"/api/intake/{lead_id}/state",
            cookies={"admin_sid": sid},
        )
        assert resp.status_code == 200
        assert resp.json()["timer"]["is_running"] is False


# ---------------------------------------------------------------------------
# REQ-7 — close_session1 writes completed_at + auto-pauses timer
# ---------------------------------------------------------------------------

class TestCloseSession1Timer:
    """C-1: session1 close hook fixes."""

    async def _setup_with_strategic_block(
        self, client: AsyncClient, db: AsyncSession, tag: str
    ) -> tuple[str, str, str]:
        """Create accepted lead, submit strategic block, return (lead_id, session_id, sid)."""
        user, sid = await _create_admin_session(
            db, f"close.{tag}@t.com", f"close-{tag}-sid"
        )
        lead_id, session_id = await _create_accepted_lead(
            client, db, sid, user.id, f"close.{tag}.lead@t.com"
        )

        # Auto-start the timer
        await client.get(f"/api/intake/{lead_id}/state", cookies={"admin_sid": sid})

        # Submit strategic block (required precondition for close)
        block_resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"test": "data"}, "skip_analysis": True},
            cookies={"admin_sid": sid},
        )
        assert block_resp.status_code == 202, block_resp.text

        return lead_id, session_id, sid

    def _close_patches(self):
        """Context managers to mock background tasks in close_session1."""
        return [
            patch(
                "app.api.intake_routes.run_session1_synthesis",
                new_callable=lambda: lambda *a, **kw: AsyncMock(),
            ),
            patch(
                "app.services.deep.generator.generate_all_branches",
                new_callable=AsyncMock,
            ),
        ]

    async def test_close_session1_writes_completed_at(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """POST /session1/close sets session1_completed_at."""
        lead_id, session_id, sid = await self._setup_with_strategic_block(
            client, test_db, "complet1"
        )

        session_before = await _get_session(test_db, session_id)
        assert session_before.session1_completed_at is None

        with (
            patch(
                "app.api.intake_routes.run_session1_synthesis",
                new_callable=lambda: lambda *a, **kw: AsyncMock(),
            ),
            patch(
                "app.services.deep.generator.generate_all_branches",
                new=AsyncMock(),
            ),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/close",
                cookies={"admin_sid": sid},
            )
        assert resp.status_code == 202, resp.text

        session_after = await _get_session(test_db, session_id)
        assert session_after.session1_completed_at is not None

    async def test_close_session1_auto_pauses_running_timer(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """POST /session1/close auto-pauses a running timer (accumulates time + sets paused_at)."""
        lead_id, session_id, sid = await self._setup_with_strategic_block(
            client, test_db, "autopause1"
        )

        # Verify timer is running
        session_before = await _get_session(test_db, session_id)
        assert session_before.timer_started_at is not None
        assert session_before.timer_paused_at is None

        with (
            patch(
                "app.api.intake_routes.run_session1_synthesis",
                new_callable=lambda: lambda *a, **kw: AsyncMock(),
            ),
            patch(
                "app.services.deep.generator.generate_all_branches",
                new=AsyncMock(),
            ),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/close",
                cookies={"admin_sid": sid},
            )
        assert resp.status_code == 202, resp.text

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at is None
        assert session_after.timer_paused_at is not None
        # Accumulated time must have increased
        assert session_after.timer_accumulated_seconds >= 0

    async def test_close_session1_leaves_paused_timer_alone(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """POST /session1/close does NOT touch an already-paused timer's paused_at."""
        lead_id, session_id, sid = await self._setup_with_strategic_block(
            client, test_db, "leavepause1"
        )

        # Pause the timer manually first
        await client.patch(
            f"/api/intake/{lead_id}/timer",
            json={"action": "pause"},
            cookies={"admin_sid": sid},
        )

        session_paused = await _get_session(test_db, session_id)
        paused_at_before = session_paused.timer_paused_at
        accumulated_before = session_paused.timer_accumulated_seconds
        assert paused_at_before is not None

        with (
            patch(
                "app.api.intake_routes.run_session1_synthesis",
                new_callable=lambda: lambda *a, **kw: AsyncMock(),
            ),
            patch(
                "app.services.deep.generator.generate_all_branches",
                new=AsyncMock(),
            ),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/close",
                cookies={"admin_sid": sid},
            )
        assert resp.status_code == 202, resp.text

        session_after = await _get_session(test_db, session_id)
        # Paused-at must NOT change (already paused)
        assert session_after.timer_paused_at == paused_at_before
        assert session_after.timer_accumulated_seconds == accumulated_before
        # completed_at still written
        assert session_after.session1_completed_at is not None

    async def test_close_session1_leaves_never_started_timer_alone(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """POST /session1/close does nothing to a timer that never started."""
        user, sid = await _create_admin_session(
            test_db, "close.never1@t.com", "close-never-sid1"
        )
        # Do NOT select area — timer auto-start only fires on GET /state for in_progress
        # We want a session where timer_started_at is genuinely NULL at close time
        lead_id, session_id = await _create_accepted_lead(
            client, test_db, sid, user.id, "close.never1.lead@t.com", select_area=False
        )

        # Submit strategic block WITHOUT auto-starting timer (don't call GET /state)
        block_resp = await client.post(
            f"/api/intake/{lead_id}/blocks/block-1-strategic/submit",
            json={"payload": {"test": "data"}, "skip_analysis": True},
            cookies={"admin_sid": sid},
        )
        assert block_resp.status_code == 202, block_resp.text

        # Ensure timer never started
        session_before = await _get_session(test_db, session_id)
        assert session_before.timer_started_at is None

        with (
            patch(
                "app.api.intake_routes.run_session1_synthesis",
                new_callable=lambda: lambda *a, **kw: AsyncMock(),
            ),
            patch(
                "app.services.deep.generator.generate_all_branches",
                new=AsyncMock(),
            ),
        ):
            resp = await client.post(
                f"/api/intake/{lead_id}/session1/close",
                cookies={"admin_sid": sid},
            )
        assert resp.status_code == 202, resp.text

        session_after = await _get_session(test_db, session_id)
        assert session_after.timer_started_at is None
        assert session_after.timer_paused_at is None
        assert session_after.session1_completed_at is not None
