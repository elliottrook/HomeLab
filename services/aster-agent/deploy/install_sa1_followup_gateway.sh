#!/bin/bash
set -Eeuo pipefail

packet=${1:-/tmp/aster-sa1-followup-gateway-20261027}
target_root=/opt/aster-agent
checkpoint=/var/lib/aster/sa1-followup-pre-gateway-20261027
changed=0

files=(
  aster_agent.py
  sysadmin_incident_store.py
  sysadmin_incident_stream.py
  sysadmin_followup_selector.py
)
live_shas=(
  e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116
  5a72b9f9c16ff66c64ac4d93d7f4f6ae9f3a7fe61d7a377efca237a95120e555
  2154598ed14c7364a1ddc03b2c5f39ec1722b25b45de034e629965d46be78971
)
candidate_shas=(
  3915413d0190456456aa419d583e8c8dc69805a7c3e21a849efab3cad8eefd0a
  c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb
  90a927675178d0fa344c570217bb3215a55770ac779946fd8c4218c60b64d47c
  f6ce43d5b72ec56ecf82d7257551bcac5bcd20233e368373bb2a77441d1ae14d
)

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
  local index name
  for index in 0 1 2; do
    name=${files[$index]}
    install -o root -g root -m 0644 "$checkpoint/$name" "$target_root/$name.new"
    mv -f "$target_root/$name.new" "$target_root/$name"
  done
  rm -f "$target_root/sysadmin_followup_selector.py"
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
  rm -rf "$packet"
  echo "SA1_FOLLOWUP_GATEWAY_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"
test ! -e "$target_root/sysadmin_followup_selector.py"

for index in 0 1 2; do
  name=${files[$index]}
  test "$(hash_of "$target_root/$name")" = "${live_shas[$index]}"
  test "$(stat -c '%U:%G %a' "$target_root/$name")" = 'root:root 644'
done
for index in "${!files[@]}"; do
  name=${files[$index]}
  test "$(hash_of "$packet/$name")" = "${candidate_shas[$index]}"
done

install -d -o root -g root -m 0700 "$checkpoint"
for index in 0 1 2; do
  name=${files[$index]}
  cp -p "$target_root/$name" "$checkpoint/$name"
  test "$(hash_of "$checkpoint/$name")" = "${live_shas[$index]}"
done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target_root" \
  /opt/aster-agent/venv/bin/python -B -c \
  'import aster_agent, sysadmin_followup_selector, sysadmin_incident_store, sysadmin_incident_stream'

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
for index in "${!files[@]}"; do
  test "$(hash_of "$target_root/${files[$index]}")" = "${candidate_shas[$index]}"
  test "$(stat -c '%U:%G %a' "$target_root/${files[$index]}")" = 'root:root 644'
done

rm -rf "$packet"
changed=0
trap - EXIT INT TERM
echo "SA1_FOLLOWUP_GATEWAY_OK checkpoint=$checkpoint"
