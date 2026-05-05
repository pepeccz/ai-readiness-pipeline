"""
app/models — SQLAlchemy ORM models.

All models are imported here so Alembic's env.py can reach Base.metadata
with a single `import app.models` without knowing each model file. The import
side-effect registers every model class against Base.metadata, which Alembic
uses when generating or running migrations.

Models:
  User          — admin user accounts
  SessionRow    — server-side session records (named to avoid clash with SA Session)
  LoginAttempt  — rate-limiting log for auth/reset/submission attempts
  Assessment    — the core assessment record (hybrid flat+JSON schema)
  Lead          — v2 TRIAGE lead record
  Consent       — GDPR consent audit trail (RESTRICT delete)
  IntakeSession — consultant-led intake session per accepted Lead
  BlockAnalysis — LLM analysis per (session, block) pair
  Suggestion    — individual suggestions extracted from block analysis
  DeepBranch    — AI-generated deep-dive questions sent to client
"""

from app.models.assessment import Assessment
from app.models.block_analysis import BlockAnalysis
from app.models.consent import Consent
from app.models.deep_branch import DeepBranch
from app.models.intake_session import IntakeSession
from app.models.lead import Lead
from app.models.login_attempt import LoginAttempt
from app.models.session_row import SessionRow
from app.models.suggestion import Suggestion
from app.models.user import User

__all__ = [
    "Assessment",
    "BlockAnalysis",
    "Consent",
    "DeepBranch",
    "IntakeSession",
    "Lead",
    "LoginAttempt",
    "SessionRow",
    "Suggestion",
    "User",
]
