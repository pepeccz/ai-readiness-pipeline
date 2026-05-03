#!/bin/bash
# restore.sh — Restore an ai-readiness-pipeline SQLite backup
#
# Usage: ./scripts/restore.sh <path/to/app-YYYYMMDD_HHMMSS.db.gz>
#
# WARNING: This REPLACES the current database. All data since the backup
# was taken will be LOST. Verify the backup file before running.
#
# The script:
#   1. Stops the container (prevents DB corruption during replace)
#   2. Decompresses the backup directly into the Docker volume path
#   3. Starts the container again
#
# Environment variables:
#   DB_VOLUME_PATH — host path to the SQLite file in the Docker volume
#                    (default: auto-detect from standard compose project name)

set -euo pipefail

BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <path/to/app-YYYYMMDD_HHMMSS.db.gz>" >&2
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

DB_VOLUME_PATH="${DB_VOLUME_PATH:-/var/lib/docker/volumes/ai-readiness-pipeline_app_db/_data/app.db}"

echo "=========================================="
echo "  AI Readiness Pipeline — DB Restore"
echo "=========================================="
echo "Backup : $BACKUP_FILE"
echo "Target : $DB_VOLUME_PATH"
echo ""
echo "WARNING: This will REPLACE the current database."
echo "Press Ctrl+C in the next 5 seconds to cancel."
sleep 5

echo ""
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Stopping container..."
docker compose stop pipeline 2>/dev/null || docker compose stop app 2>/dev/null || true

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Restoring database..."
# Ensure parent directory exists (first-run scenario)
mkdir -p "$(dirname "$DB_VOLUME_PATH")"

# Decompress into the volume path, replacing the existing file
gunzip -c "$BACKUP_FILE" > "$DB_VOLUME_PATH"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting container..."
docker compose start pipeline 2>/dev/null || docker compose start app 2>/dev/null || true

echo ""
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Restore complete."
echo ""
echo "Verify the restore worked:"
echo "  curl -s https://<your-host>/api/health | jq ."
echo "  curl -s https://<your-host>/api/admin/auth/me  # expect 401 (not 500)"
