"""Independent deadline/recovery boundary for the evaluation lease.

The default CLI path is inert.  A future installed watchdog must supply an
effect-authorized recovery adapter explicitly; otherwise it reports disabled
without reading or mutating lease state.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from evaluation_lease import watchdog_decision


@dataclass(frozen=True)
class WatchdogInput:
    lease_id: str
    generation: int
    phase: str
    heartbeat_epoch: int
    window_start_epoch: int
    hard_deadline_epoch: int
    restore_deadline_epoch: int


def load_watchdog_input(path: Path, *, expected_lease_id: str,
                        expected_generation: int, required_uid: int | None = None) -> WatchdogInput:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError("watchdog state custody is weak")
    if required_uid is not None and info.st_uid != required_uid:
        raise ValueError("watchdog state owner is unexpected")
    value = json.loads(path.read_text(encoding="utf-8"))
    result = WatchdogInput(
        value["lease_id"], value["generation"], value["phase"],
        value["heartbeat_epoch"], value["window_start_epoch"],
        value["hard_deadline_epoch"], value["restore_deadline_epoch"],
    )
    validate_watchdog_input(result, expected_lease_id=expected_lease_id,
                            expected_generation=expected_generation)
    return result


def validate_watchdog_input(value: WatchdogInput, *, expected_lease_id: str,
                            expected_generation: int) -> None:
    if (value.lease_id != expected_lease_id or value.generation != expected_generation
            or value.phase not in {"quiescing", "running", "restoring"}
            or value.heartbeat_epoch < value.window_start_epoch
            or value.hard_deadline_epoch != value.window_start_epoch + 75 * 60
            or value.restore_deadline_epoch != value.window_start_epoch + 90 * 60):
        raise ValueError("watchdog input is not bound to the expected durable lease")


def run_once(*, now_epoch: int, heartbeat_epoch: int, heartbeat_timeout: int,
             hard_deadline_epoch: int, restore_deadline_epoch: int,
             owner_present: bool, effect_authorized: bool,
             recovery: Callable[[], object] | None = None) -> dict[str, object]:
    decision = watchdog_decision(
        now_epoch=now_epoch, heartbeat_epoch=heartbeat_epoch,
        heartbeat_timeout=heartbeat_timeout,
        hard_deadline_epoch=hard_deadline_epoch,
        restore_deadline_epoch=restore_deadline_epoch,
        owner_present=owner_present,
    )
    if decision.action == "continue":
        return {"effects": "not-attempted", "decision": decision.reason}
    # The unbound API is intentionally incapable of recovery.  It remains as
    # a read-only diagnostic seam for old callers and tests.
    return {"effects": "disabled", "decision": decision.reason}


def run_bound_once(*, value: WatchdogInput, expected_lease_id: str,
                   expected_generation: int, now_epoch: int,
                   heartbeat_timeout: int, owner_present: bool,
                   effect_authorized: bool,
                   recovery: Callable[[], object] | None = None) -> dict[str, object]:
    """Run recovery only from a validated, identity-bound durable record."""
    validate_watchdog_input(value, expected_lease_id=expected_lease_id,
                            expected_generation=expected_generation)
    decision = watchdog_decision(
        now_epoch=now_epoch, heartbeat_epoch=value.heartbeat_epoch,
        heartbeat_timeout=heartbeat_timeout,
        hard_deadline_epoch=value.hard_deadline_epoch,
        restore_deadline_epoch=value.restore_deadline_epoch,
        owner_present=owner_present,
    )
    if decision.action == "continue" or not effect_authorized or recovery is None:
        return {"effects": "disabled" if decision.action != "continue" else "not-attempted",
                "decision": decision.reason}
    try:
        result = recovery()
    except Exception:
        return {"effects": "uncertain", "decision": decision.reason}
    return {"effects": "recovered", "decision": decision.reason, "result": result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    del args
    print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
