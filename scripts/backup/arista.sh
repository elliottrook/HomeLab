#!/bin/bash

set -euo pipefail

REPO="$HOME/lab/homelab"
source "$REPO/scripts/lib/output.sh"

BACKUP_ROOT="$HOME/lab/private-backups/arista"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

header "Arista Configuration Backup"

backup_cmd() {
    local description="$1"
    local command="$2"
    local outfile="$3"

    info "$description..."
    ssh arista "$command" > "$BACKUP_DIR/$outfile"
    success "$outfile saved"
}

backup_cmd "Collecting running configuration"      "show running-config"        "running-config.txt"
backup_cmd "Collecting startup configuration"      "show startup-config"        "startup-config.txt"
backup_cmd "Collecting EOS version"                "show version"               "version.txt"
backup_cmd "Collecting hardware inventory"         "show inventory"             "inventory.txt"
backup_cmd "Collecting interface status"           "show interfaces status"     "interfaces-status.txt"
backup_cmd "Collecting VLAN configuration"         "show vlan"                  "vlan.txt"
backup_cmd "Collecting environment status"         "show environment all"       "environment.txt"

footer "Arista backup completed successfully"
