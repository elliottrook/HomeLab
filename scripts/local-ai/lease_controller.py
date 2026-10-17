#!/usr/bin/env python3
"""Manual Proxmox-side controller for the Local AI lab lease.

The controller is intentionally unscheduled.  ``acquire --light`` is the
bounded live test mode: it drains only the three Local AI production services
and leaves unrelated guests untouched.  Full guest draining and host restart
remain explicit future operations under the same lease contract.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/var/lib/local-ai-lab")
LOCK = ROOT / "lease.lock"
STATE = ROOT / "lease.json"
CHECKPOINTS = ROOT / "checkpoints"
CONTROL_PLANE = (
    "pve-cluster",
    "pvedaemon",
    "pvestatd",
    "pveproxy",
    "ssh",
    "networking",
    "nut-monitor",
)
AI_SERVICES = (
    (104, "aster-agent.service"),
    (110, "aster-llama.service"),
    (116, "aster-speech.service"),
)


class LeaseFailure(RuntimeError):
    pass


@contextmanager
def archive_observation_exclusion():
    """Share the installed observer's nonblocking directory advisory lock.

    The manual entrypoint lives in /usr/local/sbin, outside the candidate
    module's import root, so it verifies and locks the same directory itself.
    This guards acquisition only; its old state schema remains unsuitable for
    the independently supervised full-stop drill.
    """
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(ROOT, flags)
    except OSError as exc:
        raise LeaseFailure("host exclusion directory is unavailable") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o700):
            raise LeaseFailure("host exclusion directory custody is invalid")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LeaseFailure("host exclusion is held or unavailable") from exc
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def run(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, text=True, capture_output=True)
    if check and result.returncode:
        raise LeaseFailure(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_root() -> None:
    if os.geteuid() != 0:
        raise LeaseFailure("must run as root on the Proxmox host")
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    CHECKPOINTS.mkdir(mode=0o700, parents=True, exist_ok=True)


def control_plane_health() -> dict[str, str]:
    health = {}
    for unit in CONTROL_PLANE:
        value = run("systemctl", "is-active", unit, check=False) or "unknown"
        health[unit] = value
    failed = [unit for unit, value in health.items() if value != "active"]
    if failed:
        raise LeaseFailure("control-plane survival check failed: " + ", ".join(failed))
    return health


def backup_activity() -> str:
    return run("pgrep", "-af", "vzdump|rsync|pbs-client", check=False)


def guest_service_state() -> dict[str, str]:
    state = {}
    for vmid, unit in AI_SERVICES:
        value = run("pct", "exec", str(vmid), "--", "systemctl", "is-active", unit, check=False) or "unknown"
        state[f"{vmid}:{unit}"] = value
    return state


def acquire(args: argparse.Namespace) -> None:
    ensure_root()
    with archive_observation_exclusion():
        _acquire_locked(args)


def _acquire_locked(args: argparse.Namespace) -> None:
    if not args.light:
        raise LeaseFailure("only --light is enabled for this bounded live test")
    if not args.backup_verified:
        raise LeaseFailure("--backup-verified is required; the operator must confirm the completed backup chain")
    if not args.test_window:
        raise LeaseFailure("this manual test is outside the scheduled window; pass --test-window explicitly")
    if STATE.exists():
        raise LeaseFailure("an active lease state already exists")
    if LOCK.exists():
        raise LeaseFailure("lease lock already exists")
    if backup_activity():
        raise LeaseFailure("backup or rsync activity is still running")

    health = control_plane_health()
    services = guest_service_state()
    checkpoint_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint = {
        "created_at": now(),
        "control_plane": health,
        "services": services,
        "backup_verified_by_operator": True,
        "mode": "light-service-drain",
    }
    checkpoint_path = CHECKPOINTS / f"{checkpoint_id}.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2) + "\n")
    checkpoint_path.chmod(0o600)
    LOCK.mkdir(mode=0o700)
    try:
        for key, value in services.items():
            if value == "active":
                vmid, unit = key.split(":", 1)
                run("pct", "exec", vmid, "--", "systemctl", "stop", unit)
        state = {
            "state": "leased",
            "acquired_at": now(),
            "mode": "light-service-drain",
            "checkpoint": str(checkpoint_path),
            "services": [key for key, value in services.items() if value == "active"],
            "reboot_permitted": False,
            "scheduler_enabled": False,
        }
        STATE.write_text(json.dumps(state, indent=2) + "\n")
        STATE.chmod(0o600)
    except Exception:
        for key, value in services.items():
            if value == "active":
                vmid, unit = key.split(":", 1)
                run("pct", "exec", vmid, "--", "systemctl", "start", unit, check=False)
        LOCK.rmdir()
        raise
    print(json.dumps({"ok": True, **state}, indent=2))


def release() -> None:
    ensure_root()
    if not STATE.exists() or not LOCK.exists():
        raise LeaseFailure("no active lease state and lock found")
    state = json.loads(STATE.read_text())
    if state.get("state") != "leased":
        raise LeaseFailure("lease state is not leased")
    state["state"] = "restoring"
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    for key in state.get("services", []):
        vmid, unit = key.split(":", 1)
        run("pct", "exec", vmid, "--", "systemctl", "start", unit)
    health = control_plane_health()
    services = guest_service_state()
    failed = [key for key in state.get("services", []) if services.get(key) != "active"]
    if failed:
        raise LeaseFailure("production health gate failed; lease retained: " + ", ".join(failed))
    state.update({"state": "ready", "released_at": now(), "control_plane": health, "services_after": services})
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    STATE.unlink()
    LOCK.rmdir()
    print(json.dumps({"ok": True, **state}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire_parser = sub.add_parser("acquire")
    acquire_parser.add_argument("--light", action="store_true")
    acquire_parser.add_argument("--backup-verified", action="store_true")
    acquire_parser.add_argument("--test-window", action="store_true")
    sub.add_parser("release")
    sub.add_parser("status")
    args = parser.parse_args()
    try:
        if args.command == "acquire":
            acquire(args)
        elif args.command == "release":
            release()
        else:
            print(STATE.read_text() if STATE.exists() else json.dumps({"state": "ready"}, indent=2))
        return 0
    except (LeaseFailure, OSError, json.JSONDecodeError) as exc:
        print(f"lease-controller: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
