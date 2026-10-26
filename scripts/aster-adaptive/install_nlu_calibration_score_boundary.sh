#!/bin/bash
set -Eeuo pipefail

vmid=110
source_commit=9f4da72d
target=/var/lib/aster-nlu-calibration/nlu-calibration-v1
score=/tmp/nlu_calibration_score.$source_commit.py
journal=/tmp/nlu_calibration_journal.$source_commit.py
validator=/tmp/nlu_calibration_stage_manifest.$source_commit.py
manifest=/tmp/nlu-calibration-stage-manifest.$source_commit.json
score_tests=/tmp/test_nlu_calibration_score.$source_commit.py
corpus_tests=/tmp/test_nlu_calibration_corpus.py
stamp=$(date -u +%Y%m%dT%H%M%SZ)
checkpoint=/var/lib/aster-nlu-calibration/checkpoints/score-boundary-$source_commit-$stamp

old_score=ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd
old_journal=992960fe76540941fe9adf7b75ddaf82541c55039782bf4cf360ad6c5279a744
new_score=7bce041e47a7707fcf35d3c3787e1e12e6725fff4c5b80db81f92ad7e5492ccd
new_journal=966786f8952aa990915044281b3ddc45241b05940102aad2c4ddfad19abf5beb
new_validator=83c7ed1135e444d832518e95bc7df51c59d5cb1c3cc7041177f31fc8cb84c3c9
new_manifest=7b547d9b38d3be1d951e2d8cbeee011a723f8582006c0885ad37d01f5388ee80
score_tests_sha=b6d86d82eb6e272a159c1f65b7ae78824a445576fdb26a43ac8990ca7dcef3b0
corpus_tests_sha=3147b69314866239ae8d2ce61b8e7d1e98121d9d5bc96548d154aef5f20ba8c0
started=0

transport_files=("$score" "$journal" "$validator" "$manifest" "$score_tests" "$corpus_tests")

cleanup_transport() {
  pct exec "$vmid" -- rm -f "${transport_files[@]}"
  rm -f "${transport_files[@]}"
}

rollback() {
  local rc=$?
  trap - ERR
  set +e
  if test "$started" = 1; then
    for name in nlu_calibration_score.py nlu_calibration_journal.py; do
      pct exec "$vmid" -- install -o root -g root -m 0600 \
        "$checkpoint/$name" "$target/.$name.rollback.$$"
      pct exec "$vmid" -- mv -T "$target/.$name.rollback.$$" "$target/$name"
    done
  fi
  cleanup_transport
  printf '{"state":"rolled_back","exit":%d,"checkpoint":"%s"}\n' "$rc" "$checkpoint" >&2
  exit "$rc"
}
trap rollback ERR

check_sha() { test "$(sha256sum "$1" | cut -d' ' -f1)" = "$2"; }
check_sha "$score" "$new_score"
check_sha "$journal" "$new_journal"
check_sha "$validator" "$new_validator"
check_sha "$manifest" "$new_manifest"
check_sha "$score_tests" "$score_tests_sha"
check_sha "$corpus_tests" "$corpus_tests_sha"
for path in "${transport_files[@]}"; do pct push "$vmid" "$path" "$path"; done

/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'
test "$(pct exec "$vmid" -- systemctl is-active aster-llama.service)" = active
test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%F' "$target")" = 'root:root:700:directory'
check_installed() {
  test "$(pct exec "$vmid" -- sha256sum "$target/$1" | cut -d' ' -f1)" = "$2"
}
check_installed nlu_calibration_score.py "$old_score"
check_installed nlu_calibration_journal.py "$old_journal"
pct exec "$vmid" -- test ! -e "$target/run.json"
pct exec "$vmid" -- test ! -e "$target/attempt-journal.jsonl"
pct exec "$vmid" -- test ! -e "$target/__pycache__"
test -z "$(pct exec "$vmid" -- pgrep -af '[n]lu_calibration_runner' || true)"

pct exec "$vmid" -- install -d -o root -g root -m 0700 \
  /var/lib/aster-nlu-calibration/checkpoints "$checkpoint"
for name in nlu_calibration_score.py nlu_calibration_journal.py; do
  pct exec "$vmid" -- install -o root -g root -m 0600 "$target/$name" "$checkpoint/$name"
done
started=1

install_one() {
  local source_path=$1 target_name=$2
  pct exec "$vmid" -- install -o root -g root -m 0600 \
    "$source_path" "$target/.$target_name.new.$$"
  pct exec "$vmid" -- mv -T "$target/.$target_name.new.$$" "$target/$target_name"
}
install_one "$score" nlu_calibration_score.py
install_one "$journal" nlu_calibration_journal.py

check_installed nlu_calibration_score.py "$new_score"
check_installed nlu_calibration_journal.py "$new_journal"
for name in nlu_calibration_score.py nlu_calibration_journal.py; do
  test "$(pct exec "$vmid" -- stat -c '%U:%G:%a:%h:%F' "$target/$name")" = 'root:root:600:1:regular file'
done
pct exec "$vmid" -- env PYTHONPATH="$target" PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$validator" --manifest "$manifest" --staged-directory "$target"
pct exec "$vmid" -- sh -c \
  "cd /tmp && PYTHONPATH='$target:/tmp' PYTHONDONTWRITEBYTECODE=1 python3 -B '$score_tests'"
pct exec "$vmid" -- env PYTHONPATH="$target" PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
  'import nlu_calibration_runner, nlu_calibration_score, nlu_calibration_journal, nlu_calibration_stage_manifest'
pct exec "$vmid" -- test ! -e "$target/__pycache__"
pct exec "$vmid" -- test ! -e "$target/run.json"
pct exec "$vmid" -- test ! -e "$target/attempt-journal.jsonl"
test -z "$(pct exec "$vmid" -- pgrep -af '[n]lu_calibration_runner' || true)"
test "$(pct exec "$vmid" -- systemctl is-active aster-llama.service)" = active
/usr/local/sbin/local-ai-lease status | python3 -c \
  'import json,sys; assert json.load(sys.stdin) == {"state":"ready"}'

pct exec "$vmid" -- sh -c \
  "printf '%s\n' 'source=$source_commit' 'score_sha256=$new_score' 'journal_sha256=$new_journal' 'manifest_sha256=$new_manifest' 'state=complete' > '$checkpoint/result' && chown root:root '$checkpoint/result' && chmod 0600 '$checkpoint/result'"
cleanup_transport
trap - ERR
printf '{"state":"complete","checkpoint":"%s","score_sha256":"%s","journal_sha256":"%s","manifest_sha256":"%s"}\n' \
  "$checkpoint" "$new_score" "$new_journal" "$new_manifest"
