#!/bin/bash

set -euo pipefail

REPO="$HOME/lab/homelab"
source "$REPO/scripts/lib/output.sh"

BACKUP_ROOT="$HOME/lab/private-backups/jellyfin-integrity"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"
chmod 700 "$HOME/lab/private-backups" "$BACKUP_ROOT" "$BACKUP_DIR"

header "Jellyfin Integrity Tool Configuration Backup"

info "Collecting config and reference manifests from TrueNAS..."

fetch() {
    local remote_path="$1"
    local dest="$2"

    if ! ssh -o BatchMode=yes -o ConnectTimeout=8 truenas "cat '$remote_path'" > "$dest" 2>/dev/null; then
        error "Failed to collect $(basename "$dest")"
        exit 1
    fi
}

TOOL_DIR="/mnt/Media/data/tools/jellyfin-integrity"

fetch "$TOOL_DIR/config.json" "$BACKUP_DIR/config.json"
fetch "$TOOL_DIR/reference/plex-movie-collections.json" "$BACKUP_DIR/plex-movie-collections.json"
fetch "$TOOL_DIR/reference/plex-to-jellyfin-movie-map.json" "$BACKUP_DIR/plex-to-jellyfin-movie-map.json"

chmod 600 "$BACKUP_DIR"/*

success "Jellyfin integrity tool configuration saved"
echo
show_file_details "$BACKUP_DIR"
footer "Jellyfin integrity backup completed successfully"
