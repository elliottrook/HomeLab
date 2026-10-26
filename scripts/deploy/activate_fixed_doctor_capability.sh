#!/bin/sh
set -eu

checkpoint=/root/aster-fixed-doctor-activation-pre-20261025T1845PDT
database=/var/lib/homelab-broker/broker.db
admin=/opt/homelab-broker/broker_admin.py
service=/opt/homelab-broker/broker_service.py
core=/opt/homelab-broker/broker_core.py
doctor_adapter=/opt/aster-agent/doctor_incident_adapter.py
investigation=/opt/aster-agent/sysadmin_investigation.py
caller=aster-fixed-doctor-caller.service
gateway=aster-fixed-doctor-gateway.service
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
        systemctl disable --now "$caller" "$gateway" >/dev/null 2>&1 || true
        rm -f /run/aster-fixed-doctor-caller/caller.sock /run/aster-fixed-doctor/gateway.sock
        systemctl stop homelab-broker.service || true
        install -o hlabroker -g hlabroker -m 0600 "$checkpoint/broker.db" "$database"
        systemctl reset-failed homelab-broker.service || true
        if systemctl start homelab-broker.service && wait_for_broker; then
            echo "ACTIVATION_ROLLBACK_APPLIED_AND_HEALTHY checkpoint=$checkpoint" >&2
        else
            echo "ACTIVATION_ROLLBACK_APPLIED_HEALTH_UNCONFIRMED checkpoint=$checkpoint" >&2
        fi
    fi
    exit "$rc"
}
trap rollback EXIT

[ "$(sha "$admin")" = e90acd24acfa13f959070f2c791d29ea28ebf1d4240edd5a9b39b54dfc7ef4aa ]
[ "$(sha "$service")" = c6217f4988510b4d38581829b4f6b333487b1cd35732a6ba5b3d82dcc69b627e ]
[ "$(sha "$core")" = 2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99 ]
[ "$(sha "$doctor_adapter")" = c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db ]
[ "$(sha "$investigation")" = bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe ]
[ "$(sha /opt/aster-agent/fixed_doctor_caller.py)" = aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a ]
[ "$(sha /opt/aster-agent/fixed_doctor_gateway.py)" = 852e609ef278acee1b4343ea8627d2c01f8f1a2cc42556aeb9acfa184b4bd495 ]
[ "$(sha /opt/aster-agent/fixed_doctor_capability.py)" = 7c0fd1bcc3404661052627ec7d2fa04e811149f43fb3ea23bc27edf57bb5fb3b ]
[ "$(sha /etc/systemd/system/aster-fixed-doctor-caller.service)" = 9a4aa0336df27de60483e567cef43360277d0ec4ebbee2fbcb4093e644b055bf ]
[ "$(sha /etc/systemd/system/aster-fixed-doctor-gateway.service)" = 44ee0df1c163bc453148032f7187c56e38a532377efc5084dadb40d461b629ef ]
[ "$(stat -c '%U:%G:%a' "$database")" = hlabroker:hlabroker:600 ]
[ "$(id -u aster-doctor-caller)" = 978 ]
id -nG aster | tr ' ' '\n' | grep -Fxq aster-doctor-client
systemctl is-active --quiet homelab-broker.service
systemctl is-active --quiet aster-agent.service
broker_health
systemctl is-active --quiet "$caller" && exit 1 || true
systemctl is-active --quiet "$gateway" && exit 1 || true
systemctl is-enabled --quiet "$caller" && exit 1 || true
systemctl is-enabled --quiet "$gateway" && exit 1 || true
[ ! -e /run/aster-fixed-doctor-caller/caller.sock ]
[ ! -e /run/aster-fixed-doctor/gateway.sock ]
[ ! -e "$checkpoint" ]

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
assert [c.execute(f"select count(*) from {t} where {col}=?", (value,)).fetchone()[0]
        for t, col, value in checks] == [0, 0, 0, 0, 0]
assert c.execute("pragma integrity_check").fetchone()[0] == "ok"
PY

install -d -o root -g root -m 0700 "$checkpoint"
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
sha256sum "$checkpoint/broker.db" > "$checkpoint/SHA256SUMS"
chmod 0600 "$checkpoint/SHA256SUMS"

rollback_needed=1
python3 "$admin" --database "$database" enable-fixed-doctor --agent-uid 978

