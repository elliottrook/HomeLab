#!/usr/bin/env python3
"""Read-only B60 Lab Hours booking and control-plane readiness check."""

from __future__ import annotations

import argparse
import json
import re
import subprocess


SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{7,63}")
SAFE_HOST = re.compile(r"[A-Za-z0-9_.@:-]+")


def ssh(host: str, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("ssh", "-o", "BatchMode=yes", host, command),
        capture_output=True, text=True, timeout=30, check=False,
    )


def json_value(raw: str) -> object | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("booking_id")
    parser.add_argument("--host", default="root@192.168.50.10")
    args = parser.parse_args()
    if not SAFE_ID.fullmatch(args.booking_id) or not SAFE_HOST.fullmatch(args.host):
        parser.error("booking id or host is outside the fixed safe character set")

    booking_result = ssh(args.host, f"/usr/local/sbin/aster-lab-hours get {args.booking_id}")
    booking = json_value(booking_result.stdout)
    checks: dict[str, object] = {
        "booking_readable": booking_result.returncode == 0 and isinstance(booking, dict),
    }
    if not isinstance(booking, dict):
        print(json.dumps({"state": "no_go", "checks": checks}, sort_keys=True))
        return 2

    workload = booking.get("workload")
    owner = booking.get("owner")
    if not isinstance(workload, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{2,95}", workload):
        checks["registered_workload_identity"] = False
        print(json.dumps({"state": "no_go", "booking": booking, "checks": checks}, sort_keys=True))
        return 2

    probe = (
        "PYTHONDONTWRITEBYTECODE=1 python3 -B -c '"
        "import json,sys; p=\"/usr/local/libexec/local-ai-lease/full-inference-pilot\"; "
        "sys.path.insert(0,p); import lab_hours_workloads as w; "
        f"s=w.workload(\"{workload}\"); w.validate_registry(); "
        "import lab_hours_reserved_runner as r; r.load_manifest(); "
        f"v=w.validate_inactive_target(p,workload_id=\"{workload}\"); "
        "print(json.dumps({\"owner\":s.owner,\"minimum_booking_seconds\":s.minimum_booking_seconds,"
        "\"recovery_reserve_seconds\":s.recovery_reserve_seconds,\"runner_kind\":s.runner_kind,"
        "\"deadline_seconds\":s.deadline_seconds,\"retryable_session\":s.retryable_session,"
        "\"maximum_attempts\":s.maximum_attempts,"
        "\"target\":v},sort_keys=True))'"
    )
    registry_result = ssh(args.host, probe)
    registry = json_value(registry_result.stdout)
    timer = ssh(args.host, "systemctl is-active aster-lab-hours-dispatch.timer")
    lease = ssh(args.host, "/usr/local/sbin/local-ai-lease status")
    lease_value = json_value(lease.stdout)
    locks = ssh(
        args.host,
        "test ! -e /run/local-ai-lab-operation.lock && "
        "test ! -e /var/lib/local-ai-lab/full-inference-drain.lock",
    )
    duration = int(booking.get("end_epoch", 0)) - int(booking.get("start_epoch", 0))
    checks.update({
        "booking_state_admissible": booking.get("state") in {"scheduled", "claimed"},
        "dispatcher_active": timer.returncode == 0 and timer.stdout.strip() == "active",
        "lease_ready": lease.returncode == 0 and isinstance(lease_value, dict)
            and lease_value.get("state") == "ready",
        "shared_locks_absent": locks.returncode == 0,
        "registry_and_release_valid": registry_result.returncode == 0 and isinstance(registry, dict),
        "owner_matches_registry": isinstance(registry, dict) and registry.get("owner") == owner,
        "duration_meets_registry": isinstance(registry, dict)
            and duration >= int(registry.get("minimum_booking_seconds", 10**18)),
        "recovery_matches_registry": isinstance(registry, dict)
            and int(booking.get("restore_buffer_seconds", -1))
            >= int(registry.get("recovery_reserve_seconds", 10**18)),
        "session_contract_bounded": isinstance(registry, dict)
            and type(registry.get("retryable_session")) is bool
            and (registry.get("maximum_attempts") is None
                 or (type(registry.get("maximum_attempts")) is int
                     and 1 <= int(registry["maximum_attempts"]) <= 16))
            and type(registry.get("deadline_seconds")) is int
            and int(registry.get("deadline_seconds", 0)) > 0,
    })
    if isinstance(registry, dict) and registry.get("retryable_session") is True:
        attempt_count = booking.get("attempt_count", 0)
        attempt_state = booking.get("attempt_state")
        retry_available = booking.get("retry_available", False)
        maximum_attempts = registry.get("maximum_attempts")
        count_within_limit = (maximum_attempts is None
                              or attempt_count <= int(maximum_attempts))
        retry_within_limit = (maximum_attempts is None
                              or attempt_count < int(maximum_attempts))
        checks["session_attempt_state_valid"] = (
            booking.get("state") == "scheduled"
            or (booking.get("state") == "claimed"
                and type(attempt_count) is int
                and 1 <= attempt_count and count_within_limit
                and attempt_state in {"running", "failed_restored", "complete_restored"}
                and (retry_available is not True
                     or (attempt_state == "failed_restored"
                         and retry_within_limit)))
        )
    ready = all(checks.values())
    print(json.dumps({
        "state": "ready" if ready else "no_go",
        "booking": booking,
        "registry": registry,
        "checks": checks,
    }, sort_keys=True))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
