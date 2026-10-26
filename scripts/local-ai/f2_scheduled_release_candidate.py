"""Source-only two-phase F2 schedule coordinator.

The host timer is the clock.  Codex heartbeat observes the terminal state and
does not launch, retry, or extend a cycle.  This module never writes a receipt,
starts a lease, stops services, or calls a model.
"""

from __future__ import annotations

import json
import os
import re
import signal
import stat
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from f2_preflight_fixed_wrapper import (capture_fixed_preflight,
                                        run_fixed_final_guard)
from f2_preflight_snapshot import CLOCK, F2FinalGuardError, F2PreflightError

LOCAL_ZONE = ZoneInfo("America/Vancouver")
STATE_ROOT = Path("/var/lib/local-ai-lab/f2-scheduled")
OBSERVER = Path("/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py")
HARD_END_MINUTE = 100  # 01:40 Vancouver
PREPARE_MINUTE = 75  # 01:15 Vancouver
FINAL_MINUTE = 80  # 01:20 Vancouver
SCHEMA = "aster-f2-scheduled.v1"

FAILURE_CLASSES = frozenset({
    "WINDOW",
    "STATE_CONFLICT",
    "STATE_CUSTODY",
    "PREFLIGHT_FAILED",
    "FINAL_GUARD_FAILED",
    "OBSERVER_TIMEOUT",
    "OBSERVER_FAILED",
    "OBSERVER_OUTPUT_OVERSIZED",
    "OBSERVER_OUTPUT_INVALID",
    "OBSERVER_PROJECTION_INVALID",
    "FINAL_GUARD_SUBCHECK_FAILED",
    "FINAL_GUARD_CLOCK",
    "FINAL_GUARD_WINDOW",
    "FINAL_GUARD_LEASE_RECEIPT",
    "FINAL_GUARD_EXCLUSION",
    "FINAL_GUARD_LEASE_READY",
    "FINAL_GUARD_QUIET_PROCESSES",
    "FINAL_GUARD_LOAD",
    "FINAL_GUARD_INSTALLED_PIN",
    "FINAL_GUARD_SNAPSHOT_FLAGS",
    "FINAL_GUARD_CLOCK_MONOTONIC",
    "FINAL_GUARD_FRESHNESS",
    "OBSERVER_LAUNCH_FAILED",
    "OBSERVER_COMMUNICATION_FAILED",
    "OBSERVER_EXIT_NONZERO",
    "FINAL_FAILED",
    "UNKNOWN",
})


class ScheduledF2Error(ValueError):
    pass


class FinalSubcheckError(ScheduledF2Error):
    """Content-free classification for a bounded final subcheck failure."""

    def __init__(self, code: str, message: str):
        if code not in FAILURE_CLASSES:
            raise ValueError("final subcheck code is not bounded")
        super().__init__(message)
        self.code = code


def _root_custody(meta) -> bool:
    return meta.st_uid == 0 and meta.st_gid == 0


def _epoch(runner: Callable) -> int:
    code, output = runner(CLOCK, 3.0)
    if code != 0:
        raise ScheduledF2Error("host clock unavailable")
    try:
        return int(output.strip())
    except ValueError as exc:
        raise ScheduledF2Error("host clock invalid") from exc


def _cycle(epoch: int) -> tuple[str, int]:
    local = datetime.fromtimestamp(epoch, LOCAL_ZONE)
    return local.strftime("%Y-%m-%d"), local.hour * 60 + local.minute


def _state_path(cycle: str) -> Path:
    if len(cycle) != 10 or cycle[4] != "-" or cycle[7] != "-":
        raise ScheduledF2Error("cycle is invalid")
    return STATE_ROOT / f"{cycle}.json"