python3 - "$database" <<'PY'
import sqlite3
import sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
assert c.execute("select unix_uid,state from agents where agent_id=?", ("agent-aster-fixed-doctor",)).fetchone() == (978, "observer")
assert c.execute("select execution_mode,enabled,credential_type,custody_identifier,credential_scope,health from services where service_id=?", ("aster-fixed-doctor",)).fetchone() == ("proxy", 1, "none", "none", "fixed aster.agent_inference read only", "candidate")
assert c.execute("select service_id,risk_class,probation_allowed,enabled from capabilities where capability=?", ("diagnostic.aster-inference.latest",)).fetchone() == ("aster-fixed-doctor", "green", 0, 1)
assert c.execute("select capability from agent_capabilities where agent_id=?", ("agent-aster-fixed-doctor",)).fetchall() == [("diagnostic.aster-inference.latest",)]
assert c.execute("select count(*) from requests where capability=?", ("diagnostic.aster-inference.latest",)).fetchone()[0] == 0
PY

systemctl enable --now "$gateway"
attempt=0
while [ "$attempt" -lt 20 ]; do
    systemctl is-active --quiet "$gateway" && [ -S /run/aster-fixed-doctor/gateway.sock ] && break
    attempt=$((attempt + 1))
    sleep 0.25
done
systemctl is-active --quiet "$gateway"
[ -S /run/aster-fixed-doctor/gateway.sock ]
systemctl enable --now "$caller"
attempt=0
while [ "$attempt" -lt 20 ]; do
    systemctl is-active --quiet "$caller" && [ -S /run/aster-fixed-doctor-caller/caller.sock ] && break
    attempt=$((attempt + 1))
    sleep 0.25
done
systemctl is-active --quiet "$caller"
[ -S /run/aster-fixed-doctor-caller/caller.sock ]

runuser -u aster -- python3 - <<'PY'
import json
import socket
s = socket.socket(socket.AF_UNIX)
s.settimeout(10)
s.connect('/run/aster-fixed-doctor-caller/caller.sock')
s.sendall(b'{"method":"doctor.aster-inference.latest","arguments":{}}\n')
r = json.loads(s.makefile('rb').readline())
assert set(r) == {"ok", "result"} and r["ok"] is True
result = r["result"]
assert set(result) == {"schema", "capability", "observation"}
assert result["schema"] == 1 and result["capability"] == "diagnostic.aster-inference.latest"
observation = result["observation"]
assert set(observation) == {"source", "state", "observed_at", "age_seconds", "facts"}
assert observation["source"] == "homelab-doctor-structured/v2"
assert observation["state"] == "ok"
assert observation["facts"] == {"check_id": "aster.agent_inference"}
assert isinstance(observation["age_seconds"], int) and 0 <= observation["age_seconds"] <= 129600
print("FIXED_DOCTOR_READ_OK state=ok")
PY

python3 - "$database" <<'PY'
import sqlite3
import sys
c = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
assert c.execute("select count(*) from agents where agent_id=?", ("agent-aster-fixed-doctor",)).fetchone()[0] == 1
assert c.execute("select count(*) from services where service_id=? and enabled=1", ("aster-fixed-doctor",)).fetchone()[0] == 1
assert c.execute("select count(*) from capabilities where capability=? and risk_class='green' and enabled=1", ("diagnostic.aster-inference.latest",)).fetchone()[0] == 1
assert c.execute("select count(*) from agent_capabilities where agent_id=? and capability=?", ("agent-aster-fixed-doctor", "diagnostic.aster-inference.latest")).fetchone()[0] == 1
rows = c.execute("select status from requests where capability=? order by created_at", ("diagnostic.aster-inference.latest",)).fetchall()
assert rows == [("consumed",)], rows
assert c.execute("pragma integrity_check").fetchone()[0] == "ok"
print("FIXED_DOCTOR_AUTHORITY_OK grant=1 consumed_requests=1")
PY

systemctl is-enabled --quiet "$gateway"
systemctl is-enabled --quiet "$caller"
systemctl is-active --quiet "$gateway"
systemctl is-active --quiet "$caller"
[ "$(systemctl show "$gateway" -p NRestarts --value)" = 0 ]
[ "$(systemctl show "$caller" -p NRestarts --value)" = 0 ]
systemctl is-active --quiet homelab-broker.service
systemctl is-active --quiet aster-agent.service
broker_health

rollback_needed=0
echo "FIXED_DOCTOR_ACTIVATION_PASS checkpoint=$checkpoint"
