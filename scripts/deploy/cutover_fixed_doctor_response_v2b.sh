#!/bin/bash
set -euo pipefail

guest=104
candidate=/opt/aster-agent/candidates/fixed-doctor-response-v2b
checkpoint=/root/aster-fixed-doctor-response-v2-pre-cutover
live_caller=/opt/aster-agent/fixed_doctor_caller.py
live_response=/opt/aster-agent/fixed_doctor_response.py
old_caller_sha=aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a
new_caller_sha=d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48
new_response_sha=4ca8721b1076815de3220dc51a1e499fd6822f3a9a1085bfc561804bea065298

pct_exec() { pct exec "$guest" -- "$@"; }
sha() { pct_exec sha256sum "$1" | awk '{print $1}'; }

[ "$(sha "$candidate/fixed_doctor_caller.py")" = "$new_caller_sha" ]
[ "$(sha "$candidate/fixed_doctor_response.py")" = "$new_response_sha" ]
[ "$(sha "$live_caller")" = "$old_caller_sha" ]
pct_exec test ! -e "$live_response"
[ "$(sha "$checkpoint/fixed_doctor_caller.py")" = "$old_caller_sha" ]
[ "$(pct_exec stat -c %a "$checkpoint")" = 700 ]
[ "$(pct_exec stat -c %a "$checkpoint/fixed_doctor_caller.py")" = 600 ]
pct_exec systemctl is-active --quiet aster-fixed-doctor-caller.service
pct_exec systemctl is-active --quiet aster-agent.service
agent_restarts=$(pct_exec systemctl show -p NRestarts --value aster-agent.service)

changed=0
rollback() {
  status=$?
  if [ "$status" -ne 0 ] && [ "$changed" -eq 1 ]; then
    pct_exec install -o root -g root -m 0644 "$checkpoint/fixed_doctor_caller.py" "$live_caller"
    pct_exec rm -f "$live_response"
    pct_exec systemctl restart aster-fixed-doctor-caller.service
  fi
  exit "$status"
}
trap rollback EXIT

pct_exec install -o root -g root -m 0644 "$candidate/fixed_doctor_caller.py" "$live_caller.new"
pct_exec install -o root -g root -m 0644 "$candidate/fixed_doctor_response.py" "$live_response.new"
[ "$(sha "$live_caller.new")" = "$new_caller_sha" ]
[ "$(sha "$live_response.new")" = "$new_response_sha" ]
pct_exec mv "$live_caller.new" "$live_caller"
pct_exec mv "$live_response.new" "$live_response"
changed=1
pct_exec systemctl restart aster-fixed-doctor-caller.service

for _ in $(seq 1 20); do
  if pct_exec systemctl is-active --quiet aster-fixed-doctor-caller.service; then
    break
  fi
  sleep 0.25
done
pct_exec systemctl is-active --quiet aster-fixed-doctor-caller.service
pct_exec runuser -u aster -- /opt/aster-agent/venv/bin/python -c '
import json,socket
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
s.settimeout(5)
s.connect("/run/aster-fixed-doctor-caller/caller.sock")
s.sendall(b"{\"method\":\"doctor.aster-inference.latest\",\"arguments\":{}}\n")
r=json.loads(s.makefile("rb").readline())
assert r.get("ok") is True
v=r["result"]
assert set(v)=={"schema","capability","observation","answer","authority"}
assert v["schema"]==2 and v["authority"]=="not-granted"
assert v["capability"]=="diagnostic.aster-inference.latest"
assert isinstance(v["answer"],str) and v["answer"].strip()
'
[ "$(sha "$live_caller")" = "$new_caller_sha" ]
[ "$(sha "$live_response")" = "$new_response_sha" ]
pct_exec systemctl is-active --quiet aster-agent.service
[ "$(pct_exec systemctl show -p NRestarts --value aster-agent.service)" = "$agent_restarts" ]
changed=0
trap - EXIT
echo 'FIXED_DOCTOR_V2B_CUTOVER_OK schema=2 authority=not-granted'

