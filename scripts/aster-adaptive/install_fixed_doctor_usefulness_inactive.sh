#!/bin/bash
set -Eeuo pipefail

vmid=104
target=/var/lib/aster/fixed-doctor-usefulness-v1
archive=/tmp/fixed-doctor-usefulness-v1-a9468009.tar.gz
validator=/tmp/fixed_doctor_usefulness_stage_manifest.a9468009.py
manifest=/tmp/fixed-doctor-usefulness-stage-manifest.a9468009.json
archive_sha=7c89cd3a46bfbcff52257e35d0473c9954eb7a73f43ec91f5b54b79f7a1f50ea
validator_sha=88eb7bd866d6db0d874503e42d4e44fc1b4b19d4f041abacb8237e517972e65c
manifest_sha=621235c27fae7d0e6055a9d315fd4ef6197a724993ad93bbd89320d43ad9bfcc
temporary=$target.new.$$
started=0

cleanup_transport() {
  pct exec "$vmid" -- rm -f "$archive" "$validator" "$manifest"
  rm -f "$archive" "$validator" "$manifest"
}

rollback() {
  local rc=$?
  trap - ERR
  set +e
  if test "$started" = 1; then
    pct exec "$vmid" -- rm -rf "$temporary" "$target"
  fi
  cleanup_transport
  printf '{"state":"rolled_back","exit":%d}\n' "$rc" >&2
  exit "$rc"
}
trap rollback ERR

test "$(sha256sum "$archive" | cut -d' ' -f1)" = "$archive_sha"
test "$(sha256sum "$validator" | cut -d' ' -f1)" = "$validator_sha"
test "$(sha256sum "$manifest" | cut -d' ' -f1)" = "$manifest_sha"
/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
test "$(pct status "$vmid" | tr -d '\r')" = 'status: running'
test "$(pct exec "$vmid" -- systemctl is-active aster-agent.service)" = active
pct exec "$vmid" -- test ! -e "$target"
test -z "$(pct exec "$vmid" -- pgrep -af '[r]un_fixed_doctor_usefulness' || true)"

pct push "$vmid" "$archive" "$archive"
pct push "$vmid" "$validator" "$validator"
pct push "$vmid" "$manifest" "$manifest"
pct exec "$vmid" -- install -d -o root -g root -m 0700 "$temporary"
started=1
pct exec "$vmid" -- tar -xzf "$archive" -C "$temporary" --no-same-owner
pct exec "$vmid" -- chown -R root:root "$temporary"
pct exec "$vmid" -- chmod 0700 "$temporary"
pct exec "$vmid" -- find "$temporary" -mindepth 1 -maxdepth 1 -type f \
  -exec chmod 0600 '{}' +
pct exec "$vmid" -- mv -T "$temporary" "$target"

pct exec "$vmid" -- env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$target" \
  python3 -B "$validator" --manifest "$manifest" --staged-directory "$target"
pct exec "$vmid" -- env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$target" \
  python3 -B -c \
  'import fixed_doctor_usefulness, fixed_doctor_usefulness_capture, journaled_fixed_doctor_usefulness_capture, fixed_doctor_usefulness_9b_adapter, fixed_doctor_usefulness_profile, run_fixed_doctor_usefulness'
pct exec "$vmid" -- env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$target" \
  python3 -B "$target/run_fixed_doctor_usefulness.py" --help >/dev/null
pct exec "$vmid" -- test ! -e "$target/__pycache__"
pct exec "$vmid" -- test ! -e "$target/attempt-journal.jsonl"
pct exec "$vmid" -- test ! -e "$target/raw-attempts.json"
test -z "$(pct exec "$vmid" -- pgrep -af '[r]un_fixed_doctor_usefulness' || true)"
test "$(pct exec "$vmid" -- systemctl is-active aster-agent.service)" = active
/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'

cleanup_transport
trap - ERR
printf '{"state":"complete","target":"%s","archive_sha256":"%s"}\n' \
  "$target" "$archive_sha"
