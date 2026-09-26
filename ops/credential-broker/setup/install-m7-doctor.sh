#!/bin/sh
set -eu

source_dir=${1:-/tmp/homelab-m7-source}
checkpoint=/var/lib/homelab-broker/m7-doctor-rollback-$(date +%Y%m%d-%H%M%S)
owner_source=/etc/aster/lab-operations.env

for file in \
  "$source_dir/broker_service.py" \
  "$source_dir/broker_admin.py" \
  "$source_dir/homelab-broker.service" \
  "$source_dir/lab_operations.py" \
  "$source_dir/lab_operations_broker_gateway.py" \
  "$source_dir/aster-lab-operations-broker.service"
do
  test -s "$file" || { echo "missing deployment artifact: $file" >&2; exit 1; }
done
test -r "$owner_source" || { echo "Lab Operations environment is unavailable" >&2; exit 1; }

owner=$(sed -n 's/^ASTER_LAB_OWNER=//p' "$owner_source")
case "$owner" in
  *[!a-f0-9]*|'') echo "Lab Operations owner is not a source-local SHA-256 hash" >&2; exit 1 ;;
esac
test "${#owner}" -eq 64 || { echo "Lab Operations owner hash has the wrong length" >&2; exit 1; }

python3 - <<'PY'
import sqlite3
for path in ('/var/lib/aster/lab-operations/jobs.sqlite3','/var/lib/homelab-broker/broker.db'):
    db=sqlite3.connect('file:'+path+'?mode=ro',uri=True)
    try:
        if path.endswith('jobs.sqlite3'):
            active=db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running','unknown')").fetchone()[0]
            if active: raise SystemExit('active or uncertain Lab Operations work blocks M7 deployment')
        else:
            agent=db.execute("SELECT state FROM agents WHERE agent_id='agent-hermes'").fetchone()
            if agent != ('operator',): raise SystemExit('agent-hermes must be operator before M7 deployment')
    finally: db.close()
PY

install -d -o root -g root -m 0700 "$checkpoint"
for file in \
  /opt/homelab-broker/broker_service.py \
  /opt/homelab-broker/broker_admin.py \
  /etc/systemd/system/homelab-broker.service \
  /opt/aster-agent/lab_operations.py
do
  cp -a "$file" "$checkpoint/"
done
CHECKPOINT="$checkpoint/broker.db" python3 - <<'PY'
import os, sqlite3
source=sqlite3.connect('file:/var/lib/homelab-broker/broker.db?mode=ro',uri=True)
target=sqlite3.connect(os.environ['CHECKPOINT'])
try: source.backup(target)
finally:
    target.close()
    source.close()
PY
chmod 0600 "$checkpoint/broker.db"

getent group aster-lab-broker >/dev/null || groupadd --system aster-lab-broker
install -o root -g root -m 0644 "$source_dir/broker_service.py" /opt/homelab-broker/broker_service.py
install -o root -g root -m 0700 "$source_dir/broker_admin.py" /opt/homelab-broker/broker_admin.py
install -o root -g root -m 0644 "$source_dir/homelab-broker.service" /etc/systemd/system/homelab-broker.service
install -o root -g root -m 0644 "$source_dir/lab_operations.py" /opt/aster-agent/lab_operations.py
install -o root -g root -m 0644 "$source_dir/lab_operations_broker_gateway.py" /opt/aster-agent/lab_operations_broker_gateway.py
install -o root -g root -m 0644 "$source_dir/aster-lab-operations-broker.service" /etc/systemd/system/aster-lab-operations-broker.service
printf 'ASTER_LAB_OWNER=%s\n' "$owner" | install -o root -g root -m 0600 /dev/stdin /etc/aster/lab-operations-broker.env

/usr/bin/python3 /opt/homelab-broker/broker_admin.py \
  --database /var/lib/homelab-broker/broker.db enable-lab-doctor
chown hlabroker:hlabroker /var/lib/homelab-broker/broker.db
chmod 0600 /var/lib/homelab-broker/broker.db

systemctl daemon-reload
systemctl enable --now aster-lab-operations-broker.service
systemctl restart homelab-broker.service
systemctl is-active --quiet aster-lab-operations-broker.service homelab-broker.service
test -S /run/aster-lab-operations-broker/gateway.sock
echo "M7_DOCTOR_INSTALLED checkpoint=$checkpoint"
