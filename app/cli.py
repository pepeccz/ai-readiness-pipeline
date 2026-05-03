"""
app/cli — Admin command-line interface for the AI Readiness pipeline.

Entry point:
  python -m app.cli create_admin --email pepe@zanovix.com --password 'strong-pass'

Or, via the package __main__ shim (python -m app ...):
  python -m app create_admin --email pepe@zanovix.com --password 'strong-pass'

Available subcommands:
  create_admin            — Bootstrap the first (or additional) admin user directly in the DB.
                            Use this on first deploy before any UI is available.
  cleanup-form-data-keys  — Remove orphan / legacy form_data keys from all assessments.
                            Dry-run by default; pass --apply to actually delete.

Design notes:
  - Uses argparse — no Click/Typer dep needed for bootstrapping commands.
  - Opens its own async SQLAlchemy session via async_session_factory() (NOT get_db(),
    which is a FastAPI dependency that requires a running request context).
  - Password validation mirrors the reset-password endpoint policy (min 12 chars,
    1 letter + 1 digit) so operators can't create weak credentials from the CLI.
  - Exit codes: 0 = success, 1 = validation error, 2 = user already exists.
  - Errors → stderr, success confirmation → stdout.

Invocation from Docker (design §2.2 migration plan step 2):
  docker exec ai-readiness python -m app.cli create_admin \\
    --email pepe@zanovix.com \\
    --password '<strong-password-from-1password>'

  docker exec air-pipeline python -m app.cli cleanup-form-data-keys          # dry-run
  docker exec air-pipeline python -m app.cli cleanup-form-data-keys --apply  # commit
"""

import argparse
import asyncio
import re
import sys
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.orm import attributes

from app.auth.password import hash_password
from app.db.session import async_session_factory
from app.models.assessment import Assessment
from app.models.user import User
from app.utils import FORM_DATA_KEYS

logger = structlog.get_logger(__name__)

# Password policy — identical to the reset-password endpoint check.
# Min 12 chars is enforced separately before this regex is checked.
_PASSWORD_MIN_LEN = 12
_PASSWORD_RE = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d).+$")

# Basic email format check — pydantic is not available in CLI context
# without a full app import chain. This regex covers the overwhelming
# majority of valid addresses and is good enough for a bootstrap command
# used by a single operator.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> None:
    """Raise SystemExit(1) if the email format looks invalid."""
    if not _EMAIL_RE.match(email):
        print(f"Error: '{email}' no parece un email válido.", file=sys.stderr)
        sys.exit(1)


def _validate_password(password: str) -> None:
    """
    Enforce password policy. Raises SystemExit(1) on violation.

    Policy (same as reset-password endpoint):
      - Minimum 12 characters
      - At least one letter AND at least one digit
    """
    if len(password) < _PASSWORD_MIN_LEN:
        print(
            f"Error: La contraseña debe tener al menos {_PASSWORD_MIN_LEN} caracteres.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not _PASSWORD_RE.match(password):
        print(
            "Error: La contraseña debe tener al menos una letra y un número.",
            file=sys.stderr,
        )
        sys.exit(1)


async def _create_admin(email: str, password: str) -> None:
    """
    Core async logic for create_admin subcommand.

    Opens its own session (not request-scoped). Checks for duplicates, inserts
    the user row, and commits. Exits with the appropriate code on error.
    """
    _validate_email(email)
    _validate_password(password)

    async with async_session_factory() as session:
        # Check for existing user with this email.
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(
                f"Error: Ya existe un usuario con el email '{email}' (id: {existing.id}).",
                file=sys.stderr,
            )
            sys.exit(2)

        # Create the admin user.
        password_hash = hash_password(password)
        now = datetime.now(tz=timezone.utc)
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True,
            created_at=now,
        )
        session.add(user)
        await session.flush()  # populate user.id before commit

        user_id = str(user.id)  # capture before commit (expire_on_commit=False, so safe either way)

        await session.commit()

    print(f"Admin user created: {email} (id: {user_id})")
    logger.info("cli_create_admin_success", email=email, user_id=user_id)


