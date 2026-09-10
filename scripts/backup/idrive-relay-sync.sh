#!/bin/sh

# Canonical relay command for LXC 112. LXC 110 model archives are deliberately
# kept out of the metered 1 TB off-site tier; their dedicated TrueNAS mirror is
# same-site recovery coverage only.

set -eu

log_dir=/var/log/idrive-relay
lock_file=/run/idrive-relay-sync.lock
export RCLONE_CONFIG=/etc/rclone/rclone.conf

install -d -m 0700 "$log_dir"

exec flock -n "$lock_file" /usr/local/bin/rclone sync \
  /srv/backup \
  idrive-crypt: \
  --exclude '/aster-lxc110/**' \
  --exclude '/homelab-proxmox-guests/vzdump-lxc-110-*.tar.zst' \
  --transfers 4 \
  --checkers 8 \
  --bwlimit 20M \
  --log-file "$log_dir/sync.log" \
  --log-level INFO
