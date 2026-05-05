"""
tests/integration/test_admin_leads_list.py

Integration tests for GET /api/admin/leads endpoint.

Covers:
- Unauthenticated request returns 401
- Paginated list returns correct shape
- Filter by bucket
- Filter by status
- Filter by sector
- Filter by date range (from_date, to_date)
- Search by email / company_name
- Pagination (page, page_size)
- Empty result returns 200 with empty items list
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.session_row import SessionRow
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_lead(
    *,
    email: str = "test@example.com",
    company_name: str = "Acme",
    sector: str = "tecnologia",
    triage_bucket: str = "review",
    status: str = "pending_review",
    triage_score: int = 60,
    created_at: datetime | None = None,
) -> Lead:
    now = created_at or datetime.now(tz=timezone.utc)
    return Lead(
        full_name="Test User",
        email=email,
        company_name=company_name,
        phone=None,
        sector=sector,
        company_size="10_25",
        respondent_role="ceo",
        ai_maturity="exploracion",
        ai_goals=["eficiencia"],
        urgency="normal",
        commitment="explorar",
        triage_payload={"answers": {}},
        triage_score=triage_score,
        triage_bucket=triage_bucket,
        status=status,
        created_at=now,
    )


async def _create_admin_session(db: AsyncSession) -> tuple[User, str]:
    """Create a test admin user + session, return (user, sid)."""
    from app.auth.password import hash_password

    user = User(
        email="admin@test.com",
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    sid = "test-session-id-12345678"
    session = SessionRow(
        id=sid,
        user_id=user.id,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
        last_seen_at=datetime.now(tz=timezone.utc),
        revoked_at=None,
    )
    db.add(session)
    await db.commit()
    return user, sid


# ---------------------------------------------------------------------------
# T4.1 - GET /api/admin/leads — 401 without session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_requires_auth(client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    resp = await client.get("/api/admin/leads")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T4.1 - Authenticated: empty list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_empty(client: AsyncClient, test_db: AsyncSession) -> None:
    """Authenticated request with no leads returns 200 empty list."""
    _, sid = await _create_admin_session(test_db)

    resp = await client.get("/api/admin/leads", cookies={"admin_sid": sid})
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert "page_size" in body
    assert "pages" in body


# ---------------------------------------------------------------------------
# T4.1 - Basic list returns all leads
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_returns_all(client: AsyncClient, test_db: AsyncSession) -> None:
    """List returns all leads with correct shape."""
    _, sid = await _create_admin_session(test_db)

    lead1 = _make_lead(email="a@co.com", company_name="Alpha")
    lead2 = _make_lead(email="b@co.com", company_name="Beta")
    test_db.add(lead1)
    test_db.add(lead2)
    await test_db.commit()

    resp = await client.get("/api/admin/leads", cookies={"admin_sid": sid})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

    # Check DTO shape
    item = body["items"][0]
    for field in ("id", "full_name", "email", "company_name", "sector",
                  "triage_bucket", "triage_score", "status", "created_at"):
        assert field in item, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# T4.1 - Filter by bucket
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_filter_bucket(client: AsyncClient, test_db: AsyncSession) -> None:
    """Filter by bucket returns only matching leads."""
    _, sid = await _create_admin_session(test_db)

    test_db.add(_make_lead(triage_bucket="auto_accept"))
    test_db.add(_make_lead(triage_bucket="auto_accept"))
    test_db.add(_make_lead(triage_bucket="review"))
    await test_db.commit()

    resp = await client.get(
        "/api/admin/leads?bucket=auto_accept", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(i["triage_bucket"] == "auto_accept" for i in body["items"])


# ---------------------------------------------------------------------------
# T4.1 - Filter by status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_filter_status(client: AsyncClient, test_db: AsyncSession) -> None:
    """Filter by status returns only matching leads."""
    _, sid = await _create_admin_session(test_db)

    test_db.add(_make_lead(status="pending_review"))
    test_db.add(_make_lead(status="accepted"))
    test_db.add(_make_lead(status="rejected"))
    await test_db.commit()

    resp = await client.get(
        "/api/admin/leads?status=accepted", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "accepted"


# ---------------------------------------------------------------------------
# T4.1 - Filter by sector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_filter_sector(client: AsyncClient, test_db: AsyncSession) -> None:
    """Filter by sector returns only matching leads."""
    _, sid = await _create_admin_session(test_db)

    test_db.add(_make_lead(sector="salud"))
    test_db.add(_make_lead(sector="retail"))
    await test_db.commit()

    resp = await client.get(
        "/api/admin/leads?sector=salud", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["sector"] == "salud"


# ---------------------------------------------------------------------------
# T4.1 - Filter by date range
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_filter_date_range(client: AsyncClient, test_db: AsyncSession) -> None:
    """Filter by from_date/to_date returns only matching leads."""
    _, sid = await _create_admin_session(test_db)

    now = datetime.now(tz=timezone.utc)
    test_db.add(_make_lead(created_at=now - timedelta(days=10)))
    test_db.add(_make_lead(created_at=now - timedelta(days=3)))
    test_db.add(_make_lead(created_at=now - timedelta(days=1)))
    await test_db.commit()

    from_date = (now - timedelta(days=5)).date().isoformat()
    resp = await client.get(
        f"/api/admin/leads?from_date={from_date}", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2  # only the 3-day and 1-day old leads


# ---------------------------------------------------------------------------
# T4.1 - Search by email
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_search_email(client: AsyncClient, test_db: AsyncSession) -> None:
    """Search param filters by email."""
    _, sid = await _create_admin_session(test_db)

    test_db.add(_make_lead(email="alice@example.com"))
    test_db.add(_make_lead(email="bob@other.com"))
    await test_db.commit()

    resp = await client.get(
        "/api/admin/leads?search=alice", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "alice@example.com"


# ---------------------------------------------------------------------------
# T4.1 - Search by company name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_search_company(client: AsyncClient, test_db: AsyncSession) -> None:
    """Search param filters by company_name."""
    _, sid = await _create_admin_session(test_db)

    test_db.add(_make_lead(company_name="AlphaCorp"))
    test_db.add(_make_lead(company_name="BetaInc"))
    await test_db.commit()

    resp = await client.get(
        "/api/admin/leads?search=BetaInc", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["company_name"] == "BetaInc"


# ---------------------------------------------------------------------------
# T4.1 - Pagination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_pagination(client: AsyncClient, test_db: AsyncSession) -> None:
    """Pagination returns correct slice."""
    _, sid = await _create_admin_session(test_db)

    for i in range(5):
        test_db.add(_make_lead(email=f"user{i}@co.com"))
    await test_db.commit()

    resp = await client.get(
        "/api/admin/leads?page=1&page_size=2", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["pages"] == 3


# ---------------------------------------------------------------------------
# T4.2 - GET /api/admin/leads/{id} — detail endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lead_detail(client: AsyncClient, test_db: AsyncSession) -> None:
    """GET /api/admin/leads/{id} returns full lead detail."""
    _, sid = await _create_admin_session(test_db)

    lead = _make_lead(email="detail@test.com", company_name="DetailCo")
    test_db.add(lead)
    await test_db.commit()
    await test_db.refresh(lead)

    resp = await client.get(
        f"/api/admin/leads/{lead.id}", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == lead.id
    assert body["email"] == "detail@test.com"
    assert body["company_name"] == "DetailCo"
    assert "triage_payload" in body
    assert "consents" in body


@pytest.mark.asyncio
async def test_get_lead_detail_not_found(client: AsyncClient, test_db: AsyncSession) -> None:
    """GET /api/admin/leads/{id} returns 404 for nonexistent id."""
    _, sid = await _create_admin_session(test_db)

    resp = await client.get(
        "/api/admin/leads/nonexistent-id", cookies={"admin_sid": sid}
    )
    assert resp.status_code == 404
