#!/bin/sh
# Independent transient watchdog: never leave the candidate owning production.
set -eu
python3 /run/b60-matched-sycl/guard.py finalize --execute --allow-production
pct exec 114 -- python3 /run/b60-bar-validate-generation.py
pct exec 114 -- systemctl start news-aggregator-ingest.timer news-aggregator-digest.timer
