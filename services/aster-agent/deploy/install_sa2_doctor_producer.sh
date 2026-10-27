#!/bin/bash
set -Eeuo pipefail

test "$#" -eq 0
packet=/tmp/aster-sa2-doctor-producer-20261027
target=/opt/aster-agent
checkpoint=/var/lib/aster/sa2-pre-doctor-producer-20261027
files=(doctor_incident_adapter.py sysadmin_incident_store.py sysadmin_registered_producer.py)
before=(
  c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db
  c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb
  b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd
)
after=(
  0baece59b29dcee47395dbc42bab742ba33fa0d3ad708ffedc41c22a2ae23968
  5676b4b865b5ff9100802967dbce1a455aa6a4d8815ac0e489dc09e368978328
  3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a
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
  for name in "${files[@]}"; do
    install -o root -g root -m 0644 "$checkpoint/$name" "$target/$name.new"
    mv -f "$target/$name.new" "$target/$name"
  done
}
rollback() {
  local code=$?
  trap - EXIT INT TERM; set +e
  if [ "$changed" -eq 1 ]; then restore; systemctl restart aster-agent.service; health; fi
  if [ "$staged" -eq 1 ]; then cleanup_new; fi
  rm -rf "$packet"
  echo "SA2_DOCTOR_PRODUCER_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"
for i in "${!files[@]}"; do
  name=${files[$i]}
  test "$(digest "$target/$name")" = "${before[$i]}"
  test "$(stat -c '%U:%G %a' "$target/$name")" = 'root:root 644'
  test ! -e "$target/$name.new"
  test "$(digest "$packet/$name")" = "${after[$i]}"
done

staged=1
install -d -o root -g root -m 0700 "$checkpoint"
for i in "${!files[@]}"; do
  name=${files[$i]}
  cp -p "$target/$name" "$checkpoint/$name"
  test "$(digest "$checkpoint/$name")" = "${before[$i]}"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target" \
  /opt/aster-agent/venv/bin/python -B -c \
  'from pathlib import Path; import sysadmin_registered_producer as p; from sysadmin_incident_store import IncidentStore; assert p.DOCTOR_REPORT == Path("/var/lib/aster/health/latest.json"); assert hasattr(IncidentStore,"pending_follow_up_claim")'
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
for i in "${!files[@]}"; do
  name=${files[$i]}; test "$(digest "$target/$name")" = "${after[$i]}"
done
rm -rf "$packet"
changed=0; staged=0; trap - EXIT INT TERM
echo "SA2_DOCTOR_PRODUCER_OK checkpoint=$checkpoint"
