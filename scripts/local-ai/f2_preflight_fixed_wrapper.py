"""Fixed source-bound F2 preflight wrapper candidate.

No CLI may select the cycle, snapshot path, exclusion, or installed pin
map. The wrapper obtains them from fixed host probes and the local clock.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from f2_preflight_snapshot import (CLOCK, F2Coordinator, F2PreflightError,
                                   LEASE_STATUS, PVE_ARTIFACTS, collect_snapshot,
                                   final_guard, read_snapshot, write_snapshot)

LOCAL_ZONE = ZoneInfo("America/Vancouver")
SNAPSHOT_DIR = Path("/var/lib/local-ai-lab/f2-preflight")
SNAPSHOT_PATH = SNAPSHOT_DIR / "current.json"
COORDINATOR_ROOT = Path("/var/lib/local-ai-lab")
EXPECTED_PINS = {
    "/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py": "6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f",
    "/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py": "5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb",
    "/usr/local/libexec/local-ai-lease/retained_archive_integrity.py": "11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5",
    "/usr/local/libexec/local-ai-lease/fixed_source_adapters.py": "8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9",
    "/usr/local/libexec/local-ai-lease/host_exclusion.py": "f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563",
    "/usr/local/sbin/local-ai-lease": "67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c",
}


def _probe_epoch(runner) -> int:
    code, output = runner(CLOCK, 3.0)
    if code != 0:
        raise F2PreflightError("fixed F2 clock probe failed")
    try:
        return int(output.strip())
    except ValueError as exc:
        raise F2PreflightError("fixed F2 clock output is invalid") from exc


def capture_fixed_preflight(runner):
    """Capture the slow chain using only fixed host-owned values."""
    captured = _probe_epoch(runner)
    cycle = datetime.fromtimestamp(captured, LOCAL_ZONE).strftime("%Y-%m-%d")
    snapshot = collect_snapshot(runner, cycle=cycle, lease_issued_epoch=captured,
                                captured_epoch=captured)
    write_snapshot(SNAPSHOT_PATH, snapshot)
    return snapshot


def run_fixed_final_guard(runner) -> None:
    """Run the narrow guard against the fixed snapshot and complete pin map."""
    snapshot = read_snapshot(SNAPSHOT_PATH)
    with F2Coordinator(COORDINATOR_ROOT) as coordinator:
        final_guard(snapshot, runner=runner, expected_pins=EXPECTED_PINS,
                    coordinator=coordinator)
