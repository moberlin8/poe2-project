#!/bin/bash
# b2_backup.sh — PoE2 project backup script
# Syncs project data to B2 bucket: hal-poe2-project-data
# Uses rclone --backup-dir to version changes to hal-b2-snapshots
# 
# Usage: ./b2_backup.sh
# Scheduled via cron: daily at 3:30 AM UTC

set -euo pipefail

SOURCE_DIR="/home/mao/DaveMatt/poe2-project/data"
BUCKET_NAME="hal-poe2-project-data"
SNAPSHOT_BUCKET="hal-b2-snapshots"
TIMESTAMP=$(date +"%Y-%m-%dT%H-%M-%SZ")
LOG_FILE="/home/mao/DaveMatt/poee-project/scripts/backup.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting PoE2 backup" >> "$LOG_FILE"

# Sync data files to B2 main bucket, with older snapshots to backup-dir bucket
# --backup-dir stores overwritten/deleted files in the snapshots bucket
# This follows the same pattern as the GD project backup
# Note: --backup-dir must NOT overlap with destination bucket path
"$HOME/.local/bin/rclone" sync "$SOURCE_DIR" "b2:${BUCKET_NAME}/data" \
    --backup-dir "b2:${SNAPSHOT_BUCKET}/poe2-snapshots/${TIMESTAMP}" \
    --exclude "*.tmp" \
    --verbose >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Backup completed successfully" >> "$LOG_FILE"
    
    # Also sync scripts and output
    "$HOME/.local/bin/rclone" sync "/home/mao/DaveMatt/poe2-project/scripts" "b2:${BUCKET_NAME}/scripts" \
        --backup-dir "b2:${SNAPSHOT_BUCKET}/poe2-snapshots/${TIMESTAMP}" \
        --exclude "*.tmp" \
        --verbose >> "$LOG_FILE" 2>&1
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Scripts backup completed" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Backup FAILED with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
