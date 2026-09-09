#!/bin/bash
# See ffmpeg-jellyfin-wrapper.sh — same rationale, for ffprobe.
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
exec docker exec jellyfin /usr/lib/jellyfin-ffmpeg/ffprobe "${args[@]}"
