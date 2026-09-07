#!/bin/bash
# Runs jellyfin-ffmpeg's ffmpeg via the already-running jellyfin container (dynamically
# linked, so it can't just be copied onto the bare host) instead of downloading a fresh
# static build. Translates host paths under /mnt/Media/data to the container's /media
# mount point (jellyfin's own bind mount) before exec'ing.
set -euo pipefail
HOST_PREFIX="/mnt/Media/data"
CONTAINER_PREFIX="/media"
args=()
for a in "$@"; do
  if [[ "$a" == "$HOST_PREFIX"* ]]; then
    a="${CONTAINER_PREFIX}${a#$HOST_PREFIX}"
  fi
  args+=("$a")
done
exec docker exec jellyfin /usr/lib/jellyfin-ffmpeg/ffmpeg "${args[@]}"
