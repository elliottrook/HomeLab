#!/bin/bash
set -Eeuo pipefail

packet=${1:-/tmp/aster-sa2-registered-producer-20261027}
target_root=/opt/aster-agent
checkpoint=/var/lib/aster/sa2-pre-registered-producer-20261027
old_gateway_sha=3915413d0190456456aa419d583e8c8dc69805a7c3e21a849efab3cad8eefd0a
new_gateway_sha=28f2e2f611ade77fac0f054fa0d238e4c575075d8013d5548d2810d1b9dfc703
producer_sha=5c112b670e42e50ee63a7658253197937663ae0775c623e3e92345e23193f931
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

rollback() {
  local code=$?
  trap - EXIT INT TERM
  set +e
  if [ "$changed" -eq 1 ]; then
    install -o root -g root -m 0644 "$checkpoint/aster_agent.py" "$target_root/aster_agent.py.new"
    mv -f "$target_root/aster_agent.py.new" "$target_root/aster_agent.py"
    rm -f "$target_root/sysadmin_registered_producer.py"
    systemctl restart aster-agent.service
    wait_for_health
  fi
  rm -rf "$packet"
  echo "SA2_REGISTERED_PRODUCER_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"
test ! -e "$target_root/sysadmin_registered_producer.py"
test "$(hash_of "$target_root/aster_agent.py")" = "$old_gateway_sha"
test "$(stat -c '%U:%G %a' "$target_root/aster_agent.py")" = 'root:root 644'
test "$(hash_of "$packet/aster_agent.py")" = "$new_gateway_sha"
test "$(hash_of "$packet/sysadmin_registered_producer.py")" = "$producer_sha"

install -d -o root -g root -m 0700 "$checkpoint"
cp -p "$target_root/aster_agent.py" "$checkpoint/aster_agent.py"
test "$(hash_of "$checkpoint/aster_agent.py")" = "$old_gateway_sha"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:$target_root" \
  /opt/aster-agent/venv/bin/python -B -c \
  'import aster_agent, sysadmin_registered_producer'

install -o root -g root -m 0644 "$packet/aster_agent.py" "$target_root/aster_agent.py.new"
install -o root -g root -m 0644 "$packet/sysadmin_registered_producer.py" \
  "$target_root/sysadmin_registered_producer.py.new"
test "$(hash_of "$target_root/aster_agent.py.new")" = "$new_gateway_sha"
test "$(hash_of "$target_root/sysadmin_registered_producer.py.new")" = "$producer_sha"

changed=1
mv -f "$target_root/aster_agent.py.new" "$target_root/aster_agent.py"
mv -f "$target_root/sysadmin_registered_producer.py.new" \
  "$target_root/sysadmin_registered_producer.py"
systemctl restart aster-agent.service
wait_for_health
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 http://192.168.70.10:9120/v1/models)" = 401
test "$(hash_of "$target_root/aster_agent.py")" = "$new_gateway_sha"
test "$(hash_of "$target_root/sysadmin_registered_producer.py")" = "$producer_sha"
test "$(stat -c '%U:%G %a' "$target_root/aster_agent.py")" = 'root:root 644'
test "$(stat -c '%U:%G %a' "$target_root/sysadmin_registered_producer.py")" = 'root:root 644'

rm -rf "$packet"
changed=0
trap - EXIT INT TERM
echo "SA2_REGISTERED_PRODUCER_OK checkpoint=$checkpoint"
