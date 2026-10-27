#!/bin/bash
set -Eeuo pipefail

test "$#" -eq 0
packet=/tmp/aster-sa3-proposal-gateway-20261027
target_root=/opt/aster-agent
checkpoint=/var/lib/aster/sa3-pre-proposal-gateway-20261027
files=(aster_agent.py sysadmin_proposal_boundary.py sysadmin_proposal_transport.py sysadmin_proposal_gateway.py)
candidate_shas=(
  02a2001caee5204b6229f7f576dcc945227471ac531b852f0ab0f60ecb032f9b
  121d61c12c2f33368176ec35bcc0047f075c1d21d4640749658bf509fce813ff
  9b4d98df78c69e360e2f59544a47152c7eefc58bcad7f33e74e917158c24e4fa
  4a4d112e8dcb805f5cdead1cedbfca9229b57eb7066ce7b7a5164138c9a5bd9c
)
live_agent_sha=43af11c953fb63fdbc37cd7465fe69fb7b6d0c3cd64cff206d484e0398284613
changed=0
staged_new=0

hash_of() {
  sha256sum "$1" | cut -d' ' -f1
}

wait_for_health() {
  local attempts=0
  while [ "$attempts" -lt 50 ]; do
    if curl -fsS --max-time 2 http://192.168.70.10:9120/health 2>/dev/null \
      | /opt/aster-agent/venv/bin/python -c \
        'import json,sys; assert json.load(sys.stdin) == {"status":"ok","service":"aster-agent"}' \
        2>/dev/null; then
      return 0
    fi
    sleep 0.2
    attempts=$((attempts + 1))
  done
  return 1
}

restore_checkpoint() {
  install -o root -g root -m 0644 "$checkpoint/aster_agent.py" "$target_root/aster_agent.py.new"
  mv -f "$target_root/aster_agent.py.new" "$target_root/aster_agent.py"
  rm -f \
    "$target_root/sysadmin_proposal_boundary.py" \
    "$target_root/sysadmin_proposal_transport.py" \
    "$target_root/sysadmin_proposal_gateway.py"
}

cleanup_partial_installs() {
  rm -f \
    "$target_root/aster_agent.py.new" \
    "$target_root/sysadmin_proposal_boundary.py.new" \
    "$target_root/sysadmin_proposal_transport.py.new" \
    "$target_root/sysadmin_proposal_gateway.py.new"
}

rollback() {
  local code=$?
  trap - EXIT INT TERM
  set +e
  if [ "$changed" -eq 1 ]; then
    restore_checkpoint
    systemctl restart aster-agent.service
    wait_for_health
  fi
  if [ "$staged_new" -eq 1 ]; then
    cleanup_partial_installs
  fi
  rm -rf "$packet"
  echo "SA3_PROPOSAL_GATEWAY_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"
test "$(hash_of "$target_root/aster_agent.py")" = "$live_agent_sha"
test "$(stat -c '%U:%G %a' "$target_root/aster_agent.py")" = 'root:root 644'
test ! -e "$target_root/sysadmin_proposal_boundary.py"
test ! -e "$target_root/sysadmin_proposal_transport.py"
test ! -e "$target_root/sysadmin_proposal_gateway.py"
for name in "${files[@]}"; do
  test ! -e "$target_root/$name.new"
done

staged_new=1
for index in "${!files[@]}"; do
  name=${files[$index]}
  test "$(hash_of "$packet/$name")" = "${candidate_shas[$index]}"
done

install -d -o root -g root -m 0700 "$checkpoint"
cp -p "$target_root/aster_agent.py" "$checkpoint/aster_agent.py"
test "$(hash_of "$checkpoint/aster_agent.py")" = "$live_agent_sha"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target_root" \
  /opt/aster-agent/venv/bin/python -B -c \
  'import aster_agent,sysadmin_proposal_boundary,sysadmin_proposal_transport,sysadmin_proposal_gateway; assert any(getattr(r,"path",None)=="/v1/sysadmin/incidents/{incident_id}/propose" for r in aster_agent.app.routes)'

for index in "${!files[@]}"; do
  name=${files[$index]}
  install -o root -g root -m 0644 "$packet/$name" "$target_root/$name.new"
  test "$(hash_of "$target_root/$name.new")" = "${candidate_shas[$index]}"
done
changed=1
for name in "${files[@]}"; do
  mv -f "$target_root/$name.new" "$target_root/$name"
done

systemctl restart aster-agent.service
wait_for_health
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 http://192.168.70.10:9120/v1/models)" = 401
test "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 -X POST \
  http://192.168.70.10:9120/v1/sysadmin/incidents/inc-auth-check/propose)" = 401
for index in "${!files[@]}"; do
  name=${files[$index]}
  test "$(hash_of "$target_root/$name")" = "${candidate_shas[$index]}"
  test "$(stat -c '%U:%G %a' "$target_root/$name")" = 'root:root 644'
done

rm -rf "$packet"
changed=0
staged_new=0
trap - EXIT INT TERM
echo "SA3_PROPOSAL_GATEWAY_OK checkpoint=$checkpoint"
