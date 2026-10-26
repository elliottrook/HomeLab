#!/bin/sh
set -eu

stage=/root/aster-fixed-doctor-broker-stage-20261025T1825PDT
checkpoint=/root/aster-fixed-doctor-broker-pre-20261025T1825PDT
admin=/opt/homelab-broker/broker_admin.py
service=/opt/homelab-broker/broker_service.py
database=/var/lib/homelab-broker/broker.db
expected_admin=00216b27e179d936e1b5fd9feb1ca17dc25bb6af3e34b044408ae21133924e8b
expected_service=05a555241b97ad7e6a9d268ad91426af0432fb0ae0785dabf46bf4081e713ccb
candidate_admin=e90acd24acfa13f959070f2c791d29ea28ebf1d4240edd5a9b39b54dfc7ef4aa
candidate_service=c6217f4988510b4d38581829b4f6b333487b1cd35732a6ba5b3d82dcc69b627e
expected_core=2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99
rollback_needed=0

sha() { sha256sum "$1" | cut -d ' ' -f 1; }

broker_health() {
    runuser -u hlabagent -- python3 -c 'import json,socket; s=socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect("/run/homelab-broker/mcp.sock"); s.sendall(b"{\"method\":\"health\"}\n"); r=json.loads(s.makefile("rb").readline()); assert r.get("ok") is True and r.get("result",{}).get("status")=="ok"'
}

wait_for_broker() {
    attempt=0
    while [ "$attempt" -lt 20 ]; do
        if systemctl is-active --quiet homelab-broker.service && broker_health >/dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 0.5
    done
    return 1
}

rollback() {
    rc=$?
    trap - EXIT
    if [ "$rc" -ne 0 ] && [ "$rollback_needed" -eq 1 ]; then
        install -o root -g root -m 0700 "$checkpoint/broker_admin.py" "$admin"
        install -o root -g root -m 0644 "$checkpoint/broker_service.py" "$service"
        install -o hlabroker -g hlabroker -m 0600 "$checkpoint/broker.db" "$database"
        systemctl reset-failed homelab-broker.service || true
        if systemctl restart homelab-broker.service && wait_for_broker; then
            echo "ROLLBACK_APPLIED_AND_HEALTHY checkpoint=$checkpoint" >&2
        else
            echo "ROLLBACK_APPLIED_HEALTH_UNCONFIRMED checkpoint=$checkpoint" >&2
        fi
    fi
    exit "$rc"
}
trap rollback EXIT

[ "$(sha "$admin")" = "$expected_admin" ]
[ "$(sha "$service")" = "$expected_service" ]
[ "$(sha /opt/homelab-broker/broker_core.py)" = "$expected_core" ]
[ "$(stat -c '%U:%G:%a' "$database")" = "hlabroker:hlabroker:600" ]
[ "$(stat -c '%U:%G:%a' /run/homelab-broker/mcp.sock)" = "hlabroker:hlabroker-clients:660" ]
getent group hlabroker-clients | grep -Fq 'hlabagent'
broker_health
[ "$(sha "$stage/broker_admin.py")" = "$candidate_admin" ]
[ "$(sha "$stage/broker_service.py")" = "$candidate_service" ]
[ ! -e "$checkpoint" ]
install -d -o root -g root -m 0700 "$checkpoint"
cp -a "$admin" "$checkpoint/broker_admin.py"
cp -a "$service" "$checkpoint/broker_service.py"
python3 - "$database" "$checkpoint/broker.db" <<'PY'
import sqlite3
import sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
with target:
    source.backup(target)
target.close()
source.close()
PY
chown root:root "$checkpoint/broker.db"
chmod 0600 "$checkpoint/broker.db"
sha256sum "$checkpoint/broker_admin.py" "$checkpoint/broker_service.py" "$checkpoint/broker.db" > "$checkpoint/SHA256SUMS"
chmod 0600 "$checkpoint/SHA256SUMS"

PYTHONPYCACHEPREFIX="$stage/pycache" python3 -m py_compile "$stage/broker_admin.py" "$stage/broker_service.py"
PYTHONPATH=/opt/homelab-broker python3 -c 'import broker_core'

rollback_needed=1
install -o root -g root -m 0700 "$stage/broker_admin.py" "$admin.new"
install -o root -g root -m 0644 "$stage/broker_service.py" "$service.new"
[ "$(sha "$admin.new")" = "$candidate_admin" ]
[ "$(sha "$service.new")" = "$candidate_service" ]
mv -f "$admin.new" "$admin"
mv -f "$service.new" "$service"
systemctl restart homelab-broker.service

wait_for_broker
broker_health
[ "$(systemctl show homelab-broker.service -p NRestarts --value)" = 0 ]
[ "$(sha "$admin")" = "$candidate_admin" ]
[ "$(sha "$service")" = "$candidate_service" ]
[ "$(sha /opt/homelab-broker/broker_core.py)" = "$expected_core" ]

broker_health
echo 'BROKER_HEALTH_OK'

python3 - "$database" <<'PY'
import sqlite3
import sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
checks = [
    ("agents", "agent_id", "agent-aster-fixed-doctor"),
    ("services", "service_id", "aster-fixed-doctor"),
    ("capabilities", "capability", "diagnostic.aster-inference.latest"),
    ("agent_capabilities", "agent_id", "agent-aster-fixed-doctor"),
    ("requests", "capability", "diagnostic.aster-inference.latest"),
]
counts = [c.execute(f"select count(*) from {t} where {column}=?", (value,)).fetchone()[0]
          for t, column, value in checks]
assert counts == [0, 0, 0, 0, 0], counts
route = c.execute(
    "select service_id,risk_class,probation_allowed,enabled from capabilities where capability=?",
    ("forgejo.write.project-documents",),
).fetchone()
assert route == ("forgejo-mcp-project-write", "yellow", 0, 1), route
print("DATABASE_BOUNDARY_OK fixed_counts=0,0,0,0,0 project_route=preserved")
PY

grep -Fq 'enable-forgejo-project-documents' "$admin"
grep -Fq 'enable-fixed-doctor' "$admin"
grep -Fq 'forgejo.write.project-documents' "$service"
grep -Fq 'create_file_batch' "$service"
grep -Fq 'forgejo_project_write_socket' "$service"
grep -Fq 'diagnostic.aster-inference.latest' "$service"
grep -Fq 'fixed_doctor_socket' "$service"
systemctl is-active --quiet aster-agent.service
systemctl is-active --quiet aster-fixed-doctor-caller.service && exit 1 || true
systemctl is-active --quiet aster-fixed-doctor-gateway.service && exit 1 || true
systemctl is-enabled --quiet aster-fixed-doctor-caller.service && exit 1 || true
systemctl is-enabled --quiet aster-fixed-doctor-gateway.service && exit 1 || true
[ ! -e /run/aster-fixed-doctor/gateway.sock ]
[ ! -e /run/aster-fixed-doctor-caller/caller.sock ]

rollback_needed=0
echo "BROKER_RECONCILIATION_PASS checkpoint=$checkpoint"
