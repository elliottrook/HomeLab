#!/bin/bash
# Nightly archive compaction (re-encode archive files > 2.5 GB in place; see
# docs/projects/Archive-Large-File-Compaction.md). Shares the archiver's lock and
# waits for it; stops starting new files at the configured deadline.
set -euo pipefail
cd "$(dirname "$0")"
set -a; source ./.env; set +a
exec /usr/bin/python3 -m video_archiver.compact --config config.json --execute >> logs/compact-cron.log 2>&1
