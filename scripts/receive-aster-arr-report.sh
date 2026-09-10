#!/usr/bin/env bash
# Forced SSH command on Proxmox: accept one bounded sanitized ARR report only.
set -euo pipefail

readonly maximum_bytes=65536
temporary=$(mktemp /tmp/aster-arr-report.XXXXXX)
cleanup() { rm -f "$temporary"; }
trap cleanup EXIT

dd of="$temporary" bs=$((maximum_bytes + 1)) count=1 iflag=fullblock status=none
test "$(wc -c < "$temporary")" -le "$maximum_bytes"

python3 - "$temporary" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)

required_report = {"schema_version", "generated_at", "services"}
required_service = {"status", "coverage", "queue_pending", "queue_errors", "import_pending", "import_errors"}
allowed_services = {"sonarr", "radarr", "lidarr", "prowlarr", "sabnzbd", "jellyfin"}
allowed_coverage = {"health", "queue", "import"}

if not isinstance(report, dict) or set(report) != required_report or report["schema_version"] != 1:
    raise SystemExit("invalid report")
services = report["services"]
if not isinstance(services, dict) or not services or not set(services).issubset(allowed_services):
    raise SystemExit("invalid services")
for service in services.values():
    if not isinstance(service, dict) or set(service) != required_service:
        raise SystemExit("invalid service")
    coverage = service["coverage"]
    if not isinstance(coverage, list) or "health" not in coverage or not set(coverage).issubset(allowed_coverage):
        raise SystemExit("invalid coverage")
PY

pct push 104 "$temporary" /tmp/aster-arr-report.candidate.json
pct exec 104 -- sh -c 'set -eu
install -d -o root -g aster -m 750 /var/lib/aster/arr-report
install -o root -g aster -m 640 /tmp/aster-arr-report.candidate.json /var/lib/aster/arr-report/latest.json
rm -f /tmp/aster-arr-report.candidate.json'