def _state_root() -> Path:
    try:
        meta = os.lstat(STATE_ROOT)
        if stat.S_ISLNK(meta.st_mode):
            raise ScheduledF2Error("scheduled state directory is a symlink")
        fd = os.open(STATE_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            meta = os.fstat(fd)
        finally:
            os.close(fd)
    except FileNotFoundError as exc:
        raise ScheduledF2Error("scheduled state directory is absent") from exc
    except OSError as exc:
        raise ScheduledF2Error("scheduled state directory is not a directory") from exc
    if (not stat.S_ISDIR(meta.st_mode) or not _root_custody(meta)
            or stat.S_IMODE(meta.st_mode) != 0o700):
        raise ScheduledF2Error("scheduled state directory custody differs")
    return STATE_ROOT


def _failure_class(phase: str, exc: BaseException) -> str:
    """Map internal failures to a bounded, content-free diagnostic code."""
    if isinstance(exc, FinalSubcheckError):
        return exc.code
    text = str(exc)
    if "outside the 01:15" in text or "outside the 01:20" in text:
        return "WINDOW"
    if "custody" in text or "state directory" in text:
        return "STATE_CUSTODY"
    if "cycle already" in text or "prepared state" in text:
        return "STATE_CONFLICT"
    if isinstance(exc, subprocess.TimeoutExpired) or "hard deadline" in text:
        return "OBSERVER_TIMEOUT"
    if "bounded observer returned" in text:
        return "OBSERVER_FAILED"
    if "projection is oversized" in text:
        return "OBSERVER_OUTPUT_OVERSIZED"
    if "projection is invalid" in text:
        return "OBSERVER_OUTPUT_INVALID"
    if "projection is incomplete" in text or "projection differs" in text:
        return "OBSERVER_PROJECTION_INVALID"
    if phase == "prepare":
        return "PREFLIGHT_FAILED"
    if "final gate" in text or "fixed F2" in text:
        return "FINAL_GUARD_FAILED"
    if phase == "final":
        return "FINAL_FAILED"
    return "UNKNOWN"


def _write_state(cycle: str, phase: str, state: str, error_class: str = "",
                 result: Optional[dict] = None, *,
                 first_failure_phase: str = "", failure_class: str = "") -> None:
    root = _state_root()
    path = root / f"{cycle}.json"
    if error_class not in FAILURE_CLASSES | {""} or failure_class not in FAILURE_CLASSES | {""}:
        raise ScheduledF2Error("failure class is not bounded")
    if first_failure_phase not in {"", "prepare", "final"}:
        raise ScheduledF2Error("failure phase is invalid")
    payload = {"schema": SCHEMA, "cycle": cycle, "phase": phase,
               "state": state, "error_class": error_class,
               "first_failure_phase": first_failure_phase,
               "failure_class": failure_class}
    if result is not None:
        payload["result"] = result
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(raw) > 16_384:
        raise ScheduledF2Error("scheduled state is oversized")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=root)
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short scheduled state write")
            view = view[written:]
        os.fsync(fd)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(fd)
    os.replace(temp_name, path)
    dir_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _existing_state(cycle: str) -> Optional[dict]:
    path = _state_path(cycle)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError:
        return None
    try:
        meta = os.fstat(fd)
        if (not stat.S_ISREG(meta.st_mode) or not _root_custody(meta)
                or meta.st_nlink != 1 or stat.S_IMODE(meta.st_mode) != 0o600
                or meta.st_size <= 0 or meta.st_size > 16_384):
            raise ScheduledF2Error("scheduled state custody differs")
        raw = os.read(fd, 16_385)
        if len(raw) > 16_384:
            raise ScheduledF2Error("scheduled state is oversized")
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScheduledF2Error("cycle state is unreadable") from exc
    finally:
        os.close(fd)
    if (not isinstance(value, dict) or value.get("schema") != SCHEMA
            or value.get("cycle") != cycle):
        raise ScheduledF2Error("cycle state is invalid")
    return value


def _record_failure(cycle: str, phase: str, exc: BaseException) -> dict:
    """Persist the first failure and never overwrite an earlier terminal no-go."""
    existing = _existing_state(cycle)
    if existing is not None and existing.get("state") == "no_go":
        return existing
    code = _failure_class(phase, exc)
    _write_state(cycle, phase, "no_go", code,
                 first_failure_phase=phase, failure_class=code)
    return _existing_state(cycle) or {
        "schema": SCHEMA, "cycle": cycle, "phase": phase,
        "state": "no_go", "error_class": code,
        "first_failure_phase": phase, "failure_class": code,
    }


def prepare(runner: Callable, *, clock: Callable[[], float] = time.time) -> dict:
    """Run the slow chain before 01:10 and persist one prepared state."""
    epoch = int(clock())
    cycle, minute = _cycle(epoch)
    try:
        if minute != PREPARE_MINUTE:
            raise ScheduledF2Error("prepare is outside the 01:15 window")
        if _existing_state(cycle) is not None:
            raise ScheduledF2Error("cycle already has terminal or prepared state")
        capture_fixed_preflight(runner)
        _write_state(cycle, "prepare", "prepared")
        return {"schema": SCHEMA, "cycle": cycle, "phase": "prepare", "state": "prepared"}
    except Exception as exc:
        try:
            _record_failure(cycle, "prepare", exc)
        except Exception:
            pass
        raise


