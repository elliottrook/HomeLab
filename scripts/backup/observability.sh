#!/bin/bash

set -euo pipefail

REPO="$HOME/lab/homelab"
source "$REPO/scripts/lib/output.sh"

BACKUP_ROOT="$HOME/lab/private-backups/observability"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
ARCHIVE="$BACKUP_DIR/observability-config.tar.gz"

mkdir -p "$BACKUP_DIR"
chmod 700 "$HOME/lab/private-backups" "$BACKUP_ROOT" "$BACKUP_DIR"

header "Prometheus and Grafana Configuration Backup"

info "Collecting protected configuration from LXC 109..."

if ! ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.20.31 \
    'tar -czf - \
        /etc/prometheus \
        /etc/grafana \
        /etc/systemd/system/prometheus.service \
        /etc/systemd/system/pve-exporter.service \
        /etc/systemd/system/nut-exporter.service \
        /etc/systemd/system/graphite-exporter.service \
        /etc/systemd/system/truenas-graphite-ingress.service \
        /etc/systemd/system/grafana-server.service.d \
        /var/lib/grafana/grafana.db \
        /var/lib/grafana/dashboards \
        /root/.grafana-initial-admin-password \
        2>/dev/null' > "$ARCHIVE"; then
    error "Observability configuration backup failed"
    exit 1
fi

chmod 600 "$ARCHIVE"

info "Validating archive structure and checksum..."

required_entries=(
    etc/prometheus/prometheus.yml
    etc/grafana/grafana.ini
    etc/grafana/provisioning/datasources/prometheus.yaml
    var/lib/grafana/grafana.db
    var/lib/grafana/dashboards/homelab-overview.json
    root/.grafana-initial-admin-password
)

archive_listing="$(tar -tzf "$ARCHIVE")"
for entry in "${required_entries[@]}"; do
    if ! grep -qx "$entry" <<< "$archive_listing"; then
        error "Observability archive is missing $entry"
        exit 1
    fi
done

shasum -a 256 "$ARCHIVE" > "$ARCHIVE.sha256"
chmod 600 "$ARCHIVE.sha256"

success "Observability configuration saved and validated"
echo
show_file_details "$ARCHIVE"
footer "Observability backup completed successfully"
