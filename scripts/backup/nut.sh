#!/bin/bash

set -euo pipefail

REPO="$HOME/lab/homelab"
source "$REPO/scripts/lib/output.sh"

BACKUP_ROOT="$HOME/lab/private-backups/nut"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"
chmod 700 "$HOME/lab/private-backups" "$BACKUP_ROOT" "$BACKUP_DIR"

header "NUT / UPS Server Configuration Backup"

info "Collecting NUT configuration from the Lenovo utility host..."

fetch() {
    local remote_cmd="$1"
    local dest="$2"

    if ! ssh -o BatchMode=yes -o ConnectTimeout=8 nut "$remote_cmd" > "$dest" 2>/dev/null; then
        error "Failed to collect $(basename "$dest")"
        exit 1
    fi
}

fetch "sudo -n cat /etc/nut/ups.conf" "$BACKUP_DIR/ups.conf"
fetch "sudo -n cat /etc/nut/nut.conf" "$BACKUP_DIR/nut.conf"
fetch "sudo -n cat /etc/nut/upsd.users" "$BACKUP_DIR/upsd.users"
fetch "sudo -n cat /etc/nut/upsmon.conf" "$BACKUP_DIR/upsmon.conf"
fetch "cat /etc/ssh/sshd_config.d/hardening.conf" "$BACKUP_DIR/sshd-hardening.conf"
fetch "cat /etc/network/interfaces" "$BACKUP_DIR/network-interfaces.txt"
fetch "hostnamectl" "$BACKUP_DIR/hostnamectl.txt"

chmod 600 "$BACKUP_DIR"/*

success "NUT configuration saved"
echo
show_file_details "$BACKUP_DIR"
footer "NUT backup completed successfully"
