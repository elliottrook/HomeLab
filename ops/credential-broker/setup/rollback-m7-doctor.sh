#!/bin/sh
set -eu

checkpoint=${1:?usage: rollback-m7-doctor.sh /var/lib/homelab-broker/m7-doctor-rollback-TIMESTAMP}
case "$checkpoint" in
  /var/lib/homelab-broker/m7-doctor-rollback-*) ;;
  *) echo "refusing unexpected checkpoint path" >&2; exit 1 ;;
esac
test -d "$checkpoint" || { echo "checkpoint does not exist" >&2; exit 1; }
for file in broker_service.py broker_admin.py homelab-broker.service lab_operations.py broker.db; do
  test -s "$checkpoint/$file" || { echo "checkpoint is incomplete: $file" >&2; exit 1; }
done

systemctl stop homelab-broker.service aster-lab-operations-broker.service || true
install -o root -g root -m 0644 "$checkpoint/broker_service.py" /opt/homelab-broker/broker_service.py
install -o root -g root -m 0700 "$checkpoint/broker_admin.py" /opt/homelab-broker/broker_admin.py
install -o root -g root -m 0644 "$checkpoint/homelab-broker.service" /etc/systemd/system/homelab-broker.service
install -o root -g root -m 0644 "$checkpoint/lab_operations.py" /opt/aster-agent/lab_operations.py
install -o hlabroker -g hlabroker -m 0600 "$checkpoint/broker.db" /var/lib/homelab-broker/broker.db
rm -f /opt/aster-agent/lab_operations_broker_gateway.py \
  /etc/systemd/system/aster-lab-operations-broker.service \
  /etc/aster/lab-operations-broker.env
systemctl disable aster-lab-operations-broker.service >/dev/null 2>&1 || true
systemctl daemon-reload
systemctl start homelab-broker.service
systemctl is-active --quiet homelab-broker.service
echo "M7_DOCTOR_ROLLED_BACK checkpoint=$checkpoint"
