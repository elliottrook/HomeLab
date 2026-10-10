#!/usr/bin/env python3
"""One-shot, owner-armed Companion interruption experiment; never starts a turn.

This is deliberately outside the app bundle. It observes only the private
content-free manual request record and dispatch journal. It signals only a
specific, verified Companion PID after the new request has a recorded turn ID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import stat
import subprocess
import sys
import time


EXPECTED_APP = "/Applications/AsterCompanion.app/Contents/MacOS/AsterCompanion"
EXPECTED_HASH = "f83ed9fe74c33222beb39a73519644c5b6fd796e991e6f0f6c598cca950936b1"
EXPECTED_MANIFEST = "483062186349703ee472b51323c88fb4ffa1f780ae9ff6f351d4046da4973392"
REQUEST_RE = re.compile(r"^request-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
TERMINAL = {"completed", "failed", "interrupted"}


def private_regular(path: Path, *, max_bytes: int | None = None) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError("Expected owner-only regular file")
    if max_bytes is not None and not 0 < info.st_size <= max_bytes:
        raise ValueError("Unexpected private-record size")


def private_directory(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError("Expected owner-only state directory")


def process_matches(pid: int) -> bool:
    result = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                            capture_output=True, text=True, check=False)
    return result.returncode == 0 and result.stdout.strip() == (
        EXPECTED_APP + " --aster-local-codex-manual"
    )


def executable_matches() -> bool:
    digest = hashlib.sha256(Path(EXPECTED_APP).read_bytes()).hexdigest()
    return digest == EXPECTED_HASH


def read_pending(path: Path) -> str | None:
    try:
        private_regular(path, max_bytes=512)
    except FileNotFoundError:
        return None
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        record = json.loads(os.read(descriptor, 513))
    finally:
        os.close(descriptor)
    request_id = record.get("requestID") if isinstance(record, dict) else None
    if not isinstance(request_id, str) or not REQUEST_RE.fullmatch(request_id):
        raise ValueError("Invalid manual request identifier")
    if record.get("manifestSHA256") != EXPECTED_MANIFEST:
        raise ValueError("Manual request manifest changed")
    return request_id


def read_rows(path: Path) -> dict[str, tuple[str, str | None]]:
    private_regular(path)
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=1)
    try:
        return {job_id: (state, turn_id) for job_id, state, turn_id in
                connection.execute("SELECT job_id,state,turn_id FROM jobs")}
    finally:
        connection.close()


def decision(baseline: set[str], pending_id: str | None,
             rows: dict[str, tuple[str, str | None]]) -> str:
    """Pure decision; only `signal` authorizes a later exact-PID SIGTERM."""
    new_ids = set(rows) - baseline
    if not pending_id:
        return "wait" if not new_ids else "abort_unexpected_job"
    if pending_id in baseline or len(new_ids) > 1 or new_ids - {pending_id}:
        return "abort_unexpected_job"
    row = rows.get(pending_id)
    if row is None:
        return "wait"
    state, turn_id = row
    if state == "running" and turn_id:
        return "signal"
    if state in TERMINAL:
        return "completed_before_interrupt"
    if state in {"dispatch_unknown", "running"} and not turn_id:
        return "wait"
    return "abort_uncertain_state"


def run(state_dir: Path, pid: int, timeout: float, armed: bool) -> dict[str, object]:
    private_directory(state_dir)
    db = state_dir / "jobs.sqlite"
    pending = state_dir / "manual-pending.json"
    if read_pending(pending) is not None:
        raise ValueError("A prior manual request is still saved; do not clear it here")
    if not executable_matches() or not process_matches(pid):
        raise ValueError("Exact signed-candidate executable or flagged process mismatch")
    initial = read_rows(db)
    if any(state not in TERMINAL for state, _ in initial.values()):
        raise ValueError("A dispatch is already pending")
    baseline = set(initial)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        request_id = read_pending(pending)
        outcome = decision(baseline, request_id, read_rows(db))
        if outcome == "wait":
            time.sleep(0.05)
            continue
        if outcome == "signal":
            if not armed:
                return {"outcome": "would_signal", "request_id": request_id,
                        "signal_sent": False}
            if not process_matches(pid) or not executable_matches():
                raise ValueError("Process changed before interruption")
            os.kill(pid, signal.SIGTERM)
            return {"outcome": "signalled_on_observed_running",
                    "request_id": request_id, "signal_sent": True}
        return {"outcome": outcome, "request_id": request_id,
                "signal_sent": False}
    return {"outcome": "timeout_without_eligible_turn", "signal_sent": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=45)
    parser.add_argument("--arm", action="store_true",
                        help="Send SIGTERM to the exact flagged Companion PID if eligible")
    args = parser.parse_args()
    if args.pid <= 1 or not 1 <= args.timeout_seconds <= 60:
        parser.error("Invalid PID or timeout")
    try:
        print(json.dumps(run(args.state_dir, args.pid, args.timeout_seconds, args.arm),
                         sort_keys=True))
        return 0
    except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(json.dumps({"outcome": "preflight_or_runtime_abort",
                          "reason": type(error).__name__, "signal_sent": False}),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
