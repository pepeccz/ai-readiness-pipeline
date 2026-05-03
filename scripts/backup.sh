#!/bin/bash
# backup.sh — SQLite online backup for ai-readiness-pipeline
#
# Usage: ./scripts/backup.sh
# Cron:  0 3 * * * /opt/ai-readiness/scripts/backup.sh >> /var/log/ai-readiness-backup.log 2>&1
#
# Uses `sqlite3 .backup` (online, does NOT block writes — safe to run while app is up).
# Compresses with gzip. Deletes backups older than RETENTION_DAYS.
#
# Environment variables (all optional — override via cron env or shell):
#   BACKUP_DIR      — where to write .db.gz files  (default: /backups)
#   RETENTION_DAYS  — how many days to keep         (default: 30)
#   DB_PATH         — host path to the SQLite file  (default: auto-detect from docker volume)
#
# The host must have `sqlite3` installed (usually pre-installed on Debian/Ubuntu).
# To install: apt-get install -y sqlite3

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Default DB path: standard Docker named-volume path.
# The volume is named "app_db" in docker-compose.yml; Docker prefixes it with
# the compose project name. Override DB_PATH if your project name differs.
DB_PATH="${DB_PATH:-/var/lib/docker/volumes/ai-readiness-pipeline_app_db/_data/app.db}"

BACKUP_FILE="$BACKUP_DIR/app-$TIMESTAMP.db"

# Ensure backup destination exists
mkdir -p "$BACKUP_DIR"

# Verify source DB exists
if [ ! -f "$DB_PATH" ]; then
    echo "ERROR: DB not found at $DB_PATH. Set DB_PATH env var to override." >&2
    exit 1
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting backup — source: $DB_PATH"

# Online backup: sqlite3 .backup copies atomically without blocking writers.
# The resulting file is a complete, consistent SQLite database.
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Compress (replaces the uncompressed file in-place)
gzip "$BACKUP_FILE"
BACKUP_GZ="${BACKUP_FILE}.gz"

SIZE=$(du -sh "$BACKUP_GZ" | cut -f1)
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup written: $BACKUP_GZ ($SIZE)"

# Retention sweep: delete backups older than RETENTION_DAYS
PRUNED=$(find "$BACKUP_DIR" -name "app-*.db.gz" -mtime +"$RETENTION_DAYS" -print -delete | wc -l)
if [ "$PRUNED" -gt 0 ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Pruned $PRUNED backup(s) older than ${RETENTION_DAYS} days"
fi

# Optional offsite sync — uncomment and configure for your setup:
# rclone copy "$BACKUP_GZ" remote:ai-readiness-backups/
# aws s3 cp "$BACKUP_GZ" s3://your-bucket/ai-readiness-backups/

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup complete."
