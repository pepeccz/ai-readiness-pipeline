#!/bin/bash
set -euo pipefail

# Run Alembic migrations on container startup. Idempotent — Alembic
# checks the current revision and only applies what's missing.
echo "[entrypoint] Running alembic upgrade head..."
alembic upgrade head
echo "[entrypoint] Migrations done. Starting application..."

exec "$@"
