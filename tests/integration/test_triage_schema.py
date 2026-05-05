"""
tests/integration/test_triage_schema.py — T3.2

Integration tests for GET /api/public/triage/schema endpoint.
"""

import pytest


@pytest.mark.asyncio
async def test_triage_schema_returns_200(client):
    resp = await client.get("/api/public/triage/schema")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_triage_schema_content_type_json(client):
    resp = await client.get("/api/public/triage/schema")
    assert "application/json" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_triage_schema_has_schema_version(client):
    resp = await client.get("/api/public/triage/schema")
    data = resp.json()
    assert "schema_version" in data
    assert isinstance(data["schema_version"], str)


@pytest.mark.asyncio
async def test_triage_schema_has_schema_key(client):
    resp = await client.get("/api/public/triage/schema")
    data = resp.json()
    assert "schema" in data


@pytest.mark.asyncio
async def test_triage_schema_no_auth_required(client):
    """Endpoint is public — no Authorization header needed."""
    resp = await client.get("/api/public/triage/schema")
    assert resp.status_code != 401
    assert resp.status_code != 403