def final(runner: Callable, *, popen=None,
          clock: Callable[[], float] = time.time) -> dict:
    """Run one fresh final gate and the existing bounded observer once."""
    epoch = int(clock())
    cycle, minute = _cycle(epoch)
    try:
        if minute != FINAL_MINUTE:
            raise ScheduledF2Error("final gate is outside the 01:20 window")
        if _existing_state(cycle) != {"schema": SCHEMA, "cycle": cycle,
                                      "phase": "prepare", "state": "prepared",
                                      "error_class": "", "first_failure_phase": "",
                                      "failure_class": ""}:
            raise ScheduledF2Error("prepared state is absent or not exact")
        try:
            run_fixed_final_guard(runner)
        except F2FinalGuardError as exc:
            raise FinalSubcheckError(exc.code, "final guard subcheck failed") from exc
        except Exception as exc:
            raise FinalSubcheckError("FINAL_GUARD_SUBCHECK_FAILED",
                                     "final guard subcheck failed") from exc
        local = datetime.fromtimestamp(epoch, LOCAL_ZONE)
        hard_end = local.replace(hour=1, minute=40, second=0, microsecond=0).timestamp()
        timeout = max(1, int(hard_end - epoch))
        try:
            launcher = subprocess.Popen if popen is None else popen
            process = launcher(("/usr/bin/python3", "-B", str(OBSERVER), "--read-only-authorized"),
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            start_new_session=True,
                            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(OBSERVER.parent),
                                 "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C"})
        except Exception as exc:
            raise FinalSubcheckError("OBSERVER_LAUNCH_FAILED",
                                     "bounded observer launch failed") from exc
        try:
            output, _ = process.communicate(timeout=max(1, timeout - 5))
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)
            raise ScheduledF2Error("bounded observer reached hard deadline") from exc
        except Exception as exc:
            raise FinalSubcheckError("OBSERVER_COMMUNICATION_FAILED",
                                     "bounded observer communication failed") from exc
        if process.returncode != 0:
            raise FinalSubcheckError("OBSERVER_EXIT_NONZERO",
                                     "bounded observer returned no-go")
        if len(output) > 8_192:
            raise ScheduledF2Error("bounded observer projection is oversized")
        try:
            projection = json.loads(output.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ScheduledF2Error("bounded observer projection is invalid") from exc
        _validate_projection(projection, cycle)
        value = {"schema": SCHEMA, "cycle": cycle, "phase": "final", "state": "complete",
                 "result": projection}
        _write_state(cycle, "final", "complete", result=projection)
        return value
    except Exception as exc:
        try:
            _record_failure(cycle, "final", exc)
        except Exception:
            pass
        raise


def _validate_projection(value: object, cycle: str) -> None:
    expected_date = cycle.replace("-", "_")
    fields = {"schema", "state", "date", "archives", "admission_receipt_written"}
    if (not isinstance(value, dict) or set(value) != fields
            or value.get("schema") != "aster-read-only-archive-timing.v1"
            or value.get("state") != "complete"
            or value.get("admission_receipt_written") is not False
            or value.get("date") != expected_date
            or not isinstance(value.get("archives"), list)
            or len(value["archives"]) != 3):
        raise ScheduledF2Error("bounded observer projection is incomplete")
    row_fields = {"vmid", "volid", "size", "ctime", "test_started_epoch",
                  "test_finished_epoch", "test_elapsed_ms", "test_exit"}
    for vmid, row in zip(("104", "110", "116"), value["archives"]):
        if (not isinstance(row, dict) or set(row) != row_fields or row.get("vmid") != vmid
                or not isinstance(row.get("volid"), str)
                or re.fullmatch(rf"backups:backup/vzdump-lxc-{vmid}-{expected_date}-\d{{2}}_\d{{2}}_\d{{2}}\.tar\.zst", row["volid"]) is None
                or any(type(row.get(key)) is not int for key in
                       ("size", "ctime", "test_started_epoch", "test_finished_epoch",
                        "test_elapsed_ms", "test_exit"))
                or row["size"] <= 0 or row["ctime"] <= 0 or row["test_exit"] != 0
                or row["test_elapsed_ms"] < 0
                or row["test_elapsed_ms"] > (900_000 if vmid == "110" else 120_000)
                or not row["ctime"] <= row["test_started_epoch"] <= row["test_finished_epoch"]):
            raise ScheduledF2Error("bounded observer projection differs")


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("prepare", "final"), required=True)
    args = parser.parse_args(argv)
    def runner(command, timeout):
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout, check=False)
        return result.returncode, result.stdout
    try:
        value = prepare(runner) if args.phase == "prepare" else final(runner)
        print(json.dumps(value, sort_keys=True))
        return 0
    except Exception as exc:
        failure_class = _failure_class(args.phase, exc)
        print(json.dumps({"schema": SCHEMA, "state": "no_go",
                          "phase": args.phase, "failure_class": failure_class}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
