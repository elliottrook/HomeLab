#!/bin/bash
set -Eeuo pipefail

vmid=104
target=/var/lib/aster/fixed-doctor-usefulness-v1

declare -A hashes=(
  [fixed-doctor-usefulness-profile-v1.json]=5f3183e5a805f2f1a3ab9f1c9f8d5fa30d9006aaba0550cabb33aa6f51f0c003
  [fixed-doctor-usefulness-v1.json]=8478b516e10b64eb3ed2ac9c8bf90ef151023fe8f9b8241fc37cecb9be0df43f
  [fixed_doctor_usefulness.py]=f491bd96e70e31722401ff0ff89ec15977a6defe124bfcb4af58cb6e681d004a
  [fixed_doctor_usefulness_9b_adapter.py]=ca9ad314951e521327ca6561c13781c9f66c69a0137487e03b53be3d59edff3f
  [fixed_doctor_usefulness_capture.py]=307f16808f9be0f196d3264c47ed713fc373bd6e318db860f79f941f7f9b3c58
  [fixed_doctor_usefulness_profile.py]=03fb316e6e78c0e93629c6252e6d9d5b775befcb954f785ae346dea2f96821cb
  [journaled_fixed_doctor_usefulness_capture.py]=2f176dbacb2cd09801ab263724b228f99f4ffe7eefd81711f5acdd899fc96a17
  [run_fixed_doctor_usefulness.py]=a014d0b52ed410b7edffa931c8ad7c90212ef4a382ececd621e49431a0bed981
)

/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
test "$(pct status "$vmid" | tr -d '\r')" = 'status: running'
test "$(pct exec "$vmid" -- systemctl is-active aster-agent.service)" = active
test -z "$(pct exec "$vmid" -- pgrep -af '[r]un_fixed_doctor_usefulness' || true)"

test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%F' "$target")" = \
  'root:root:700:directory'
test "$(pct exec "$vmid" -- find "$target" -mindepth 1 -maxdepth 1 -type f | wc -l | tr -d ' ')" = 8
test -z "$(pct exec "$vmid" -- find "$target" -mindepth 1 -maxdepth 1 ! -type f -print)"

for name in "${!hashes[@]}"; do
  path=$target/$name
  test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%h:%F' "$path")" = \
    'root:root:600:1:regular file'
  test "$(pct exec "$vmid" -- sha256sum "$path" | cut -d' ' -f1)" = \
    "${hashes[$name]}"
done

for forbidden in attempt-journal.jsonl raw-attempts.json __pycache__; do
  pct exec "$vmid" -- test ! -e "$target/$forbidden"
done

for name in "${!hashes[@]}"; do
  pct exec "$vmid" -- rm -f "$target/$name"
done
pct exec "$vmid" -- rmdir "$target"

test "$(pct exec "$vmid" -- systemctl is-active aster-agent.service)" = active
/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
printf '{"state":"removed","target":"%s","files":8}\n' "$target"
