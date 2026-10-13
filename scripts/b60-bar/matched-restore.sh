#!/bin/sh
# Independent transient watchdog: never leave the candidate owning production.
set -eu
python3 /run/b60-matched-sycl/guard.py finalize --execute --allow-production
pct exec 114 -- python3 /run/b60-bar-validate-generation.py
for unit in news-aggregator-ingest.timer news-aggregator-digest.timer; do
    state=$(pct exec 114 -- systemctl is-enabled "$unit" || true)
    case "$state" in
        enabled|enabled-runtime) pct exec 114 -- systemctl start "$unit" ;;
        disabled) : ;; # Owner has reserved the B60 until explicit resume.
        *) echo "Unexpected news timer enablement state" >&2; exit 1 ;;
    esac
done
