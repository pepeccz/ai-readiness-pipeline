"""
tests/integration/test_smoke.py — Smoke tests for pytest harness (Batch 0).

T0.4: Verifies that:
  - pytest discovers and runs this file.
  - The trivial smoke test passes.
  - The health endpoint returns HTTP 200 with a schema_version key (or any response).
"""

from httpx import AsyncClient


def test_smoke() -> None:
    """Trivial test — verifies pytest harness is operational."""
    assert True


async def test_health_endpoint(client: AsyncClient) -> None:
    """
    T0.4 acceptance: GET /api/health → 200.

    schema_version key may be absent until Batch 1 wires the real YAML loader.
    This test verifies the endpoint responds and the harness works end-to-end.
    """
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
