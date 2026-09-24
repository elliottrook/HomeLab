#!/bin/bash

set -euo pipefail

REPO="${HOMELAB_REPO:-$HOME/lab/homelab}"
source "$REPO/scripts/lib/output.sh"

PRIVATE_BACKUPS="${HOMELAB_BACKUP_ROOT:-$HOME/lab/private-backups}"

BACKUP_ROOT="$PRIVATE_BACKUPS/video-archiver"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"
chmod 700 "$PRIVATE_BACKUPS" "$BACKUP_ROOT" "$BACKUP_DIR"

header "Video Archiver Configuration Backup"

info "Collecting video-archiver config/state from TrueNAS..."

fetch() {
    local remote_path="$1"
    local dest="$2"

    if ! ssh -o BatchMode=yes -o ConnectTimeout=8 truenas "cat '$remote_path'" > "$dest" 2>/dev/null; then
        error "Failed to collect $(basename "$dest")"
        exit 1
    fi
}

fetch "/mnt/Media/data/tools/video-archiver/config.json" "$BACKUP_DIR/config.json"
fetch "/mnt/Media/data/tools/video-archiver/.env" "$BACKUP_DIR/.env"
fetch "/mnt/Media/data/tools/video-archiver/run-scheduled.sh" "$BACKUP_DIR/run-scheduled.sh"
# Archive compaction (added 2026-09-24): scheduled wrapper and per-file outcome state.
fetch "/mnt/Media/data/tools/video-archiver/run-compact.sh" "$BACKUP_DIR/run-compact.sh"
fetch "/mnt/Media/data/tools/video-archiver/work/compact-state.json" "$BACKUP_DIR/compact-state.json"

chmod 600 "$BACKUP_DIR"/* "$BACKUP_DIR"/.env

success "Video archiver config/state saved"
echo
show_file_details "$BACKUP_DIR"
footer "Video archiver backup completed successfully"
