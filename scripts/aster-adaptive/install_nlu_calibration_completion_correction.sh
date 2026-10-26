#!/bin/bash
set -Eeuo pipefail

vmid=110
source_commit=0e4b7311
target=/var/lib/aster-nlu-calibration/nlu-calibration-v1
runner=/tmp/nlu_calibration_runner.$source_commit.py
validator=/tmp/nlu_calibration_stage_manifest.$source_commit.py
manifest=/tmp/nlu-calibration-stage-manifest.$source_commit.json
tests=/tmp/test_nlu_calibration_runner.$source_commit.py
stamp=$(date -u +%Y%m%dT%H%M%SZ)
checkpoint=/var/lib/aster-nlu-calibration/checkpoints/completion-$source_commit-$stamp
old_runner=a8cca4daa3a0504b07e9dc70bee4d8e04d3f181ac742c53954718c6918fc5a0f
new_runner=88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0
validator_sha=215e221165fafcacb43ccae7230c0cad13a6e19ca9e41ccab9e019f815dc42e5
manifest_sha=835bcb55ba93d25427b322c6cf93aee06cba1b5e7221af7fb63dbd41d1aab114
tests_sha=c9bdc21bafd9bfcdc263c56addd12c29fa88a5bd3ef23ab4c85d04d18c3b555d
started=0

cleanup_transport() {
  pct exec "$vmid" -- rm -f "$runner" "$validator" "$manifest" "$tests"
  rm -f "$runner" "$validator" "$manifest" "$tests"
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
test "$(sha256sum "$tests" | cut -d' ' -f1)" = "$tests_sha"
pct push "$vmid" "$runner" "$runner"
pct push "$vmid" "$validator" "$validator"
pct push "$vmid" "$manifest" "$manifest"
pct push "$vmid" "$tests" "$tests"

/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
test "$(pct exec "$vmid" -- systemctl is-active aster-llama.service)" = active
test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%F' "$target")" = \
  'root:root:700:directory'
test "$(pct exec "$vmid" -- sha256sum "$target/nlu_calibration_runner.py" | cut -d' ' -f1)" = \
  "$old_runner"
pct exec "$vmid" -- test ! -e "$target/run.json"
pct exec "$vmid" -- test ! -e "$target/attempt-journal.jsonl"
pct exec "$vmid" -- test ! -e "$target/__pycache__"
test "$(pct exec "$vmid" -- find "$target" -mindepth 1 -maxdepth 1 -type f | wc -l)" = 11
test -z "$(pct exec "$vmid" -- pgrep -af '[n]lu_calibration_runner' || true)"

pct exec "$vmid" -- install -d -o root -g root -m 0700 \
  /var/lib/aster-nlu-calibration/checkpoints "$checkpoint"
pct exec "$vmid" -- install -o root -g root -m 0600 \
  "$target/nlu_calibration_runner.py" "$checkpoint/nlu_calibration_runner.py"
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
  python3 -B "$tests"
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
  "printf '%s\n' 'source=$source_commit' 'old_runner_sha256=$old_runner' 'new_runner_sha256=$new_runner' 'manifest_sha256=$manifest_sha' 'state=complete' > '$checkpoint/result' && chown root:root '$checkpoint/result' && chmod 0600 '$checkpoint/result'"
cleanup_transport
trap - ERR
printf '{"state":"complete","checkpoint":"%s","runner_sha256":"%s","manifest_sha256":"%s"}\n' \
  "$checkpoint" "$new_runner" "$manifest_sha"
