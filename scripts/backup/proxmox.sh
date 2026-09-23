#!/bin/bash

set -euo pipefail

REPO="${HOMELAB_REPO:-$HOME/lab/homelab}"
source "$REPO/scripts/lib/output.sh"

PRIVATE_BACKUPS="${HOMELAB_BACKUP_ROOT:-$HOME/lab/private-backups}"

BACKUP_ROOT="$PRIVATE_BACKUPS/proxmox"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
ARCHIVE="$BACKUP_DIR/proxmox-host-config.tar.gz"

mkdir -p "$BACKUP_DIR"
chmod 700 "$PRIVATE_BACKUPS" "$BACKUP_ROOT" "$BACKUP_DIR"

header "Proxmox Host Configuration Backup"

info "Collecting Proxmox host configuration..."

if ! ssh proxmox \
    'set -- /etc/pve /etc/network/interfaces /etc/hosts /etc/hostname /etc/resolv.conf
     for path in /usr/local/sbin/aster-lab-guest /usr/local/sbin/aster-lab-guest-ssh /etc/sudoers.d/aster-lab-backup /var/lib/aster-lab-guest /var/lib/ai-lab-backup/.ssh/authorized_keys; do
         if [ -e "$path" ]; then set -- "$@" "$path"; fi
     done
     tar -czf - "$@" 2>/dev/null' > "$ARCHIVE"; then
    error "Proxmox configuration backup failed"
    exit 1
fi

chmod 600 "$ARCHIVE"

info "Collecting inventory information..."

ssh proxmox 'pveversion -v' > "$BACKUP_DIR/pve-version.txt"
ssh proxmox 'pct list' > "$BACKUP_DIR/lxc-list.txt"
ssh proxmox 'qm list' > "$BACKUP_DIR/vm-list.txt"
ssh proxmox 'pvesm status' > "$BACKUP_DIR/storage-status.txt"
ssh proxmox 'lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL' \
    > "$BACKUP_DIR/block-devices.txt"
ssh proxmox 'ip -brief address' > "$BACKUP_DIR/network-addresses.txt"

shasum -a 256 "$ARCHIVE" > "$ARCHIVE.sha256"
chmod 600 "$ARCHIVE.sha256"

success "Proxmox host configuration saved"

echo
show_file_details "$ARCHIVE"

footer "Proxmox backup completed successfully"
