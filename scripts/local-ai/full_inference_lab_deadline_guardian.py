"""Offline one-shot deadline guardian for the bounded full-inference pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import re
from typing import Callable, Sequence


class GuardianError(RuntimeError):
    pass


def fence_owner_unit(unit: str, budget: float,
                     runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
                     monotonic: Callable[[], float] = time.monotonic) -> bool:
    """Stop the exact owner scope and require it to be inactive before rescue."""
    if not re.fullmatch(r"aster-local-ai-pilot-owner-[A-Za-z0-9_-]+\.scope", unit):
        raise GuardianError("owner unit identity is outside the fixed pilot scope")
    if budget <= 0:
        return False
    deadline = monotonic() + budget
    def call(command: tuple[str, ...], maximum: float):
        remaining = deadline - monotonic()
        if remaining <= 0:
            return None
        return runner(command, capture_output=True, text=True,
                      timeout=min(maximum, remaining), check=False)
    call(("systemctl", "stop", unit), 30.0)
    state = call(("systemctl", "is-active", unit), 10.0)
    if state is None:
        return False
    detail = f"{state.stdout}\n{state.stderr}".lower()
    if state.returncode == 0:
        return False
    tasks = call(("systemctl", "show", unit, "--property=TasksCurrent", "--value"), 10.0)
    main_pid = call(("systemctl", "show", unit, "--property=MainPID", "--value"), 10.0)
    if tasks is None or main_pid is None:
        return False
    if (tasks.returncode == 0 and tasks.stdout.strip() == "0"
            and main_pid.returncode == 0 and main_pid.stdout.strip() == "0"):
        return True
    return (any(marker in detail for marker in ("unknown", "not found", "not-found"))
            and tasks.returncode != 0 and main_pid.returncode != 0)


def rescue_command(*, script: Path, state_root: Path, owner_id: str,
                   lease_id: str, generation: int, cycle: str,
                   model_sha256: str, binary_sha256: str,
                   unit_sha256: str) -> tuple[str, ...]:
    return (sys.executable, "-B", str(script), "--phase", "rescue",
            "--state-root", str(state_root), "--owner-id", owner_id,
            "--lease-id", lease_id, "--generation", str(generation),
            "--cycle", cycle, "--model-sha256", model_sha256,
            "--binary-sha256", binary_sha256, "--unit-sha256", unit_sha256,
            "--effect-authorized")


def _discover_identity(state_path: Path, owner_id: str) -> tuple[str, int]:
    value = json.loads(state_path.read_text(encoding="utf-8"))
    lease_id = value.get("lease_id")
    generation = value.get("generation")
    if (value.get("owner_id") != owner_id
            or value.get("mode") != "full-inference-drain-v1"
            or not isinstance(lease_id, str)
            or not lease_id.startswith(owner_id + ":")
            or not lease_id[len(owner_id) + 1:].isdigit()
            or type(generation) is not int or generation < 1
            or value.get("phase") not in {"armed", "drained"}):
        raise GuardianError("durable state is not the armed pilot lease")
    return lease_id, generation


def run_guardian(*, state_path: Path, owner_id: str, owner_fence: Callable[[], bool],
                 rescue_command_factory: Callable[[str, int], Sequence[str]],
                 rescue_at: int, hard_deadline: int, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict[str, object]:
    """Wait for the cutoff, then rescue only while the reserve remains."""
    if hard_deadline <= rescue_at:
        raise GuardianError("guardian hard deadline must follow rescue cutoff")
    if state_path.exists():
        raise GuardianError("durable state already exists when guardian is armed")
    while clock() < rescue_at:
        sleep(min(5.0, max(0.0, rescue_at - clock())))
    attempts = 0
    fenced = False
    while clock() <= hard_deadline:
        if not state_path.exists():
            return {"state": "complete", "effects": "not-attempted"}
        attempts += 1
        if not fenced:
            remaining = max(0.0, hard_deadline - clock())
            if remaining <= 0 or not owner_fence(remaining):
                raise GuardianError("owner scope could not be fenced before rescue")
            fenced = True
        lease_id, generation = _discover_identity(state_path, owner_id)
        remaining = max(0.0, hard_deadline - clock())
        if remaining <= 0:
            break
        result = runner(tuple(rescue_command_factory(lease_id, generation)), capture_output=True, text=True,
                        timeout=min(120.0, remaining), check=False)
        if result.returncode == 0 and not state_path.exists():
            return {"state": "rescued", "effects": "restored", "attempts": attempts}
        if clock() >= hard_deadline:
            break
        sleep(min(30.0, max(0.0, hard_deadline - clock())))
    raise GuardianError("deadline rescue did not clear durable pilot state")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--owner-unit", required=True)
    parser.add_argument("--cycle", required=True)
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--binary-sha256", required=True)
    parser.add_argument("--unit-sha256", required=True)
    parser.add_argument("--rescue-at", required=True, type=int)
    parser.add_argument("--hard-deadline", required=True, type=int)
    parser.add_argument("--effect-authorized", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "not-attempted", "state": "disabled"}, sort_keys=True))
        return 0
    root = Path(__file__).resolve().parent
    result = run_guardian(
        state_path=args.state_root / "full-inference-drain.json", owner_id=args.owner_id,
        owner_fence=lambda budget: fence_owner_unit(args.owner_unit, budget),
        rescue_command_factory=lambda lease_id, generation: rescue_command(
            script=root / "full_inference_lab_runtime.py", state_root=args.state_root,
            owner_id=args.owner_id, lease_id=lease_id, generation=generation,
            cycle=args.cycle, model_sha256=args.model_sha256,
            binary_sha256=args.binary_sha256, unit_sha256=args.unit_sha256),
        rescue_at=args.rescue_at, hard_deadline=args.hard_deadline)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
