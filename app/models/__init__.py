"""
app/models — SQLAlchemy ORM models.

All models are imported here so Alembic's env.py can reach Base.metadata
with a single `import app.models` without knowing each model file. The import
side-effect registers every model class against Base.metadata, which Alembic
uses when generating or running migrations.

Models (TASK-A-05):
  User         — admin user accounts
  SessionRow   — server-side session records (named to avoid clash with SA Session)
  LoginAttempt — rate-limiting log for auth/reset/submission attempts
  Assessment   — the core assessment record (hybrid flat+JSON schema)
"""

from app.models.assessment import Assessment
from app.models.login_attempt import LoginAttempt
from app.models.session_row import SessionRow
from app.models.user import User

__all__ = ["Assessment", "LoginAttempt", "SessionRow", "User"]
