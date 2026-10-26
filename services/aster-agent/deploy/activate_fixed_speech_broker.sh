#!/bin/sh
set -eu
packet=/tmp/fixed-speech-broker-packet-20261026
checkpoint=/var/lib/homelab-broker/fixed-speech-pre-activation-20261026-r1
admin=/opt/homelab-broker/broker_admin.py
service=/opt/homelab-broker/broker_service.py
database=/var/lib/homelab-broker/broker.db
changed=0

rollback() {
  code=$?
  trap - EXIT INT TERM
  if [ "$changed" -eq 1 ]; then
    systemctl stop aster-fixed-speech-caller.service aster-fixed-speech-gateway.service || true
    systemctl stop homelab-broker.service || true
    install -o root -g root -m 0700 "$checkpoint/broker_admin.py" "$admin"
    install -o root -g root -m 0644 "$checkpoint/broker_service.py" "$service"
    rm -f "$database-wal" "$database-shm"
    install -o hlabroker -g hlabroker -m 0600 "$checkpoint/broker.db" "$database"
    systemctl start homelab-broker.service || true
  fi
  rm -rf "$packet"
  echo "FIXED_SPEECH_ACTIVATION_ROLLED_BACK phase_failure exit=$code" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(sha256sum "$admin" | cut -d' ' -f1)" = e90acd24acfa13f959070f2c791d29ea28ebf1d4240edd5a9b39b54dfc7ef4aa
test "$(sha256sum "$service" | cut -d' ' -f1)" = c6217f4988510b4d38581829b4f6b333487b1cd35732a6ba5b3d82dcc69b627e
test "$(sha256sum /opt/homelab-broker/broker_core.py | cut -d' ' -f1)" = 2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99
test "$(sha256sum /etc/systemd/system/homelab-broker.service | cut -d' ' -f1)" = 8a65bb18cba169df4ab9a0b72c0f5fa04cbd9b6ddc75ade66ca3bef4c80aa1f3
test "$(sha256sum "$packet/ops/credential-broker/broker_admin.py" | cut -d' ' -f1)" = c04add38be09c98ccecefd9d548e26222b08e642fa59a1e4ec2ec62d0ccbd765
test "$(sha256sum "$packet/ops/credential-broker/broker_service.py" | cut -d' ' -f1)" = b51df2bdffa3e0117c2cb986335b14ed2ef1d787790dea1f8834eb98fc10a5a3
test "$(systemctl is-active homelab-broker.service)" = active
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl is-enabled aster-fixed-speech-gateway.service 2>/dev/null || true)" = disabled
test "$(systemctl is-active aster-fixed-speech-gateway.service 2>/dev/null || true)" = inactive
test "$(systemctl is-enabled aster-fixed-speech-caller.service 2>/dev/null || true)" = disabled
test "$(systemctl is-active aster-fixed-speech-caller.service 2>/dev/null || true)" = inactive
test ! -S /run/aster-fixed-speech/gateway.sock
test ! -S /run/aster-fixed-speech-caller/caller.sock
test ! -e "$checkpoint"
test "$(stat -c '%U:%G %a' "$database")" = "hlabroker:hlabroker 600"

python3 - "$database" <<'PY'
import sqlite3, sys
c=sqlite3.connect(sys.argv[1])
assert c.execute("select count(*) from agents where agent_id='agent-aster-fixed-speech'").fetchone()[0] == 0
assert c.execute("select count(*) from services where service_id='aster-fixed-speech'").fetchone()[0] == 0
assert c.execute("select count(*) from capabilities where capability='diagnostic.aster-speech.latest'").fetchone()[0] == 0
assert c.execute("select count(*) from agent_capabilities where agent_id='agent-aster-fixed-speech'").fetchone()[0] == 0
assert c.execute("select enabled from services where service_id='aster-fixed-doctor'").fetchone() == (1,)
assert c.execute("select count(*) from agent_capabilities where agent_id='agent-aster-fixed-doctor' and capability='diagnostic.aster-inference.latest'").fetchone()[0] == 1
PY

install -d -o root -g root -m 0700 "$checkpoint"
cp -p "$admin" "$checkpoint/broker_admin.py"
cp -p "$service" "$checkpoint/broker_service.py"
python3 - "$database" "$checkpoint/broker.db" <<'PY'
import sqlite3, sys
source=sqlite3.connect(sys.argv[1])
target=sqlite3.connect(sys.argv[2])
source.backup(target)
target.close()
source.close()
PY
chown root:root "$checkpoint/broker.db"
chmod 0600 "$checkpoint/broker.db"
changed=1

