#!/bin/bash
set -Eeuo pipefail

packet=${1:-/tmp/aster-sa0-current-composite-20261027}
candidate=$packet/aster_agent.py
target=/opt/aster-agent/aster_agent.py
knowledge=/opt/aster-agent/knowledge_usage.py
unit=/etc/systemd/system/aster-agent.service
checkpoint=/var/lib/aster/sa0-pre-current-composite-20261027

live_sha=7edc7ff9776357d62f6eff45de2093aab5749bb38317251b404df88012c6b50c
candidate_sha=e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116
knowledge_sha=900a7fccad9c6e665297e3655e01844ca976705f69b45fac689858a00ccbfb55
unit_sha=530b3918e08e8a9e27ce2f651b18fd4967bdba8c453eecc40b37788b4c9b1a15
changed=0

hash_of() {
  sha256sum "$1" | cut -d' ' -f1
}

wait_for_health() {
  local attempts=0
  while [ "$attempts" -lt 50 ]; do
    if [ "$(curl -fsS --max-time 2 http://192.168.70.10:9120/health 2>/dev/null || true)" = '{"status":"ok"}' ]; then
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
    install -o root -g root -m 0644 "$checkpoint/aster_agent.py" "$target.new"
    mv -f "$target.new" "$target"
    systemctl restart aster-agent.service
    wait_for_health
  fi
  rm -rf "$packet"
  echo "SA0_COMPOSITE_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(hash_of "$candidate")" = "$candidate_sha"
test "$(hash_of "$target")" = "$live_sha"
test "$(hash_of "$knowledge")" = "$knowledge_sha"
test "$(hash_of "$unit")" = "$unit_sha"
test "$(stat -c '%U:%G %a' "$target")" = 'root:root 644'
test "$(stat -c '%U:%G %a' "$knowledge")" = 'root:root 644'
test "$(stat -c '%U:%G %a' "$unit")" = 'root:root 644'
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test ! -e "$checkpoint"

install -d -o root -g root -m 0700 "$checkpoint"
cp -p "$target" "$checkpoint/aster_agent.py"
test "$(hash_of "$checkpoint/aster_agent.py")" = "$live_sha"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$packet:/opt/aster-agent" \
  /opt/aster-agent/venv/bin/python -B -c 'import aster_agent, knowledge_usage'
install -o root -g root -m 0644 "$candidate" "$target.new"
test "$(hash_of "$target.new")" = "$candidate_sha"
changed=1
mv -f "$target.new" "$target"

systemctl restart aster-agent.service
wait_for_health
test "$(systemctl is-active aster-agent.service)" = active
test "$(systemctl show aster-agent.service -p NRestarts --value)" = 0
test "$(hash_of "$target")" = "$candidate_sha"
test "$(hash_of "$knowledge")" = "$knowledge_sha"
test "$(hash_of "$unit")" = "$unit_sha"

rm -rf "$packet"
changed=0
trap - EXIT INT TERM
echo "SA0_COMPOSITE_OK source_sha256=$candidate_sha checkpoint=$checkpoint"
