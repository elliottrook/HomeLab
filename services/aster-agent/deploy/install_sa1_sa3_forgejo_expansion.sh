#!/bin/bash
set -Eeuo pipefail

test "$#" -eq 0
packet=/tmp/aster-sa1-sa3-forgejo-expansion-20261028
target=/opt/aster-agent
checkpoint=/var/lib/aster/sa1-sa3-pre-forgejo-expansion-20261028
files=(aster_agent.py forgejo_incident_adapter.py sysadmin_registered_producer.py sysadmin_proposal_boundary.py sysadmin_proposal_transport.py)
before=(
  02a2001caee5204b6229f7f576dcc945227471ac531b852f0ab0f60ecb032f9b
  absent
  3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a
  121d61c12c2f33368176ec35bcc0047f075c1d21d4640749658bf509fce813ff
  9b4d98df78c69e360e2f59544a47152c7eefc58bcad7f33e74e917158c24e4fa
)
after=(
  75d49b81ce7e277ff67dfe0f929536f94835dc93c710c6206aa558259208261d
  e0944352e8304d25e5f55b74d88df700cd1b64ad3fdedc784aa7c66486f25809
  27175ab0d1a0cbcfc1fbc3201859417e2818b22d1738f1d2d2dc3a48f8191c96
  2050cd7e12b5207dce21c5087d4e643ffa85965376d415c0ed7ee673d9894515
  dca6a28c3096fc398f49cbdc33ddb1f26ff09b559870566281d7bec42be1c6be
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
  for i in 0 2 3 4; do
    name=${files[$i]}; install -o root -g root -m 0644 "$checkpoint/$name" "$target/$name.new"
    mv -f "$target/$name.new" "$target/$name"
  done
  rm -f "$target/forgejo_incident_adapter.py"
}
rollback() {
  local code=$?
  trap - EXIT INT TERM; set +e
  if [ "$changed" -eq 1 ]; then restore; systemctl restart aster-agent.service; health; fi
  if [ "$staged" -eq 1 ]; then cleanup_new; fi
  rm -rf "$packet"
  echo "SA1_SA3_FORGEJO_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
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
  if [ "${before[$i]}" = absent ]; then
    test ! -e "$target/$name"
  else
    test "$(digest "$target/$name")" = "${before[$i]}"
    test "$(stat -c '%U:%G %a' "$target/$name")" = 'root:root 644'
  fi
done

staged=1
install -d -o root -g root -m 0700 "$checkpoint"
for i in 0 2 3 4; do
  name=${files[$i]}; cp -p "$target/$name" "$checkpoint/$name"
  test "$(digest "$checkpoint/$name")" = "${before[$i]}"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target" \
  /opt/aster-agent/venv/bin/python -B -c \
  'import aster_agent; import forgejo_incident_adapter as f; import sysadmin_registered_producer as p; from sysadmin_proposal_transport import build_model_payload; assert p.FORGEJO_PAIR == ("forgejo-main","git"); assert f.SOURCE == "forgejo-main-report/v1"'
for i in "${!files[@]}"; do
  name=${files[$i]}; install -o root -g root -m 0644 "$packet/$name" "$target/$name.new"
  test "$(digest "$target/$name.new")" = "${after[$i]}"
done
changed=1
for name in "${files[@]}"; do mv -f "$target/$name.new" "$target/$name"; done
systemctl restart aster-agent.service
health
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
for i in "${!files[@]}"; do
  name=${files[$i]}; test "$(digest "$target/$name")" = "${after[$i]}"
  test "$(stat -c '%U:%G %a' "$target/$name")" = 'root:root 644'
done
rm -rf "$packet"
changed=0; staged=0; trap - EXIT INT TERM
echo "SA1_SA3_FORGEJO_OK checkpoint=$checkpoint"
