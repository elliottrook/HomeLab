"""Source-only two-phase F2 schedule coordinator.

The host timer is the clock.  Codex heartbeat observes the terminal state and
does not launch, retry, or extend a cycle.  This module never writes a receipt,
starts a lease, stops services, or calls a model.
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from f2_preflight_fixed_wrapper import (capture_fixed_preflight,
                                        run_fixed_final_guard)
from f2_preflight_snapshot import CLOCK, F2PreflightError

LOCAL_ZONE = ZoneInfo("America/Vancouver")
STATE_ROOT = Path("/var/lib/local-ai-lab/f2-scheduled")
OBSERVER = Path("/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py")
HARD_END_MINUTE = 100  # 01:40 Vancouver
SCHEMA = "aster-f2-scheduled.v1"


class ScheduledF2Error(ValueError):
    pass


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


def _write_state(cycle: str, phase: str, state: str, error_class: str = "") -> None:
    path = _state_path(cycle)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {"schema": SCHEMA, "cycle": cycle, "phase": phase,
               "state": state, "error_class": error_class}
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    temp.chmod(0o600)
    temp.replace(path)


def _existing_state(cycle: str) -> Optional[dict]:
    path = _state_path(cycle)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScheduledF2Error("cycle state is unreadable") from exc
    if (not isinstance(value, dict) or value.get("schema") != SCHEMA
            or value.get("cycle") != cycle):
        raise ScheduledF2Error("cycle state is invalid")
    return value


def prepare(runner: Callable, *, clock: Callable[[], float] = time.time) -> dict:
    """Run the slow chain before 01:10 and persist one prepared state."""
    epoch = int(clock())
    cycle, minute = _cycle(epoch)
    try:
        if not 60 <= minute < 70:
            raise ScheduledF2Error("prepare is outside the 01:00-01:09 window")
        if _existing_state(cycle) is not None:
            raise ScheduledF2Error("cycle already has terminal or prepared state")
        capture_fixed_preflight(runner)
        _write_state(cycle, "prepare", "prepared")
        return {"schema": SCHEMA, "cycle": cycle, "phase": "prepare", "state": "prepared"}
    except Exception as exc:
        try:
            _write_state(cycle, "prepare", "no_go", type(exc).__name__)
        except Exception:
            pass
        raise


def final(runner: Callable, *, popen=subprocess.run,
          clock: Callable[[], float] = time.time) -> dict:
    """Run one fresh final gate and the existing bounded observer once."""
    epoch = int(clock())
    cycle, minute = _cycle(epoch)
    try:
        if not 70 <= minute < 80:
            raise ScheduledF2Error("final gate is outside the 01:10-01:19 window")
        if _existing_state(cycle) != {"schema": SCHEMA, "cycle": cycle,
                                      "phase": "prepare", "state": "prepared",
                                      "error_class": ""}:
            raise ScheduledF2Error("prepared state is absent or not exact")
        run_fixed_final_guard(runner)
        local = datetime.fromtimestamp(epoch, LOCAL_ZONE)
        hard_end = local.replace(hour=1, minute=40, second=0, microsecond=0).timestamp()
        timeout = max(1, int(hard_end - epoch))
        result = popen(("/usr/bin/python3", "-B", str(OBSERVER), "--read-only-authorized"),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=timeout, check=False,
                       env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(OBSERVER.parent),
                            "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C"})
        if result.returncode != 0:
            raise ScheduledF2Error("bounded observer returned no-go")
        value = {"schema": SCHEMA, "cycle": cycle, "phase": "final", "state": "complete"}
        _write_state(cycle, "final", "complete")
        return value
    except Exception as exc:
        try:
            _write_state(cycle, "final", "no_go", type(exc).__name__)
        except Exception:
            pass
        raise


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
        print(json.dumps({"schema": SCHEMA, "state": "no_go",
                          "error_class": type(exc).__name__}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