install -o root -g root -m 0700 "$packet/ops/credential-broker/broker_admin.py" "$admin.new"
install -o root -g root -m 0644 "$packet/ops/credential-broker/broker_service.py" "$service.new"
mv "$admin.new" "$admin"
mv "$service.new" "$service"
PYTHONPATH=/opt/homelab-broker python3 -B -c 'import broker_admin,broker_service'
systemctl restart homelab-broker.service
test "$(systemctl is-active homelab-broker.service)" = active
test "$(systemctl show homelab-broker.service -p NRestarts --value)" = 0

python3 "$admin" --database "$database" enable-fixed-speech --agent-uid 975
python3 - "$database" <<'PY'
import sqlite3, sys
c=sqlite3.connect(sys.argv[1])
assert c.execute("select unix_uid,state from agents where agent_id='agent-aster-fixed-speech'").fetchone() == (975,'observer')
assert c.execute("select execution_mode,enabled,credential_type,custody_identifier,credential_scope,rotation_due,revocation_method from services where service_id='aster-fixed-speech'").fetchone() == ('proxy',1,'none','none','fixed aster.speech read only','not-applicable','disable service and stop dedicated caller')
assert c.execute("select service_id,risk_class,probation_allowed,enabled from capabilities where capability='diagnostic.aster-speech.latest'").fetchone() == ('aster-fixed-speech','green',0,1)
assert c.execute("select capability from agent_capabilities where agent_id='agent-aster-fixed-speech'").fetchall() == [('diagnostic.aster-speech.latest',)]
assert c.execute("select enabled from services where service_id='aster-fixed-doctor'").fetchone() == (1,)
assert c.execute("select count(*) from agent_capabilities where agent_id='agent-aster-fixed-doctor' and capability='diagnostic.aster-inference.latest'").fetchone()[0] == 1
PY

systemctl start aster-fixed-speech-gateway.service
systemctl start aster-fixed-speech-caller.service
test "$(systemctl is-active aster-fixed-speech-gateway.service)" = active
test "$(systemctl is-active aster-fixed-speech-caller.service)" = active
test "$(systemctl is-enabled aster-fixed-speech-gateway.service 2>/dev/null || true)" = disabled
test "$(systemctl is-enabled aster-fixed-speech-caller.service 2>/dev/null || true)" = disabled
wait_for_socket() {
  socket_path=$1
  attempts=0
  while [ "$attempts" -lt 50 ]; do
    test -S "$socket_path" && return 0
    sleep 0.1
    attempts=$((attempts + 1))
  done
  return 1
}
wait_for_socket /run/aster-fixed-speech/gateway.sock
wait_for_socket /run/aster-fixed-speech-caller/caller.sock

canary=$(runuser -u aster -- python3 - <<'PY'
import json,socket
request={"method":"doctor.aster-speech.latest","arguments":{}}
with socket.socket(socket.AF_UNIX) as s:
    s.settimeout(8)
    s.connect("/run/aster-fixed-speech-caller/caller.sock")
    s.sendall(json.dumps(request,separators=(",",":")).encode()+b"\n")
    raw=s.makefile("rb").readline(16385)
response=json.loads(raw)
assert set(response)=={"ok","result"} and response["ok"] is True
result=response["result"]
assert set(result)=={"schema","capability","observation","answer","authority"}
assert result["schema"]==2
assert result["capability"]=="diagnostic.aster-speech.latest"
assert result["authority"]=="not-granted"
assert result["observation"]["facts"] in ({},{"check_id":"aster.speech"})
print(json.dumps({"ok":True,"capability":result["capability"],"state":result["observation"]["state"],"authority":result["authority"]},sort_keys=True))
PY
)
test "$(systemctl is-active homelab-broker.service)" = active
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show homelab-broker.service -p NRestarts --value)" = 0
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test "$(systemctl show aster-fixed-speech-gateway.service -p NRestarts --value)" = 0
test "$(systemctl show aster-fixed-speech-caller.service -p NRestarts --value)" = 0
rm -rf "$packet"
changed=0
trap - EXIT INT TERM
echo "FIXED_SPEECH_ACTIVATION_OK checkpoint=$checkpoint canary=$canary"
