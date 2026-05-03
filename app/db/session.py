"""
app/db/session — Async SQLAlchemy engine + session factory + FastAPI dependency.

Two engines exist in this project (by design — see design §2.2):
  1. `engine` (async, aiosqlite) — used by ALL application code.
  2. A separate sync engine in alembic/env.py — used ONLY by Alembic migrations.
     Alembic does not cleanly support async engines for migrations. The app engine
     and the Alembic engine both point at the same DB file; they are just different
     driver instances. Never use the async engine in Alembic env.py.

Session lifetime (per-request):
  - A new AsyncSession is yielded for each HTTP request via `get_db()`.
  - The session is committed automatically if the handler completes without exception.
  - On any exception, the session is rolled back before being closed.
  - `expire_on_commit=False` prevents SQLAlchemy from expiring all attributes after
    commit, which would trigger lazy loads (incompatible with async sessions).

Background job sessions:
  Background runners in app/jobs/runners.py MUST open their OWN sessions via
  `async_session_factory()` because the request-scoped session from `get_db()` is
  closed when the response is sent (before the BackgroundTask runs).

  Example:
    async with async_session_factory() as session:
        async with session.begin():
            ...

check_same_thread=False:
  SQLite's default thread-safety check raises an error when the same connection
  is accessed from a thread other than the one that created it. With aiosqlite,
  the connection lives in a dedicated worker thread and asyncio drives it from
  the event loop thread — different threads. `check_same_thread=False` disables
  the check. It is safe here because aiosqlite serialises all access internally.
"""

import os
from collections.abc import AsyncIterator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from app.db.pragmas import register_pragmas

logger = structlog.get_logger(__name__)

# Ensure the data directory exists before SQLite tries to open the file.
# The DB_URL is typically "sqlite+aiosqlite:///app/data/app.db".
# We strip the driver prefix to get the file path.
_db_file_path = settings.db_url.replace("sqlite+aiosqlite:///", "")
_db_dir = os.path.dirname(_db_file_path)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)

# --- Async engine ---
engine = create_async_engine(
    settings.db_url,
    # Required for SQLite + async: aiosqlite runs the connection in a worker thread
    # that differs from the event loop thread. check_same_thread=False disables
    # SQLite's thread-safety guard (safe because aiosqlite serialises access).
    connect_args={"check_same_thread": False},
    # Echo SQL in debug mode only. Set DB_ECHO=true in .env for development.
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
)

# Apply SQLite WAL + foreign_keys + synchronous=NORMAL pragmas on every connection.
register_pragmas(engine)

# --- Session factory ---
# expire_on_commit=False: prevents attribute expiry after commit, which would
# trigger implicit lazy loads — broken in async context.
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- FastAPI dependency ---
async def get_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that yields a database session for the duration of
    a single HTTP request.

    Usage in route handlers:
      from fastapi import Depends
      from app.db.session import get_db
      from sqlalchemy.ext.asyncio import AsyncSession

      @router.get("/example")
      async def example(db: AsyncSession = Depends(get_db)):
          ...

    DO NOT use this in background jobs — the session is closed when the
    response is sent. Use `async_session_factory()` directly instead.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
