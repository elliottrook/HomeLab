"""Persistent evaluation-owner identity process; never acquires a lease."""

from __future__ import annotations

import argparse
import json
import os
import signal
import time
from pathlib import Path

from stream_a_evaluation_watchdog import (
    IDENTITY_PATH, WatchdogIdentity, _read_root_json, _integer, _nonempty,
    owner_process_matches,
)


OWNER_INTENT_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/owner-intent.json")
OWNER_UNIT = "stream-a-evaluation-owner.service"
EXERCISE_OWNER_UNIT = "stream-a-evaluation-exercise-owner.service"
ALLOWED_OWNER_UNITS = frozenset((OWNER_UNIT, EXERCISE_OWNER_UNIT))
_running = True


def _stop(_signum, _frame):
    global _running
    _running = False


def _starttime_ticks(pid: int) -> int:
    raw = Path(f"/proc/{pid}/stat").read_text()
    return int(raw[raw.rfind(")") + 2:].split()[19])


def build_identity(intent_path: Path = OWNER_INTENT_PATH, *, pid: int | None = None,
                   required_uid: int = 0, unit: str = OWNER_UNIT) -> dict[str, object]:
    if unit not in ALLOWED_OWNER_UNITS:
        raise ValueError("owner unit is not an allowed fixed identity")
    value = _read_root_json(intent_path, {
        "lease_id", "generation", "heartbeat_timeout", "owner_id"},
        required_uid=required_uid)
    pid = os.getpid() if pid is None else pid
    return {
        "lease_id": _nonempty(value["lease_id"], "lease_id"),
        "generation": _integer(value["generation"], "generation"),
        "heartbeat_timeout": _integer(value["heartbeat_timeout"], "heartbeat_timeout"),
        "owner_id": _nonempty(value["owner_id"], "owner_id"),
        "pid": pid,
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "starttime_ticks": _starttime_ticks(pid),
        "cmdline": " ".join(Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode().split()),
        "unit": unit,
    }


def _as_watchdog_identity(value: dict[str, object]) -> WatchdogIdentity:
    return WatchdogIdentity(
        str(value["lease_id"]), int(value["generation"]),
        int(value["heartbeat_timeout"]), str(value["owner_id"]),
        int(value["pid"]), str(value["boot_id"]),
        int(value["starttime_ticks"]), str(value["cmdline"]),
        str(value["unit"]),
    )


def _write_identity(value: dict[str, object], path: Path = IDENTITY_PATH) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(temporary, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    parser.add_argument("--exercise-transient", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    if os.geteuid() != 0:
        return 1
    unit = EXERCISE_OWNER_UNIT if args.exercise_transient else OWNER_UNIT
    identity = build_identity(unit=unit)
    if not owner_process_matches(_as_watchdog_identity(identity)):
        return 1
    _write_identity(identity)
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    while _running:
        time.sleep(5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