async def _cleanup_form_data_keys(apply: bool) -> None:
    """
    Core async logic for cleanup-form-data-keys subcommand.

    Scans every assessment for orphan form_data keys (keys NOT in FORM_DATA_KEYS)
    and matching field_sources entries (keys starting with "form_data.<orphan>").

    With apply=False (dry-run): logs findings but does NOT commit.
    With apply=True: deletes orphan keys, calls flag_modified, and commits.

    Idempotent: a second run on a clean DB touches 0 rows.
    """
    mode = "apply" if apply else "dry-run"
    _log = structlog.get_logger(__name__)
    _log.info("cleanup_form_data_keys_start", mode=mode, known_keys=len(FORM_DATA_KEYS))

    total_orphan_keys = 0
    affected_assessments = 0

    async with async_session_factory() as session:
        result = await session.execute(select(Assessment))
        assessments = result.scalars().all()

        _log.info("cleanup_assessments_loaded", count=len(assessments))

        for assessment in assessments:
            form_data: dict = assessment.form_data or {}
            field_sources: dict = assessment.field_sources or {}

            # Find orphan keys in form_data (keys not in the canonical allowlist)
            orphan_fd_keys = [k for k in form_data if k not in FORM_DATA_KEYS]

            # Find matching field_sources entries: "form_data.<orphan_key>"
            orphan_fs_keys = [
                k for k in field_sources
                if k.startswith("form_data.")
                and k[len("form_data."):] not in FORM_DATA_KEYS
            ]

            if not orphan_fd_keys and not orphan_fs_keys:
                continue

            assessment_id = str(assessment.id)
            company = assessment.company_name or "(sin nombre)"
            orphan_count = len(orphan_fd_keys) + len(orphan_fs_keys)
            total_orphan_keys += orphan_count
            affected_assessments += 1

            _log.info(
                "cleanup_orphans_found",
                assessment_id=assessment_id,
                company=company,
                mode=mode,
                orphan_form_data_keys=orphan_fd_keys,
                orphan_field_sources_keys=orphan_fs_keys,
                total=orphan_count,
            )

            if apply:
                # Mutate form_data: remove orphan keys
                if orphan_fd_keys:
                    new_form_data = {k: v for k, v in form_data.items() if k not in orphan_fd_keys}
                    assessment.form_data = new_form_data
                    attributes.flag_modified(assessment, "form_data")

                # Mutate field_sources: remove orphan entries
                if orphan_fs_keys:
                    new_field_sources = {k: v for k, v in field_sources.items() if k not in orphan_fs_keys}
                    assessment.field_sources = new_field_sources
                    attributes.flag_modified(assessment, "field_sources")

                _log.info(
                    "cleanup_orphans_deleted",
                    assessment_id=assessment_id,
                    company=company,
                    deleted_form_data_keys=orphan_fd_keys,
                    deleted_field_sources_keys=orphan_fs_keys,
                )

        if apply and affected_assessments > 0:
            await session.commit()
            _log.info("cleanup_committed", affected_assessments=affected_assessments)

    action = "Deleted" if apply else "Dry-run: would delete"
    print(
        f"\nFound {total_orphan_keys} orphan key(s) across {affected_assessments} assessment(s). "
        f"{action}.\n"
    )


def main() -> None:
    """
    CLI entry point. Parses arguments and dispatches to the appropriate subcommand.

    This function is SYNCHRONOUS so it can be called from __main__.py without
    needing asyncio.run() at the top level — asyncio.run() is called internally
    by each async subcommand handler. This keeps cli.py importable in tests
    without triggering event loop creation at import time.
    """
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="AI Readiness Pipeline — admin CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- create_admin subcommand ---
    create_admin_parser = subparsers.add_parser(
        "create_admin",
        help="Create a new admin user in the database.",
        description=(
            "Bootstrap an admin user directly in the DB. "
            "Run this on first deploy to create the initial login before any UI is available."
        ),
    )
    create_admin_parser.add_argument(
        "--email",
        required=True,
        help="Admin email address (used as login identifier).",
    )
    create_admin_parser.add_argument(
        "--password",
        required=True,
        help=(
            "Admin password. Min 12 chars, at least 1 letter + 1 digit. "
            "Use a password manager (e.g. 1Password) to generate a strong value."
        ),
    )

    # --- cleanup-form-data-keys subcommand ---
    cleanup_parser = subparsers.add_parser(
        "cleanup-form-data-keys",
        help="Remove orphan / legacy form_data keys from all assessments.",
        description=(
            "Scans all assessments and removes any form_data keys not in the canonical "
            "FORM_DATA_KEYS allowlist, plus matching field_sources entries. "
            "Defaults to --dry-run; pass --apply to actually write changes."
        ),
    )
    cleanup_parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help=(
            "Actually delete orphan keys and commit. "
            "Without this flag the command runs in dry-run mode (no writes)."
        ),
    )

    args = parser.parse_args()

    if args.command == "create_admin":
        asyncio.run(_create_admin(args.email, args.password))
    elif args.command == "cleanup-form-data-keys":
        asyncio.run(_cleanup_form_data_keys(apply=args.apply))
    else:
        # Should never reach here because subparsers are required, but guard anyway.
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
