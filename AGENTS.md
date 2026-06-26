# AGENTS.md

Operational notes for AI agents and humans working on `ai-readiness-pipeline`.

## Deployment

- **Host**: `server` (Tailscale). Connect with `ssh pepe@server`.
- **Project path on server**: `/home/pepe/Proyectos/ai-readiness-pipeline`
- **Container**: `air-pipeline` (docker-compose, port 8100, healthcheck on `/api/health`).
- **DB**: SQLite in docker volume `app_db` mounted at `/app/app/data` inside the container.

## Auth model (admin users)

- Table: `users` (see `app/models/user.py`).
- Hash: Argon2id via `app/auth/password.py::hash_password` (time_cost=3, memory_cost=64MiB, parallelism=4).
- CLI: `app/cli.py` exposes `create_admin` and `cleanup-form-data-keys`. **There is no `reset-password` CLI subcommand** — reset is done via the in-app password-reset flow (token by email) or, for ops, a one-shot `docker exec` script (below).

## Operational recipes

### Reset an admin user's password (ops, in-place)

Use only when the in-app reset flow is unavailable. Generates a strong random password, hashes with the project's own `hash_password`, and clears any pending reset token. The plaintext is printed once — capture it, hand it over securely, force the user to change it on first login.

```bash
ssh pepe@server 'docker exec -i air-pipeline python <<PYEOF
import asyncio, secrets, string, sys
from sqlalchemy import select
from app.auth.password import hash_password
from app.db.session import async_session_factory
from app.models.user import User

EMAIL = "user@example.com"   # ← change this
alphabet = string.ascii_letters + string.digits
new_pw = "".join(secrets.choice(alphabet) for _ in range(20))

async def run():
    async with async_session_factory() as s:
        u = (await s.execute(select(User).where(User.email == EMAIL))).scalar_one_or_none()
        if not u:
            print("USER_NOT_FOUND", file=sys.stderr); sys.exit(2)
        u.password_hash = hash_password(new_pw)
        u.password_reset_token_hash = None
        u.password_reset_expires_at = None
        await s.commit()
        print(f"OK email={u.email} id={u.id}")
        print(f"NEW_PASSWORD={new_pw}")

asyncio.run(run())
PYEOF'
```

### Create a new admin user

```bash
ssh pepe@server "docker exec air-pipeline python -m app.cli create_admin \
  --email <email> --password '<strong-password>'"
```

Password policy: ≥12 chars, ≥1 letter, ≥1 digit.

## CLAUDE.md

`CLAUDE.md` is a symlink to this file. Edit `AGENTS.md` — both projections stay in sync.
