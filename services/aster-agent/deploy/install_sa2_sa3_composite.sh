#!/bin/bash
set -Eeuo pipefail

test "$#" -eq 0
packet=/tmp/aster-sa2-sa3-composite-20261027
target=/opt/aster-agent
checkpoint=/var/lib/aster/sa2-sa3-pre-composite-20261027
files=(aster_agent.py doctor_incident_adapter.py sysadmin_incident_store.py sysadmin_registered_producer.py sysadmin_proposal_boundary.py sysadmin_proposal_transport.py sysadmin_proposal_gateway.py)
before=(
  43af11c953fb63fdbc37cd7465fe69fb7b6d0c3cd64cff206d484e0398284613
  c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db
  c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb
  b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd
)
after=(
  02a2001caee5204b6229f7f576dcc945227471ac531b852f0ab0f60ecb032f9b
  0baece59b29dcee47395dbc42bab742ba33fa0d3ad708ffedc41c22a2ae23968
  5676b4b865b5ff9100802967dbce1a455aa6a4d8815ac0e489dc09e368978328
  3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a
  121d61c12c2f33368176ec35bcc0047f075c1d21d4640749658bf509fce813ff
  9b4d98df78c69e360e2f59544a47152c7eefc58bcad7f33e74e917158c24e4fa
  4a4d112e8dcb805f5cdead1cedbfca9229b57eb7066ce7b7a5164138c9a5bd9c
)
changed=0
staged=0

digest() { sha256sum "$1" | cut -d' ' -f1; }
health() {
  local n=0
  while [ "$n" -lt 50 ]; do
    curl -fsS --max-time 2 http://192.168.70.10:9120/health 2>/dev/null |
      /opt/aster-agent/venv/bin/python -c \
      'import json,sys; assert json.load(sys.stdin)=={"status":"ok","service":"aster-agent"}' \
      2>/dev/null && return 0
    sleep 0.2; n=$((n + 1))
  done
  return 1
}
cleanup_new() { for name in "${files[@]}"; do rm -f "$target/$name.new"; done; }
restore() {
  for name in "${files[@]:0:4}"; do
    install -o root -g root -m 0644 "$checkpoint/$name" "$target/$name.new"
    mv -f "$target/$name.new" "$target/$name"
  done
  for name in "${files[@]:4:3}"; do rm -f "$target/$name"; done
}
rollback() {
  local code=$?
  trap - EXIT INT TERM; set +e
  if [ "$changed" -eq 1 ]; then restore; systemctl restart aster-agent.service; health; fi
  if [ "$staged" -eq 1 ]; then cleanup_new; fi
  rm -rf "$packet"
  echo "SA2_SA3_COMPOSITE_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"
for i in "${!files[@]}"; do
  name=${files[$i]}
  test ! -e "$target/$name.new"
  test "$(digest "$packet/$name")" = "${after[$i]}"
  if [ "$i" -lt 4 ]; then
    test "$(digest "$target/$name")" = "${before[$i]}"
    test "$(stat -c '%U:%G %a' "$target/$name")" = 'root:root 644'
  else
    test ! -e "$target/$name"
  fi
done

staged=1
install -d -o root -g root -m 0700 "$checkpoint"
for i in 0 1 2 3; do
  name=${files[$i]}
  cp -p "$target/$name" "$checkpoint/$name"
  test "$(digest "$checkpoint/$name")" = "${before[$i]}"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target" \
  /opt/aster-agent/venv/bin/python -B -c \
  'from pathlib import Path; import aster_agent,sysadmin_registered_producer as p; from sysadmin_incident_store import IncidentStore; assert p.DOCTOR_REPORT == Path("/var/lib/aster/health/latest.json"); assert hasattr(IncidentStore,"pending_follow_up_claim"); assert any(getattr(r,"path",None)=="/v1/sysadmin/incidents/{incident_id}/propose" for r in aster_agent.app.routes); assert any(getattr(r,"path",None)=="/v1/sysadmin/incidents/{incident_id}/observe" for r in aster_agent.app.routes)'
for i in "${!files[@]}"; do
  name=${files[$i]}
  install -o root -g root -m 0644 "$packet/$name" "$target/$name.new"
  test "$(digest "$target/$name.new")" = "${after[$i]}"
done
changed=1
for name in "${files[@]}"; do mv -f "$target/$name.new" "$target/$name"; done
systemctl restart aster-agent.service
health
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 http://192.168.70.10:9120/v1/models)" = 401
for route in propose observe; do
  test "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 -X POST \
    "http://192.168.70.10:9120/v1/sysadmin/incidents/inc-auth-check/$route")" = 401
done
for i in "${!files[@]}"; do
  name=${files[$i]}
  test "$(digest "$target/$name")" = "${after[$i]}"
  test "$(stat -c '%U:%G %a' "$target/$name")" = 'root:root 644'
done
rm -rf "$packet"
changed=0; staged=0; trap - EXIT INT TERM
echo "SA2_SA3_COMPOSITE_OK checkpoint=$checkpoint"
