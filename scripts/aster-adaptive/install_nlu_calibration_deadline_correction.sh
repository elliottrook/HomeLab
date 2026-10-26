#!/bin/bash
set -Eeuo pipefail

vmid=110
target=/var/lib/aster-nlu-calibration/nlu-calibration-v1
runner=/tmp/nlu_calibration_runner.682608d2.py
validator=/tmp/nlu_calibration_stage_manifest.682608d2.py
manifest=/tmp/nlu-calibration-stage-manifest.682608d2.json
stamp=$(date -u +%Y%m%dT%H%M%SZ)
checkpoint=/var/lib/aster-nlu-calibration/checkpoints/deadline-682608d2-$stamp
old_runner=b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11
new_runner=a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f
validator_sha=487341d1d35fa7ee313aeb76816162048e2402a985a801f6053e3ea89a971e80
manifest_sha=05aa0f287795dacfa72c37d7b275a85f67e96f0cc253225dcf78908585970e19
started=0

cleanup_transport() {
  pct exec "$vmid" -- rm -f "$runner" "$validator" "$manifest"
  rm -f "$runner" "$validator" "$manifest"
}

rollback() {
  local rc=$?
  trap - ERR
  set +e
  if test "$started" = 1; then
    pct exec "$vmid" -- install -o root -g root -m 0600 \
      "$checkpoint/nlu_calibration_runner.py" \
      "$target/.nlu_calibration_runner.py.rollback.$$"
    pct exec "$vmid" -- mv -T \
      "$target/.nlu_calibration_runner.py.rollback.$$" \
      "$target/nlu_calibration_runner.py"
    if pct exec "$vmid" -- test -d "$checkpoint/__pycache__"; then
      pct exec "$vmid" -- rm -rf "$target/__pycache__"
      pct exec "$vmid" -- mv -T "$checkpoint/__pycache__" "$target/__pycache__"
    fi
  fi
  cleanup_transport
  printf '{"state":"rolled_back","exit":%d,"checkpoint":"%s"}\n' \
    "$rc" "$checkpoint" >&2
  exit "$rc"
}
trap rollback ERR

test "$(sha256sum "$runner" | cut -d' ' -f1)" = "$new_runner"
test "$(sha256sum "$validator" | cut -d' ' -f1)" = "$validator_sha"
test "$(sha256sum "$manifest" | cut -d' ' -f1)" = "$manifest_sha"
pct push "$vmid" "$runner" "$runner"
pct push "$vmid" "$validator" "$validator"
pct push "$vmid" "$manifest" "$manifest"
/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
test "$(pct exec "$vmid" -- systemctl is-active aster-llama.service)" = active
test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%F' "$target")" = \
  'root:root:700:directory'
test "$(pct exec "$vmid" -- sha256sum "$target/nlu_calibration_runner.py" | cut -d' ' -f1)" = \
  "$old_runner"
pct exec "$vmid" -- test ! -e "$target/run.json"
pct exec "$vmid" -- test ! -e "$target/attempt-journal.jsonl"
test "$(pct exec "$vmid" -- find "$target" -mindepth 1 -maxdepth 1 -type f | wc -l)" = 11
test "$(pct exec "$vmid" -- find "$target" -mindepth 1 -maxdepth 1 -type d -printf '%f\n')" = __pycache__
test -z "$(pct exec "$vmid" -- pgrep -af '[n]lu_calibration_runner' || true)"

pct exec "$vmid" -- install -d -o root -g root -m 0700 \
  /var/lib/aster-nlu-calibration/checkpoints "$checkpoint"
pct exec "$vmid" -- install -o root -g root -m 0600 \
  "$target/nlu_calibration_runner.py" "$checkpoint/nlu_calibration_runner.py"
pct exec "$vmid" -- mv -T "$target/__pycache__" "$checkpoint/__pycache__"
started=1

pct exec "$vmid" -- install -o root -g root -m 0600 \
  "$runner" "$target/.nlu_calibration_runner.py.new.$$"
pct exec "$vmid" -- mv -T \
  "$target/.nlu_calibration_runner.py.new.$$" "$target/nlu_calibration_runner.py"

test "$(pct exec "$vmid" -- sha256sum "$target/nlu_calibration_runner.py" | cut -d' ' -f1)" = \
  "$new_runner"
test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%h:%F' "$target/nlu_calibration_runner.py")" = \
  'root:root:600:1:regular file'
pct exec "$vmid" -- env PYTHONPATH="$target" PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$validator" --manifest "$manifest" --staged-directory "$target"
pct exec "$vmid" -- env PYTHONPATH="$target" PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -c \
  'import nlu_calibration_runner, nlu_calibration_corpus, nlu_calibration_release, nlu_calibration_score, nlu_calibration_journal, nlu_local_model_adapter, nlu_candidate_bundle, nlu_threshold_policy'
pct exec "$vmid" -- test ! -e "$target/__pycache__"
pct exec "$vmid" -- test ! -e "$target/run.json"
pct exec "$vmid" -- test ! -e "$target/attempt-journal.jsonl"
test -z "$(pct exec "$vmid" -- pgrep -af '[n]lu_calibration_runner' || true)"
test "$(pct exec "$vmid" -- systemctl is-active aster-llama.service)" = active
/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'

pct exec "$vmid" -- sh -c \
  "printf '%s\n' 'source=682608d2' 'old_runner_sha256=$old_runner' 'new_runner_sha256=$new_runner' 'manifest_sha256=$manifest_sha' 'state=complete' > '$checkpoint/result' && chown root:root '$checkpoint/result' && chmod 0600 '$checkpoint/result'"
cleanup_transport
trap - ERR
printf '{"state":"complete","checkpoint":"%s","runner_sha256":"%s","manifest_sha256":"%s"}\n' \
  "$checkpoint" "$new_runner" "$manifest_sha"
