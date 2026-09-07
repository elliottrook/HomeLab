#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
report_dir="$HOME/lab/private-backups/aster-knowledge-review"
mkdir -p "$report_dir"
chmod 700 "$report_dir"

stamp=$(date '+%Y-%m-%dT%H-%M-%S%z')
set +e
"$repo_root/scripts/aster-knowledge-review.py" \
  --reference-root "$HOME/lab/homelab-reference" \
  --report "$report_dir/$stamp.json" \
  >"$report_dir/$stamp.log" 2>&1
status=$?
set -e
cp "$report_dir/$stamp.json" "$report_dir/latest.json"
cp "$report_dir/$stamp.log" "$report_dir/latest.log"
exit "$status"
