#!/bin/bash
# Nightly archive compaction (re-encode archive files > 2.0 GB in place; see
# docs/projects/Archive-Large-File-Compaction.md). Shares the archiver's lock and
# waits for it; stops starting new files at the configured deadline.
set -euo pipefail
cd "$(dirname "$0")"
set -a; source ./.env; set +a
# Owner policy 2026-10-03: keep verified transcodes, not snapshot copies of originals.
exec /usr/bin/python3 -m video_archiver.compact --config config.json --execute --no-snapshot >> logs/compact-cron.log 2>&1
