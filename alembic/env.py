"""
alembic/env.py — Alembic migration environment.

IMPORTANT — Sync vs async engines
==================================
Alembic's migration runner does NOT cleanly support async SQLAlchemy engines.
The application runtime uses an ASYNC engine (create_async_engine with aiosqlite)
in app/db/session.py. This file uses a separate SYNC engine (create_engine with
the plain sqlite:// driver) that points at the SAME database file.

  App engine (runtime):   sqlite+aiosqlite:///app/data/app.db  (async, aiosqlite)
  Alembic engine (migrations): sqlite:///app/data/app.db       (sync, stdlib sqlite3)

Both are valid SQLite connections to the same file. Migrations are run serially
(typically `alembic upgrade head` in the container entrypoint before uvicorn starts),
so there is no concurrency conflict. WAL mode means concurrent reads from the app
engine won't block, but in practice migrations finish before the app starts.

See design §2.2 "Alembic config" for the full rationale.

Usage:
  alembic upgrade head    — apply all pending migrations
  alembic current         — show current DB revision
  alembic history         — list all revisions
  alembic downgrade -1    — roll back one revision (use with care in production)
"""

import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Ensure the repo root is on sys.path so `import app` and `import config` work
# regardless of where alembic is invoked from.
# ---------------------------------------------------------------------------
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Import Base (triggers model registration via app/models/__init__.py side-effect).
# Must come AFTER sys.path manipulation.
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402, F401 — side-effect: registers all models against Base

# Alembic Config object — provides access to alembic.ini values.
config = context.config

# Set up Python logging from alembic.ini [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our metadata so `alembic revision --autogenerate` can diff.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    In offline mode Alembic emits SQL to stdout rather than executing against
    a live DB. Useful for generating SQL scripts to review before applying.

    `context.execute()` accepts string SQL; no DB connection is opened.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite-specific: render CREATE INDEX ... WHERE correctly.
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (normal operation).

    Opens a real sync JDBC connection to the SQLite file and applies pending
    migrations. `render_as_batch=True` is required for SQLite because ALTER TABLE
    support is limited — Alembic emits batch rewrite operations instead.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling for migrations — one-shot.
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite requires batch mode for most ALTER TABLE operations.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
