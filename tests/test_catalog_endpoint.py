"""
tests/test_catalog_endpoint.py — Integration tests for GET /api/catalog/services.

C.1: endpoint returns 3 services with correct shape. Unauthenticated (ADR-15).
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_catalog_endpoint_returns_three_services(client):
    """GET /api/catalog/services returns 200 with 3 services."""
    resp = await client.get("/api/catalog/services")

    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert len(data["services"]) == 3


@pytest.mark.asyncio
async def test_catalog_endpoint_shape(client):
    """Each service has required fields: key, nombre, descripcion, cuando_recomendar."""
    resp = await client.get("/api/catalog/services")

    assert resp.status_code == 200
    services = resp.json()["services"]

    for svc in services:
        assert "key" in svc
        assert "nombre" in svc
        assert "descripcion" in svc
        assert "cuando_recomendar" in svc
        assert isinstance(svc["cuando_recomendar"], list)


@pytest.mark.asyncio
async def test_catalog_endpoint_known_keys(client):
    """Endpoint returns exactly the 3 expected service keys."""
    resp = await client.get("/api/catalog/services")

    keys = {svc["key"] for svc in resp.json()["services"]}
    assert keys == {
        "diagnostico_profundo",
        "desarrollo_acompanamiento",
        "formacion_personalizada",
    }


@pytest.mark.asyncio
async def test_catalog_endpoint_no_auth_required(client):
    """Catalog endpoint is unauthenticated — no auth header needed."""
    # client has no auth headers set — if this returns 200 it's unauthenticated
    resp = await client.get("/api/catalog/services")
    assert resp.status_code == 200
