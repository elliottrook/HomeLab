#!/bin/sh
set -eu

[ "${1:-}" = "--approved-m2-window" ] || {
  echo "explicit M2 deployment window required" >&2
  exit 2
}
source_dir=${2:-/tmp/homelab-broker-source}
credential=/etc/homelab-broker/openbao-project-write-approle.json

test -s "$credential" || {
  echo "project-write OpenBao AppRole credential is not installed" >&2
  exit 1
}
test -s /etc/homelab-bundle-runner/base_revision || exit 1
test -s /etc/homelab-bundle-runner/policy_digest || exit 1
test -s /etc/homelab-bundle-runner/allowed_signers || exit 1
mkdir -p /var/lib/homelab-bundle-runner/handoff

getent group hlabroker-project-write >/dev/null || groupadd --system hlabroker-project-write
id hlabroker-project-write >/dev/null 2>&1 || \
  useradd --system --gid hlabroker-project-write --home-dir /nonexistent --shell /usr/sbin/nologin hlabroker-project-write
usermod -a -G hlabroker hlabroker-project-write
usermod -a -G hlabundle hlabroker-project-write
usermod -a -G hlabroker-project-write hlabundle
chown hlabundle:hlabroker-project-write /var/lib/homelab-bundle-runner
chmod 0710 /var/lib/homelab-bundle-runner
chown hlabundle:hlabroker-project-write /var/lib/homelab-bundle-runner/handoff
chmod 2770 /var/lib/homelab-bundle-runner/handoff
chown root:hlabroker-project-write "$credential"
chmod 0640 "$credential"

install -o root -g root -m 0644 "$source_dir/broker_service.py" /opt/homelab-broker/broker_service.py
install -o root -g root -m 0644 "$source_dir/forgejo_mcp_gateway.py" /opt/homelab-broker/forgejo_mcp_gateway.py
install -o root -g root -m 0644 "$source_dir/mcp_policy_adapter.py" /opt/homelab-broker/mcp_policy_adapter.py
install -o root -g root -m 0644 "$source_dir/bundle_verifier.py" /opt/homelab-broker/bundle_verifier.py
install -o root -g root -m 0644 "$source_dir/project_document_bundle_verifier.py" /opt/homelab-broker/project_document_bundle_verifier.py
install -o root -g root -m 0644 "$source_dir/project_document_bundle_runner.py" /opt/homelab-broker/project_document_bundle_runner.py
install -o root -g root -m 0700 "$source_dir/broker_admin.py" /opt/homelab-broker/broker_admin.py
install -o root -g root -m 0644 "$source_dir/homelab-broker.service" /etc/systemd/system/homelab-broker.service
install -o root -g root -m 0644 "$source_dir/forgejo-mcp-project-write-gateway.service" /etc/systemd/system/forgejo-mcp-project-write-gateway.service

systemctl daemon-reload
systemctl enable --now forgejo-mcp-project-write-gateway.service
systemctl restart forgejo-mcp-project-write-gateway.service
systemctl restart homelab-broker.service
