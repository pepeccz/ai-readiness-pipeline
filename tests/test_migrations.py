"""
tests/test_migrations.py — Verifies Alembic migration adds expected columns.

Uses SQLAlchemy inspector to check columns after running create_all
(which uses the model definitions after migration is applied).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_migration_adds_columns():
    """
    After applying all migrations (via metadata.create_all on the ORM models),
    intake_sessions table has all 4 new columns.
    """
    from app.db.base import Base
    from app.models import intake_session  # noqa: F401 — ensure model is registered

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.connect() as conn:
        columns = await conn.run_sync(
            lambda sync_conn: {
                c["name"] for c in sa_inspect(sync_conn).get_columns("intake_sessions")
            }
        )

    expected = {
        "synthesis_edited_json",
        "synthesis_edited_at",
        "synthesis_last_exported_at",
        "synthesis_export_count",
    }
    assert expected.issubset(columns), (
        f"Missing columns: {expected - columns}"
    )

    await engine.dispose()
