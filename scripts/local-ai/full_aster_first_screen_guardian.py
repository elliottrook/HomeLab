"""Independent deadline guardian for the full-Aster first screen."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import subprocess
import time
from typing import Callable

from full_aster_first_screen_observer import FixedObserver
from full_aster_first_screen_recovery import RecoveryIdentity, recover
from full_inference_lab_deadline_guardian import fence_owner_unit


class GuardianError(RuntimeError):
    pass


STATE = Path("/var/lib/local-ai-lab/full-aster-first-screen.json")
FULL_DRAIN_STATE = Path("/var/lib/local-ai-lab/full-inference-drain.json")


def _identity(screen_state: dict, drain_state: dict) -> RecoveryIdentity:
    required = {"schema", "phase", "owner_id", "owner_unit", "cycle",
                "model_sha256", "binary_sha256", "unit_sha256"}
    if (set(screen_state) != required
            or screen_state["schema"] != "aster-full-path-first-screen-live.v1"
            or screen_state["phase"] not in {"armed", "drained", "mounted", "candidate"}
            or drain_state.get("owner_id") != screen_state["owner_id"]):
        raise GuardianError("durable screen state is not exact")
    value = RecoveryIdentity(
        owner_id=screen_state["owner_id"], lease_id=drain_state.get("lease_id", ""),
        generation=drain_state.get("generation"), cycle=screen_state["cycle"],
        model_sha256=screen_state["model_sha256"],
        binary_sha256=screen_state["binary_sha256"],
        unit_sha256=screen_state["unit_sha256"])
    value.validate()
    return value


def run_guardian(*, state_path: Path, drain_state_path: Path,
                 owner_unit: str, rescue_at: int, hard_deadline: int,
                 clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 fence: Callable[[float], bool],
                 recoverer: Callable[[RecoveryIdentity], None]) -> dict[str, object]:
    if (not re.fullmatch(r"aster-full-screen-owner-[0-9a-f]{16}\.scope", owner_unit)
            or hard_deadline <= rescue_at
            or hard_deadline - rescue_at < 900):
        raise GuardianError("guardian identity or recovery reserve is invalid")
    if state_path.exists():
        raise GuardianError("screen state already exists when guardian is armed")
    while clock() < rescue_at:
        sleep(min(5.0, max(0.0, rescue_at - clock())))
    if not state_path.exists():
        return {"state": "complete", "effects": "not-attempted"}
    remaining = hard_deadline - clock()
    if remaining <= 0 or not fence(remaining):
        raise GuardianError("owner scope could not be fenced before recovery")
    if not drain_state_path.exists():
        raise GuardianError("full-drain state is absent during screen recovery")
    screen = json.loads(state_path.read_text(encoding="utf-8"))
    drain = json.loads(drain_state_path.read_text(encoding="utf-8"))
    identity = _identity(screen, drain)
    recoverer(identity)
    if state_path.exists() or drain_state_path.exists():
        raise GuardianError("recovery did not clear durable state")
    return {"state": "rescued", "effects": "restored"}


def _command_runner(command, timeout):
    result = subprocess.run(tuple(command), capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode != 0:
        raise GuardianError("fixed recovery command failed")


def _recover_and_clear(identity: RecoveryIdentity) -> None:
    recover(identity=identity, observer=FixedObserver(), runner=_command_runner)
    if FULL_DRAIN_STATE.exists():
        raise GuardianError("full-drain rescue retained its state")
    STATE.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-unit", required=True)
    parser.add_argument("--rescue-at", type=int, required=True)
    parser.add_argument("--hard-deadline", type=int, required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"state": "disabled", "effects": "not-attempted"}, sort_keys=True))
        return 0
    result = run_guardian(
        state_path=STATE, drain_state_path=FULL_DRAIN_STATE,
        owner_unit=args.owner_unit, rescue_at=args.rescue_at,
        hard_deadline=args.hard_deadline,
        fence=lambda budget: fence_owner_unit(args.owner_unit, budget),
        recoverer=_recover_and_clear)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
