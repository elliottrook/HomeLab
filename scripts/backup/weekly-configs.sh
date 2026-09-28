#!/bin/bash
# Attempt every bounded exporter; report failure after all have had a chance.
set -u
repo="${HOMELAB_REPO:-$HOME/lab/homelab}"
failed=0
for name in opnsense arista proxmox nut observability video-archiver jellyfin-integrity; do
    "$repo/scripts/backup/$name.sh" || failed=1
done
python3 "$repo/scripts/backup/operator-configs.py" || failed=1
exit "$failed"
