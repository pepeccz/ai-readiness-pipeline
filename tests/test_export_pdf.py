"""
tests/test_export_pdf.py — Integration tests for POST /api/intake/{lead_id}/session1/export-pdf.

C.6: PDF export with state guard, synthesis null guard, streaming response, DB counters.
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

_SAMPLE_SYNTHESIS = {
    "summary": "Empresa lista para piloto IA.",
    "key_insights": ["Alta madurez operativa"],
    "recommendations": [
        {"text": "Piloto RPA", "impact": "alto", "effort": "medio", "related_service": None}
    ],
    "roadmap": {"d30": ["Diagnóstico"], "d60": [], "d90": []},
    "next_steps": ["Siguiente sesión"],
    "hypothesis": "Hipótesis interna (NO debe aparecer en PDF).",
    "generated_at": "2026-05-06T12:00:00Z",
    "model": "claude-sonnet-4-6",
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
            "full_name": "Export Test",
            "email": email,
            "company_name": "Exportadora SA",
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


async def _set_session_state_and_synthesis(
    db: AsyncSession, session_id: str, state: str, synthesis: dict | None = None
) -> None:
    result = await db.execute(select(IntakeSession).where(IntakeSession.id == session_id))
    session = result.scalar_one()
    session.state = state
    if synthesis is not None:
        session.session1_synthesis = synthesis
    await db.commit()


# ─── Tests ───────────────────────────────────────────────────────────────────

async def test_export_pdf_success(client, test_db):
    """POST export-pdf with synthesis in deep_received → 200, PDF bytes, correct headers."""
    user, sid = await _create_admin_session(test_db, "exp@t.com", "exp-sid-001")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@exp1.com")
    await _set_session_state_and_synthesis(test_db, session_id, "deep_received", _SAMPLE_SYNTHESIS)

    resp = await client.post(
        f"/api/intake/{lead_id}/session1/export-pdf",
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "content-disposition" in resp.headers
    assert "exportadora" in resp.headers["content-disposition"].lower()
    assert resp.content[:4] == b"%PDF"


async def test_export_pdf_blocked_deep_pending(client, test_db):
    """POST export-pdf in deep_pending → 409."""
    user, sid = await _create_admin_session(test_db, "exp2@t.com", "exp-sid-002")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@exp2.com")
    await _set_session_state_and_synthesis(test_db, session_id, "deep_pending", _SAMPLE_SYNTHESIS)

    resp = await client.post(
        f"/api/intake/{lead_id}/session1/export-pdf",
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 409


async def test_export_pdf_null_synthesis_blocked(client, test_db):
    """POST export-pdf when synthesis is null → 409."""
    user, sid = await _create_admin_session(test_db, "exp3@t.com", "exp-sid-003")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@exp3.com")
    await _set_session_state_and_synthesis(test_db, session_id, "deep_received", synthesis=None)

    resp = await client.post(
        f"/api/intake/{lead_id}/session1/export-pdf",
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 409


async def test_export_pdf_uses_edited_synthesis(client, test_db):
    """When synthesis_edited_json exists, PDF is rendered from it."""
    user, sid = await _create_admin_session(test_db, "exp4@t.com", "exp-sid-004")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@exp4.com")
    await _set_session_state_and_synthesis(test_db, session_id, "deep_received", _SAMPLE_SYNTHESIS)

    # Set an edited synthesis
    result = await test_db.execute(select(IntakeSession).where(IntakeSession.id == session_id))
    session = result.scalar_one()
    edited = {**_SAMPLE_SYNTHESIS, "summary": "Resumen editado por el consultor."}
    session.synthesis_edited_json = edited
    await test_db.commit()

    resp = await client.post(
        f"/api/intake/{lead_id}/session1/export-pdf",
        cookies={"admin_sid": sid},
    )

    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


async def test_export_pdf_bumps_count_and_timestamp(client, test_db):
    """Successful export increments synthesis_export_count and sets synthesis_last_exported_at."""
    user, sid = await _create_admin_session(test_db, "exp5@t.com", "exp-sid-005")
    lead_id, session_id = await _create_accepted_lead(client, test_db, sid, user.id, "lead@exp5.com")
    await _set_session_state_and_synthesis(test_db, session_id, "deep_received", _SAMPLE_SYNTHESIS)

    resp = await client.post(
        f"/api/intake/{lead_id}/session1/export-pdf",
        cookies={"admin_sid": sid},
    )
    assert resp.status_code == 200

    await test_db.refresh(await test_db.get(IntakeSession, session_id))
    result = await test_db.execute(select(IntakeSession).where(IntakeSession.id == session_id))
    session = result.scalar_one()

    assert session.synthesis_export_count == 1
    assert session.synthesis_last_exported_at is not None
