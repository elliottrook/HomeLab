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
import re
import sys
from datetime import datetime, timedelta, timezone

with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)

required_report = {"schema_version", "generated_at", "services", "repair_candidates"}
required_service = {"status", "coverage", "queue_pending", "queue_errors", "import_pending", "import_errors"}
allowed_services = {"sonarr", "radarr", "lidarr", "prowlarr", "sabnzbd", "jellyfin"}
allowed_coverage = {"health", "queue", "import"}
allowed_status = {"healthy", "warning", "failed", "unknown"}

if not isinstance(report, dict) or set(report) != required_report or report["schema_version"] != 1:
    raise SystemExit("invalid report")
try:
    generated_at = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
except ValueError:
    raise SystemExit("invalid report timestamp")
now = datetime.now(timezone.utc)
if (
    generated_at.tzinfo is None
    or generated_at.astimezone(timezone.utc) > now
    or now - generated_at.astimezone(timezone.utc) > timedelta(minutes=15)
):
    raise SystemExit("invalid report timestamp")
services = report["services"]
if not isinstance(services, dict) or not services or not set(services).issubset(allowed_services):
    raise SystemExit("invalid services")
for service in services.values():
    if not isinstance(service, dict) or set(service) != required_service:
        raise SystemExit("invalid service")
    coverage = service["coverage"]
    if (
        service["status"] not in allowed_status
        or not isinstance(coverage, list)
        or len(coverage) != len(set(coverage))
        or "health" not in coverage
        or not set(coverage).issubset(allowed_coverage)
    ):
        raise SystemExit("invalid coverage")
    for scope, fields in {
        "queue": ("queue_pending", "queue_errors"),
        "import": ("import_pending", "import_errors"),
    }.items():
        values = [service[field] for field in fields]
        if scope in coverage:
            if any(
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
                or value > 1_000_000
                for value in values
            ):
                raise SystemExit("invalid counters")
        elif any(value is not None for value in values):
            raise SystemExit("invalid uncovered counters")
candidates = report["repair_candidates"]
if not isinstance(candidates, list) or len(candidates) > 1:
    raise SystemExit("invalid candidates")
for candidate in candidates:
    if not isinstance(candidate, dict) or set(candidate) != {"operation", "service", "candidate_ref", "expires_at"}:
        raise SystemExit("invalid candidate")
    if candidate["operation"] != "dismiss_stale_radarr_queue_record" or candidate["service"] != "radarr":
        raise SystemExit("invalid candidate")
    if not isinstance(candidate["candidate_ref"], str) or not re.fullmatch(r"radarr-q-[a-z2-7]{16}", candidate["candidate_ref"]):
        raise SystemExit("invalid candidate")
    try:
        expires_at = datetime.fromisoformat(str(candidate["expires_at"]).replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit("invalid candidate")
    if (
        expires_at.tzinfo is None
        or expires_at.astimezone(timezone.utc) <= now
        or expires_at.astimezone(timezone.utc)
        > generated_at.astimezone(timezone.utc) + timedelta(minutes=5)
    ):
        raise SystemExit("invalid candidate")
PY

pct push 104 "$temporary" /tmp/aster-arr-report.candidate.json
pct exec 104 -- sh -c 'set -eu
install -d -o root -g aster -m 750 /var/lib/aster/arr-report
install -o root -g aster -m 640 /tmp/aster-arr-report.candidate.json /var/lib/aster/arr-report/latest.json
rm -f /tmp/aster-arr-report.candidate.json'
