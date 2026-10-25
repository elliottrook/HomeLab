"""Independent deadline/recovery boundary for the evaluation lease.

The default CLI path is inert.  A future installed watchdog must supply an
effect-authorized recovery adapter explicitly; otherwise it reports disabled
without reading or mutating lease state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from evaluation_lease import (
    EFFECT_DEADLINE_SECONDS,
    EXERCISE_HARD_DEADLINE_SECONDS,
    EXERCISE_MARKER,
    EXERCISE_MODE,
    EXERCISE_RESTORE_DEADLINE_SECONDS,
    LEASE_MODE,
    WINDOW_SECONDS,
    watchdog_decision,
)
from evaluation_lease_adapter import read_state


@dataclass(frozen=True)
class WatchdogInput:
    lease_id: str
    generation: int
    lease_mode: str
    exercise_marker: str | None
    phase: str
    heartbeat_epoch: int
    window_start_epoch: int
    hard_deadline_epoch: int
    restore_deadline_epoch: int


def load_watchdog_input(path: Path, *, expected_lease_id: str,
                        expected_generation: int, required_uid: int | None = None) -> WatchdogInput:
    import os
    if required_uid is not None and required_uid != os.geteuid():
        raise ValueError("watchdog state owner is unexpected")
    state = read_state(path, expected_lease_id=expected_lease_id,
                       expected_generation=expected_generation)
    result = WatchdogInput(
        state.lease_id, state.generation, state.lease_mode,
        state.exercise_marker, state.phase,
        state.heartbeat_epoch, state.window_start_epoch,
        state.hard_deadline_epoch, state.restore_deadline_epoch,
    )
    validate_watchdog_input(result, expected_lease_id=expected_lease_id,
                            expected_generation=expected_generation)
    return result


def validate_watchdog_input(value: WatchdogInput, *, expected_lease_id: str,
                            expected_generation: int) -> None:
    if (value.lease_id != expected_lease_id or value.generation != expected_generation
            or value.heartbeat_epoch < value.window_start_epoch):
        raise ValueError("watchdog input is not bound to the expected durable lease")
    if value.lease_mode == LEASE_MODE:
        valid = (
            value.exercise_marker is None
            and value.phase in {"prepared", "quiescing", "running", "restoring"}
            and value.hard_deadline_epoch
            == value.window_start_epoch + EFFECT_DEADLINE_SECONDS
            and value.restore_deadline_epoch
            == value.window_start_epoch + WINDOW_SECONDS
        )
    elif value.lease_mode == EXERCISE_MODE:
        valid = (
            value.exercise_marker == EXERCISE_MARKER
            and value.phase == "prepared"
            and value.hard_deadline_epoch
            == value.window_start_epoch + EXERCISE_HARD_DEADLINE_SECONDS
            and value.restore_deadline_epoch
            == value.window_start_epoch + EXERCISE_RESTORE_DEADLINE_SECONDS
        )
    else:
        valid = False
    if not valid:
        raise ValueError("watchdog input lease mode, marker, phase or deadline is invalid")


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
    return {"effects": "disabled", "decision": "in-memory-diagnostic"}


def run_bound_from_state(*, path: Path, expected_lease_id: str,
                         expected_generation: int, now_epoch: int,
                         heartbeat_timeout: int, owner_present: bool,
                         effect_authorized: bool,
                         recovery: Callable[[], object] | None = None) -> dict[str, object]:
    """Effect-capable path: read the durable descriptor before recovery."""
    value = load_watchdog_input(path, expected_lease_id=expected_lease_id,
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
