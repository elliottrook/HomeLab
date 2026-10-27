#!/bin/bash
set -Eeuo pipefail

candidate=${1:-/tmp/full_aster_first_screen_launch.py}
target=/usr/local/libexec/local-ai-lease/full-inference-pilot/full_aster_first_screen_launch.py
checkpoint=/var/lib/local-ai-lab/full-aster-first-screen-pre-absolute-window-20261027
live_sha=328b41538451a47cf8ae3355c4a3f978c2cdc47cff848b856c1671178f0bca47
candidate_sha=11568103c134b98821aad4154e79645375f15f3021fdaf9ce232340d8ef24d66
changed=0

hash_of() { sha256sum "$1" | cut -d' ' -f1; }

rollback() {
  code=$?
  trap - EXIT INT TERM
  set +e
  if [ "$changed" -eq 1 ]; then
    install -o root -g root -m 0644 "$checkpoint/full_aster_first_screen_launch.py" "$target.new"
    mv -f "$target.new" "$target"
  fi
  rm -f "$candidate"
  echo "FULL_ASTER_WINDOW_ROLLED_BACK exit=$code checkpoint=$checkpoint" >&2
  exit "$code"
}
trap rollback EXIT INT TERM

test "$(id -u)" = 0
test "$(hash_of "$target")" = "$live_sha"
test "$(hash_of "$candidate")" = "$candidate_sha"
test "$(stat -c '%U:%G %a' "$target")" = 'root:root 644'
test ! -e "$checkpoint"
test ! -e /var/lib/local-ai-lab/full-aster-first-screen.json
test ! -e /var/lib/local-ai-lab/full-aster-first-screen-guardian.json
test ! -e /var/lib/local-ai-lab/full-inference-drain.json
test "$(systemctl is-active full-aster-first-screen-20261027.timer)" = active

install -d -o root -g root -m 0700 "$checkpoint"
cp -p "$target" "$checkpoint/full_aster_first_screen_launch.py"
test "$(hash_of "$checkpoint/full_aster_first_screen_launch.py")" = "$live_sha"

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/usr/local/libexec/local-ai-lease/full-inference-pilot:/usr/local/libexec/local-ai-lease/stream-a-evaluation:/usr/local/libexec/local-ai-lease \
  /usr/bin/python3 -B -m py_compile "$candidate"
install -o root -g root -m 0644 "$candidate" "$target.new"
test "$(hash_of "$target.new")" = "$candidate_sha"
changed=1
mv -f "$target.new" "$target"

test "$(hash_of "$target")" = "$candidate_sha"
test "$(stat -c '%U:%G %a' "$target")" = 'root:root 644'
test "$(systemctl is-active full-aster-first-screen-20261027.timer)" = active
test ! -e /var/lib/local-ai-lab/full-aster-first-screen.json
test ! -e /var/lib/local-ai-lab/full-aster-first-screen-guardian.json
test ! -e /var/lib/local-ai-lab/full-inference-drain.json

rm -f "$candidate"
changed=0
trap - EXIT INT TERM
echo "FULL_ASTER_WINDOW_OK checkpoint=$checkpoint"
