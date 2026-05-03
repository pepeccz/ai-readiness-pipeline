"""
app/db/base — SQLAlchemy DeclarativeBase.

All models must inherit from `Base`. Alembic's env.py imports this module
so that `Base.metadata` contains all table definitions at migration time.

Import pattern (in each model file):
  from app.db.base import Base

Import pattern (in alembic/env.py):
  from app.db.base import Base
  import app.models  # side-effect: registers all models against Base.metadata
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""

    pass
