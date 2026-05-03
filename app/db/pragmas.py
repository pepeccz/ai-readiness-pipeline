"""
app/db/pragmas — SQLite connection pragmas.

Registers an event listener on the SYNC engine underlying the async engine.
This is a SQLAlchemy quirk: connection events fire on the sync layer, even
when the app uses an async engine. You MUST listen on `engine.sync_engine`,
not on the async engine directly.

Pragmas applied on every new connection:
  PRAGMA journal_mode=WAL
    — Write-Ahead Logging allows concurrent reads during writes. Critical
      because the admin editor and the background enrichment runners may
      both access the DB simultaneously.

  PRAGMA synchronous=NORMAL
    — Reduces fsync() calls compared to the default FULL mode. Safe with WAL:
      you might lose the last committed transaction on OS crash (not power loss),
      but WAL itself is crash-safe. Gives ~2× write throughput on typical VPS.

  PRAGMA foreign_keys=ON
    — SQLite ignores foreign key constraints by default. Must be enabled per
      connection. Ensures referential integrity (e.g. sessions.user_id → users.id).

Usage: call `register_pragmas(engine)` once after creating the async engine
in app/db/session.py.
"""

import structlog
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

logger = structlog.get_logger(__name__)


def register_pragmas(engine: AsyncEngine) -> None:
    """
    Attach the pragma event listener to the underlying sync engine.

    Must be called once, immediately after `create_async_engine(...)`.
    The listener fires for every new connection from the connection pool.
    """

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
        logger.debug("sqlite_pragmas_applied", journal_mode="WAL", synchronous="NORMAL", foreign_keys="ON")
