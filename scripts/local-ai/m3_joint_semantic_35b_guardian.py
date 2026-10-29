"""Independent mount-aware deadline guardian for the booked M3 transaction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from full_aster_first_screen_observer import (
    BINARY_SHA256, MODEL_SHA256, UNIT_SHA256, FixedObserver,
)
from full_aster_first_screen_recovery import RecoveryIdentity, recover
from full_inference_lab_deadline_guardian import fence_owner_unit


STATE = Path("/var/lib/local-ai-lab/full-inference-drain.json")


class GuardianError(RuntimeError):
    pass


def identity(value: dict, *, owner_id: str, cycle: str) -> RecoveryIdentity:
    lease_id = value.get("lease_id")
    generation = value.get("generation")
    if (value.get("owner_id") != owner_id or value.get("mode") != "full-inference-drain-v1"
            or value.get("phase") not in {"armed", "drained"}
            or not isinstance(lease_id, str) or not lease_id.startswith(owner_id + ":")
            or type(generation) is not int):
        raise GuardianError("M3 durable lease identity is invalid")
    result = RecoveryIdentity(owner_id, lease_id, generation, cycle,
                              MODEL_SHA256, BINARY_SHA256, UNIT_SHA256)
    result.validate()
    return result


def run(*, owner_id: str, owner_unit: str, cycle: str,
        rescue_at: int, hard_deadline: int, state_path: Path = STATE,
        clock=time.time, sleep=time.sleep, fence=fence_owner_unit,
        recoverer=None) -> dict[str, object]:
    if hard_deadline - rescue_at < 900:
        raise GuardianError("M3 recovery reserve is insufficient")
    while clock() < rescue_at:
        sleep(min(5.0, max(0.0, rescue_at - clock())))
    if not state_path.exists():
        return {"state": "complete", "effects": "not-attempted"}
    if not fence(owner_unit, max(0.0, hard_deadline - clock())):
        raise GuardianError("M3 owner scope could not be fenced")
    value = json.loads(state_path.read_text(encoding="utf-8"))
    recovery_identity = identity(value, owner_id=owner_id, cycle=cycle)
    if recoverer is None:
        def command(argv, timeout):
            result = subprocess.run(tuple(argv), capture_output=True, text=True,
                                    timeout=timeout, check=False)
            if result.returncode != 0:
                raise GuardianError("M3 fixed recovery command failed")
        recover(identity=recovery_identity, observer=FixedObserver(), runner=command)
    else:
        recoverer(recovery_identity)
    if state_path.exists():
        raise GuardianError("M3 recovery retained durable lease state")
    return {"state": "rescued", "effects": "restored"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--owner-unit", required=True)
    parser.add_argument("--cycle", required=True)
    parser.add_argument("--rescue-at", type=int, required=True)
    parser.add_argument("--hard-deadline", type=int, required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"state": "disabled", "effects": "not-attempted"}, sort_keys=True))
        return 0
    value = run(owner_id=args.owner_id, owner_unit=args.owner_unit, cycle=args.cycle,
                rescue_at=args.rescue_at, hard_deadline=args.hard_deadline)
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

