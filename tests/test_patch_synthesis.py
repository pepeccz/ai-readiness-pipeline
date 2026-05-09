"""
tests/test_patch_synthesis.py — Integration tests for PATCH /api/intake/{lead_id}/session1/synthesis.

C.2: edit synthesis endpoint with state guard, admin auth, column writes.
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

_VALID_SYNTHESIS_BODY = {
    "summary": "Resumen editado.",
    "key_insights": ["Insight A", "Insight B"],
    "recommendations": [
        {
            "text": "Implementar automatización",
            "impact": "alto",
            "effort": "medio",
            "related_service": "desarrollo_acompanamiento",
        }
    ],
    "roadmap": {"d30": ["Paso 1"], "d60": [], "d90": []},
    "next_steps": ["Segunda sesión"],
}


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
    client: AsyncClient, db: AsyncSession, sid: str, user_id: str, email: str
) -> tuple[str, str]:
    payload = {
        "answers": {
            "full_name": "Test User",
            "email": email,
            "company_name": "Test Corp",
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

    result = await db.execute(select(IntakeSession).where(IntakeSession.lead_id == lead_id))
    session = result.scalar_one()
    return lead_id, session.id


async def _set_session_state(db: AsyncSession, session_id: str, state: str) -> None:
    result = await db.execute(select(IntakeSession).where(IntakeSession.id == session_id))
    session = result.scalar_one()
    session.state = state
    await db.commit()


# ─── Tests ───────────────────────────────────────────────────────────────────

async def test_patch_synthesis_success(client, test_db):
    """PATCH with valid body in session2_pending state → 200; synthesis_edited_json updated. (PR5b: deep_received retired)"""
    user, sid = await _create_admin_session(test_db, "patch@t.com", "patch-sid-001")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@corp1.com")
    await _set_session_state(test_db, session_id, "session2_pending")

    resp = await client.patch(
        f"/api/intake/{lead_id}/session1/synthesis",
        json=_VALID_SYNTHESIS_BODY,
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"] == "Resumen editado."


async def test_patch_synthesis_blocked_deep_pending(client, test_db):
    """PATCH in deep_pending state → 409."""
    user, sid = await _create_admin_session(test_db, "patch2@t.com", "patch-sid-002")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@corp2.com")
    await _set_session_state(test_db, session_id, "deep_pending")

    resp = await client.patch(
        f"/api/intake/{lead_id}/session1/synthesis",
        json=_VALID_SYNTHESIS_BODY,
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 409


async def test_patch_synthesis_requires_admin(client, test_db):
    """PATCH without auth → 401/403."""
    user, sid = await _create_admin_session(test_db, "patch3@t.com", "patch-sid-003")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@corp3.com")
    await _set_session_state(test_db, session_id, "session2_pending")

    resp = await client.patch(
        f"/api/intake/{lead_id}/session1/synthesis",
        json=_VALID_SYNTHESIS_BODY,
        # no cookies
    )

    assert resp.status_code in (401, 403)


async def test_patch_synthesis_404_unknown_lead(client, test_db):
    """PATCH with unknown lead_id → 404."""
    user, sid = await _create_admin_session(test_db, "patch4@t.com", "patch-sid-004")

    resp = await client.patch(
        "/api/intake/nonexistent-lead-id/session1/synthesis",
        json=_VALID_SYNTHESIS_BODY,
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 404


async def test_patch_synthesis_writes_edited_at(client, test_db):
    """PATCH success sets synthesis_edited_at on the IntakeSession."""
    user, sid = await _create_admin_session(test_db, "patch5@t.com", "patch-sid-005")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@corp5.com")
    await _set_session_state(test_db, session_id, "session2_pending")

    resp = await client.patch(
        f"/api/intake/{lead_id}/session1/synthesis",
        json=_VALID_SYNTHESIS_BODY,
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200

    result = await test_db.execute(select(IntakeSession).where(IntakeSession.id == session_id))
    session = result.scalar_one()
    assert session.synthesis_edited_json is not None
    assert session.synthesis_edited_at is not None
    assert session.session1_synthesis is None  # raw synthesis NEVER modified
