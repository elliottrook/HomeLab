#!/bin/sh
set -eu

source_dir=${1:-/tmp/homelab-broker-source}

getent group hlabroker-clients >/dev/null || groupadd --system hlabroker-clients
getent group hlabroker-approvers >/dev/null || groupadd --system hlabroker-approvers
id hlabroker >/dev/null 2>&1 || useradd --system --home-dir /var/lib/homelab-broker --shell /usr/sbin/nologin hlabroker
id hlabagent >/dev/null 2>&1 || useradd --system --home-dir /var/lib/hlabagent --create-home --shell /usr/sbin/nologin hlabagent
usermod -a -G hlabroker-clients hlabroker
usermod -a -G hlabroker-clients hlabagent
id aster >/dev/null 2>&1 || { echo "aster service user is required for M3 approval" >&2; exit 1; }
usermod -a -G hlabroker-approvers hlabroker
usermod -a -G hlabroker-approvers aster

install -d -o root -g root -m 0755 /opt/homelab-broker
install -o root -g root -m 0644 "$source_dir/broker_core.py" /opt/homelab-broker/broker_core.py
install -o root -g root -m 0644 "$source_dir/broker_service.py" /opt/homelab-broker/broker_service.py
install -o root -g root -m 0644 "$source_dir/broker_approval_service.py" /opt/homelab-broker/broker_approval_service.py
install -o root -g root -m 0700 "$source_dir/broker_admin.py" /opt/homelab-broker/broker_admin.py
install -o root -g root -m 0755 "$source_dir/broker_client.py" /usr/local/bin/homelab-broker-client
install -o root -g root -m 0644 "$source_dir/homelab-broker.service" /etc/systemd/system/homelab-broker.service
install -o root -g root -m 0644 "$source_dir/homelab-broker-approval.service" /etc/systemd/system/homelab-broker-approval.service
install -d -o hlabroker -g hlabroker -m 0700 /var/lib/homelab-broker

agent_uid=$(id -u hlabagent)
if [ ! -e /var/lib/homelab-broker/broker.db ]; then
  /usr/bin/python3 /opt/homelab-broker/broker_admin.py \
    --database /var/lib/homelab-broker/broker.db initialize-synthetic --agent-uid "$agent_uid"
  chown hlabroker:hlabroker /var/lib/homelab-broker/broker.db
  chmod 0600 /var/lib/homelab-broker/broker.db
fi

systemctl daemon-reload
systemctl enable --now homelab-broker.service
systemctl enable --now homelab-broker-approval.service
