#!/bin/sh
# Recovery datasets verified and cut over on 2026-10-05.
# Preserves existing cloud keys and same-site-only guest exclusions.
set -eu
export RCLONE_CONFIG=/etc/rclone/rclone.conf
if [ "${1:-}" != "--locked" ]; then
    exec flock -n /run/idrive-relay-sync.lock "$0" --locked
fi
for area in guests family configuration; do
    mountpoint -q "/srv/recovery/$area" || exit 1
    test "$(cat "/srv/recovery/$area/.recovery-relay-source")" = "Recovery/$area" || exit 1
done
# Check every source before any cloud mutation. A missing mount/tree fails closed.
for rel in guests/homelab-proxmox-guests family/gowest configuration/exports configuration/mac configuration/home-assistant configuration/jellyfin configuration/paperless-service configuration/service-reconstruction; do
    test -d "/srv/recovery/$rel" || exit 1
    test -n "$(find "/srv/recovery/$rel" -type f -print -quit)" || exit 1
done
install -d -m 0700 /var/log/idrive-relay
sync_tree() {
    source_rel=$1
    cloud_rel=$2
    /usr/local/bin/rclone sync "/srv/recovery/$source_rel" "idrive-crypt:$cloud_rel" \
      --exclude '**/.candidate-*/**' \
      --exclude '**/configs.candidate.tar.gz' \
      --exclude '**/status.candidate.json' \
      --exclude '**/.previous-candidate' \
      --exclude '/vzdump-lxc-110-*.tar.zst' \
      --exclude '/vzdump-lxc-115-*.tar.zst' \
      --max-delete 100 --transfers 4 --checkers 8 --bwlimit 20M \
      --log-file /var/log/idrive-relay/sync.log --log-level INFO
}
sync_tree guests/homelab-proxmox-guests homelab-proxmox-guests
sync_tree family/gowest gowest
sync_tree configuration/exports configuration
sync_tree configuration/mac mac
sync_tree configuration/home-assistant home-assistant
sync_tree configuration/jellyfin jellyfin
sync_tree configuration/paperless-service paperless-service
sync_tree configuration/service-reconstruction service-reconstruction
