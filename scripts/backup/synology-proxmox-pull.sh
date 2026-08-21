#!/bin/bash

set -u

output_dir="/volume1/Backup/HomeLab-Backups/automated"
destination="$output_dir/proxmox-guests"
log_dir="$output_dir/logs"
log_file="$log_dir/proxmox-pull-latest.log"
status_file="$output_dir/proxmox-pull-latest.status"
success_file="$output_dir/proxmox-pull-last-success.txt"
verify_log="/tmp/proxmox-pull-verify.$$"

key_file="/root/.ssh/homelab_proxmox_pull_ed25519"
known_hosts="/root/.ssh/homelab_proxmox_known_hosts"
remote="homelab-backup@192.168.50.10"

mac_key="/root/.ssh/homelab_mac_pull_ed25519"
mac_known_hosts="/root/.ssh/homelab_mac_known_hosts"
mac_host="jelliott@192.168.1.206"
alert_script="/Users/jelliott/lab/homelab/scripts/backup-alert"

mkdir -p "$destination" "$log_dir"
trap 'rm -f "$verify_log"' EXIT

exec > "$log_file" 2>&1

send_failure_alert() {
    message="$1"

    /usr/bin/ssh \
      -i "$mac_key" \
      -o UserKnownHostsFile="$mac_known_hosts" \
      -o StrictHostKeyChecking=yes \
      -o BatchMode=yes \
      -o IdentitiesOnly=yes \
      "$mac_host" \
      "$alert_script \"Mini Atlas Proxmox backup failure\" \"$message\"" ||
      echo "WARNING: failure email could not be sent"
}

report_monitoring_status() {
    result="$1"

    /usr/bin/ssh \
      -i "$mac_key" \
      -o UserKnownHostsFile="$mac_known_hosts" \
      -o StrictHostKeyChecking=yes \
      -o BatchMode=yes \
      -o IdentitiesOnly=yes \
      "$mac_host" \
      "$alert_script report proxmox-pull $result" ||
      echo "WARNING: monitoring status could not be reported"
}

ssh_command="ssh -i $key_file -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$known_hosts"

echo "Proxmox backup pull started: $(date)"

if ! rsync -rlt \
  --partial \
  --itemize-changes \
  --delete-delay \
  --delete-excluded \
  --include='vzdump-lxc-100-*.tar.zst' \
  --include='vzdump-lxc-101-*.tar.zst' \
  --include='vzdump-qemu-102-*.vma.zst' \
  --include='vzdump-qemu-103-*.vma.zst' \
  --include='vzdump-lxc-104-*.tar.zst' \
  --include='vzdump-qemu-105-*.vma.zst' \
  --exclude='*' \
  -e "$ssh_command" \
  "$remote:/" \
  "$destination/"; then
    echo "ERROR: Proxmox archive copy failed"
    echo "1" > "$status_file"
    report_monitoring_status failure
    send_failure_alert \
      "The Backup Synology could not copy the retained Proxmox guest archives. Check proxmox-pull-latest.log."
    exit 1
fi

echo "Running checksum comparison..."

if ! rsync -rltc \
  --dry-run \
  --itemize-changes \
  --delete \
  --delete-excluded \
  --include='vzdump-lxc-100-*.tar.zst' \
  --include='vzdump-lxc-101-*.tar.zst' \
  --include='vzdump-qemu-102-*.vma.zst' \
  --include='vzdump-qemu-103-*.vma.zst' \
  --include='vzdump-lxc-104-*.tar.zst' \
  --include='vzdump-qemu-105-*.vma.zst' \
  --exclude='*' \
  -e "$ssh_command" \
  "$remote:/" \
  "$destination/" > "$verify_log" 2>&1; then
    cat "$verify_log"
    echo "ERROR: Proxmox checksum comparison failed"
    echo "1" > "$status_file"
    report_monitoring_status failure
    send_failure_alert \
      "The Proxmox guest archive checksum comparison failed. Check proxmox-pull-latest.log."
    exit 1
fi

cat "$verify_log"

if [ -s "$verify_log" ]; then
    echo "ERROR: Proxmox destination differences remain"
    echo "1" > "$status_file"
    report_monitoring_status failure
    send_failure_alert \
      "The Proxmox guest archive copy completed but verified differences remain. Check proxmox-pull-latest.log."
    exit 1
fi

date '+%Y-%m-%d %H:%M:%S %Z' > "$success_file"
echo "0" > "$status_file"
report_monitoring_status success
echo "Proxmox guest archive pull and checksum comparison completed successfully"
