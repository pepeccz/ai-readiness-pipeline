"""
tests/conftest.py — Shared pytest fixtures for ai-readiness-pipeline test suite.

Fixtures:
  test_db       — async SQLAlchemy session over sqlite+aiosqlite:///:memory:
                  Creates all tables, yields session, tears down cleanly.
  override_get_db — dependency override helper for DI injection.
  client        — httpx AsyncClient with FastAPI app and test_db override.

All fixtures are async and use pytest-asyncio's auto mode.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db

# ---------------------------------------------------------------------------
# In-memory async engine (isolated per test session)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# T0.2 — test_db: creates all tables, yields session, tears down cleanly
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async SQLAlchemy session backed by an in-memory SQLite database.

    Each test function gets a fresh set of tables (create_all before yield,
    drop_all after yield). This ensures full isolation between tests without
    requiring a separate DB file.
    """
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _test_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# T0.3 — override_get_db + client: FastAPI app with test_db DI override
# ---------------------------------------------------------------------------


async def _override_get_db_factory(session: AsyncSession):
    """Return a get_db override that yields the provided session."""

    async def _override() -> AsyncIterator[AsyncSession]:
        yield session

    return _override


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    httpx AsyncClient wrapping the FastAPI app with the in-memory DB override.

    Usage in tests:
        async def test_something(client: AsyncClient):
            resp = await client.get("/api/health")
            assert resp.status_code == 200
    """
    from webhook_service import app  # imported here to avoid circular imports at collection

    override = await _override_get_db_factory(test_db)
    app.dependency_overrides[get_db] = override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.pop(get_db, None)
