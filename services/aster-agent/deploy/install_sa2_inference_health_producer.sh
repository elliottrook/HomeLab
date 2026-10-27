#!/bin/bash
set -Eeuo pipefail

packet=${1:-/tmp/aster-sa2-inference-health-20261027}
target_root=/opt/aster-agent
checkpoint=/var/lib/aster/sa2-pre-inference-health-20261027
files=(aster_agent.py sysadmin_registered_producer.py)
live_shas=(
  28f2e2f611ade77fac0f054fa0d238e4c575075d8013d5548d2810d1b9dfc703
  5c112b670e42e50ee63a7658253197937663ae0775c623e3e92345e23193f931
)
candidate_shas=(
  43af11c953fb63fdbc37cd7465fe69fb7b6d0c3cd64cff206d484e0398284613
  b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd
)
changed=0

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
  local name
  for name in "${files[@]}"; do
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
  echo "SA2_INFERENCE_HEALTH_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"
for index in "${!files[@]}"; do
  name=${files[$index]}
  test "$(hash_of "$target_root/$name")" = "${live_shas[$index]}"
  test "$(stat -c '%U:%G %a' "$target_root/$name")" = 'root:root 644'
  test "$(hash_of "$packet/$name")" = "${candidate_shas[$index]}"
done

install -d -o root -g root -m 0700 "$checkpoint"
for index in "${!files[@]}"; do
  name=${files[$index]}
  cp -p "$target_root/$name" "$checkpoint/$name"
  test "$(hash_of "$checkpoint/$name")" = "${live_shas[$index]}"
done

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target_root" \
  /opt/aster-agent/venv/bin/python -B -c \
  'import aster_agent, sysadmin_registered_producer'

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
  name=${files[$index]}
  test "$(hash_of "$target_root/$name")" = "${candidate_shas[$index]}"
  test "$(stat -c '%U:%G %a' "$target_root/$name")" = 'root:root 644'
done

rm -rf "$packet"
changed=0
trap - EXIT INT TERM
echo "SA2_INFERENCE_HEALTH_OK checkpoint=$checkpoint"
