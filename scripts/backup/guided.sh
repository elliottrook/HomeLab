#!/bin/bash

set -euo pipefail

REPO="$HOME/lab/homelab"
source "$REPO/scripts/lib/output.sh"

GUIDED_DIR="$HOME/lab/private-backups/guided-exports"

mkdir -p "$GUIDED_DIR"/{unifi,truenas,synology-main,synology-backup}
chmod -R 700 "$GUIDED_DIR"

header "Guided Configuration Exports"

warning "The following platforms use vendor-supported web exports."
echo

info "UniFi"
echo "  Open: http://192.168.50.21:11443"
echo "  Settings → Control Plane → Backups"
echo "  Download the .unf file into:"
echo "  $GUIDED_DIR/unifi"
echo

info "TrueNAS"
echo "  Open: http://192.168.20.40"
echo "  System Settings → General → Manage Configuration"
echo "  Download the configuration into:"
echo "  $GUIDED_DIR/truenas"
echo

info "Synology DS920+"
echo "  Open: http://192.168.20.41:5000"
echo "  Control Panel → Update & Restore → Configuration Backup"
echo "  Export the .dss file into:"
echo "  $GUIDED_DIR/synology-main"
echo

info "Backup Synology"
echo "  Open: http://192.168.20.42:5000"
echo "  Control Panel → Update & Restore → Configuration Backup"
echo "  Export the .dss file into:"
echo "  $GUIDED_DIR/synology-backup"
echo

open "http://192.168.50.21:11443"
open "http://192.168.20.40"
open "http://192.168.20.41:5000"
open "http://192.168.20.42:5000"

footer "Guided backup pages opened"
