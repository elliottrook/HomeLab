#!/bin/sh
set -eu

source_dir=${1:-/tmp/homelab-broker-source}
credential=/etc/homelab-broker/openbao-write-approle.json

test -s "$credential" || {
  echo "safe-write OpenBao AppRole credential is not installed" >&2
  exit 1
}

getent group hlabroker-write >/dev/null || groupadd --system hlabroker-write
id hlabroker-write >/dev/null 2>&1 || \
  useradd --system --gid hlabroker-write --home-dir /nonexistent --shell /usr/sbin/nologin hlabroker-write
usermod -a -G hlabroker hlabroker-write
chown root:hlabroker-write "$credential"
chmod 0640 "$credential"

install -o root -g root -m 0644 "$source_dir/broker_service.py" /opt/homelab-broker/broker_service.py
install -o root -g root -m 0644 "$source_dir/forgejo_mcp_gateway.py" /opt/homelab-broker/forgejo_mcp_gateway.py
install -o root -g root -m 0644 "$source_dir/mcp_policy_adapter.py" /opt/homelab-broker/mcp_policy_adapter.py
install -o root -g root -m 0700 "$source_dir/broker_admin.py" /opt/homelab-broker/broker_admin.py
install -o root -g root -m 0644 "$source_dir/homelab-broker.service" /etc/systemd/system/homelab-broker.service
install -o root -g root -m 0644 "$source_dir/forgejo-mcp-write-gateway.service" /etc/systemd/system/forgejo-mcp-write-gateway.service

/usr/bin/python3 /opt/homelab-broker/broker_admin.py \
  --database /var/lib/homelab-broker/broker.db enable-forgejo-safe-write

systemctl daemon-reload
systemctl enable --now forgejo-mcp-write-gateway.service
systemctl restart homelab-broker.service
