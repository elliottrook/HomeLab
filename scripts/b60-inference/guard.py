#!/usr/bin/env python3
"""Fail-closed preflight and accepted-service finalizer for B60 experiments."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/Vancouver")
PREFLIGHT_HOUR = 22
PREFLIGHT_FIRST_MINUTE = 0
PREFLIGHT_LAST_MINUTE = 14
EXPERIMENT_START_MINUTE = 15
EXPERIMENT_DEADLINE_MINUTE = 20
RESTORATION_DEADLINE_MINUTE = 40
ACCEPTED_BINARY_SHA256 = "47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693"
ACCEPTED_UNIT_SHA256 = "7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013"
CANDIDATE_UNIT = "aster-b60-candidate.service"


class GuardError(RuntimeError):
    pass


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise GuardError("timestamp must include timezone")
    return result.astimezone(TZ)


def validate_preflight(data: dict[str, Any], now: datetime, estimated_minutes: int) -> dict[str, Any]:
    required = {
        "collected_at", "backup_completed_at", "mirror_completed_at", "mirror_state",
        "service_health", "driver", "vulkan_device", "binary_sha256", "unit_sha256",
        "disk_free_bytes", "ram_available_bytes", "vram_headroom_bytes",
    }
    if set(data) != required:
        raise GuardError(f"preflight keys differ: missing={sorted(required-set(data))} extra={sorted(set(data)-required)}")
    local_now = now.astimezone(TZ)
    if not (local_now.hour == PREFLIGHT_HOUR and
            PREFLIGHT_FIRST_MINUTE <= local_now.minute <= PREFLIGHT_LAST_MINUTE):
        raise GuardError("preflight must run from 22:00 through 22:14 America/Vancouver")
    collected = parse_time(data["collected_at"])
    if collected > local_now or local_now - collected > timedelta(minutes=5):
        raise GuardError("preflight evidence is future-dated or older than five minutes")
    for field in ("backup_completed_at", "mirror_completed_at"):
        age = local_now - parse_time(data[field])
        if age < timedelta(0) or age > timedelta(hours=26):
            raise GuardError(f"{field} is not fresh")
    checks = {
        "mirror_success": data["mirror_state"] == "SUCCESS",
        "service_healthy": data["service_health"] == "ok",
        "driver_xe": data["driver"] == "xe",
        "vulkan_b60": "BMG G21" in data["vulkan_device"],
        "accepted_binary": data["binary_sha256"] == ACCEPTED_BINARY_SHA256,
        "accepted_unit": data["unit_sha256"] == ACCEPTED_UNIT_SHA256,
        "disk_headroom": int(data["disk_free_bytes"]) >= 20 * 1024**3,
        "ram_headroom": int(data["ram_available_bytes"]) >= 4 * 1024**3,
        "vram_headroom": int(data["vram_headroom_bytes"]) >= 2 * 1024**3,
    }
    failed = sorted(key for key, passed in checks.items() if not passed)
    if failed:
        raise GuardError(f"preflight failed: {failed}")
    hard_stop = local_now.replace(hour=23, minute=RESTORATION_DEADLINE_MINUTE,
                                  second=0, microsecond=0)
    experiment_deadline = local_now.replace(hour=23, minute=EXPERIMENT_DEADLINE_MINUTE,
                                             second=0, microsecond=0)
    if local_now + timedelta(minutes=estimated_minutes) > experiment_deadline:
        raise GuardError("estimated run would cross the 23:20 experiment deadline")
    return {"checks": checks, "start_not_before": local_now.replace(minute=EXPERIMENT_START_MINUTE, second=0, microsecond=0).isoformat(),
            "experiment_deadline": experiment_deadline.isoformat(), "restoration_deadline": hard_stop.isoformat()}


def commands() -> list[list[str]]:
    return [
        ["pct", "exec", "110", "--", "systemctl", "stop", CANDIDATE_UNIT],
        ["pct", "exec", "110", "--", "systemctl", "stop", "aster-llama.service"],
        ["pct", "exec", "110", "--", "systemctl", "start", "--no-block", "aster-llama.service"],
        ["pct", "exec", "110", "--", "systemctl", "is-active", "--quiet", "aster-llama.service"],
        ["pct", "exec", "110", "--", "curl", "-fsS", "http://192.168.70.12:11435/health"],
        ["pct", "exec", "110", "--", "sha256sum", "/opt/llama.cpp-b11081/llama-server"],
        ["pct", "exec", "110", "--", "sha256sum", "/etc/systemd/system/aster-llama.service"],
        ["readlink", "/sys/bus/pci/devices/0000:04:00.0/driver"],
        ["pct", "exec", "110", "--", "vulkaninfo", "--summary"],
    ]


def execute_finalizer(run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
                      sleep: Callable[[float], None] = time.sleep,
                      quiesce_seconds: int = 30, readiness_attempts: int = 60,
                      readiness_interval: int = 5) -> None:
    steps = commands()
    # Candidate absence is acceptable. Stopping accepted production is mandatory so
    # GPU/process state can quiesce before a clean, non-blocking start.
    run(steps[0], capture_output=True, text=True, timeout=180)
    stopped = run(steps[1], capture_output=True, text=True, timeout=180)
    if stopped.returncode != 0:
        raise GuardError("finalizer failed to stop accepted service")
    sleep(quiesce_seconds)
    started = run(steps[2], capture_output=True, text=True, timeout=180)
    if started.returncode != 0:
        raise GuardError("finalizer failed to request accepted service start")

    ready = False
    for attempt in range(readiness_attempts):
        active = run(steps[3], capture_output=True, text=True, timeout=30)
        if active.returncode == 0:
            health = run(steps[4], capture_output=True, text=True, timeout=30)
            if health.returncode == 0 and "ok" in health.stdout.lower():
                ready = True
                break
        if attempt + 1 < readiness_attempts:
            sleep(readiness_interval)
    if not ready:
        raise GuardError("accepted service did not become active and healthy")

    results = [run(command, capture_output=True, text=True, timeout=180)
               for command in steps[5:]]
    if any(result.returncode != 0 for result in results):
        raise GuardError("accepted-service validation command failed")
    if ACCEPTED_BINARY_SHA256 not in results[0].stdout:
        raise GuardError("accepted binary hash mismatch")
    if ACCEPTED_UNIT_SHA256 not in results[1].stdout:
        raise GuardError("accepted unit hash mismatch")
    if not results[2].stdout.strip().endswith("/xe"):
        raise GuardError("B60 is not bound to xe")
    if "BMG G21" not in results[3].stdout:
        raise GuardError("B60 Vulkan enumeration missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("preflight")
    preflight.add_argument("snapshot", type=Path)
    preflight.add_argument("--estimated-minutes", type=int, required=True)
    finalizer = sub.add_parser("finalize")
    finalizer.add_argument("--execute", action="store_true")
    finalizer.add_argument("--allow-production", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            payload = json.loads(args.snapshot.read_text(encoding="utf-8"))
            print(json.dumps(validate_preflight(payload, datetime.now(TZ), args.estimated_minutes), indent=2, sort_keys=True))
        elif not (args.execute and args.allow_production):
            print(json.dumps({"execution_authorized": False, "commands": commands()}, indent=2))
        else:
            execute_finalizer()
            print("accepted production service restored and validated")
    except (OSError, ValueError, GuardError, json.JSONDecodeError) as exc:
        print(f"guard failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
