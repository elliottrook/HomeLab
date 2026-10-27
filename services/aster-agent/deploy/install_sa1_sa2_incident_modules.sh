#!/bin/bash
set -Eeuo pipefail

packet=${1:-/tmp/aster-sa1-sa2-incident-modules-20261027}
target_root=/opt/aster-agent
checkpoint=/var/lib/aster/sa1-sa2-pre-incident-modules-20261027
gateway_sha=e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116
changed=0

files=(
  sysadmin_incident_store.py
  sysadmin_incident_stream.py
  sysadmin_investigation.py
)
live_shas=(
  4e8a36a803c3d8e5eac362e4c17a0cadc1f4ae2accca05cc73283b646b8e5c4b
  8aa8c572cbe3208b9b8c1a0ce34dfdab893a064ba79e7e5a87c7d8decca8d683
  bfd5e9675b4a7ef06aa0ddb28e7c9b5fda2076a86957cd5474a75ccbd50ee6fe
)
candidate_shas=(
  5a72b9f9c16ff66c64ac4d93d7f4f6ae9f3a7fe61d7a377efca237a95120e555
  2154598ed14c7364a1ddc03b2c5f39ec1722b25b45de034e629965d46be78971
  1f903f4a702d1548783990c38954d4e21a3688f83a062e42416183c7949481ed
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
  for index in "${!files[@]}"; do
    name=${files[$index]}
    install -o root -g root -m 0644 "$checkpoint/$name" "$target_root/$name.new"
    mv -f "$target_root/$name.new" "$target_root/$name"
  done
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
  echo "SA1_SA2_INCIDENT_MODULES_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(hash_of "$target_root/aster_agent.py")" = "$gateway_sha"
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"

for index in "${!files[@]}"; do
  name=${files[$index]}
  test "$(hash_of "$packet/$name")" = "${candidate_shas[$index]}"
  test "$(hash_of "$target_root/$name")" = "${live_shas[$index]}"
  test "$(stat -c '%U:%G %a' "$target_root/$name")" = 'root:root 644'
done

install -d -o root -g root -m 0700 "$checkpoint"
for index in "${!files[@]}"; do
  name=${files[$index]}
  cp -p "$target_root/$name" "$checkpoint/$name"
  test "$(hash_of "$checkpoint/$name")" = "${live_shas[$index]}"
done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target_root" \
  /opt/aster-agent/venv/bin/python -B -c \
  'import aster_agent, sysadmin_incident_store, sysadmin_incident_stream, sysadmin_investigation'

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
test "$(hash_of "$target_root/aster_agent.py")" = "$gateway_sha"
for index in "${!files[@]}"; do
  test "$(hash_of "$target_root/${files[$index]}")" = "${candidate_shas[$index]}"
done

rm -rf "$packet"
changed=0
trap - EXIT INT TERM
echo "SA1_SA2_INCIDENT_MODULES_OK checkpoint=$checkpoint"
