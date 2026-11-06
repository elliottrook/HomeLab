#!/usr/bin/env bash
# Read-only aggregate audit, installed separately from the disabled old jobs.
set -euo pipefail
umask 077

audit_root=/mnt/Media/data/tools/media-retention-audit
environment_file=/mnt/Media/data/tools/video-archiver/.env
status_file="$audit_root/status.json"
temporary_file="$audit_root/status.json.tmp"

if [[ ! -r "$environment_file" ]]; then
    echo 'Retention audit environment unavailable' >&2
    exit 1
fi
source "$environment_file"
unset RADARR_API_KEY SONARR_API_KEY
if [[ -z "${JELLYFIN_API_KEY:-}" ]]; then
    echo 'Retention audit Jellyfin key unavailable' >&2
    exit 1
fi
export JELLYFIN_API_KEY

cd "$audit_root"
exec 9> "$audit_root/audit.lock"
flock -n 9 || { echo 'Retention audit already running' >&2; exit 1; }
trap 'rm -f "$temporary_file"' EXIT
PYTHONPATH="$audit_root" python3 -m video_archiver.retention_audit \
    --discover-docker \
    --data-root /mnt/Media/data \
    --jellyfin-url http://127.0.0.1:8096 > "$temporary_file"
mv "$temporary_file" "$status_file"
