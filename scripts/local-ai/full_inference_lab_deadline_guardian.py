"""Offline one-shot deadline guardian for the bounded full-inference pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Callable, Sequence


class GuardianError(RuntimeError):
    pass


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


def run_guardian(*, state_path: Path, rescue_at: int, hard_deadline: int,
                 command: Sequence[str], clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict[str, object]:
    """Wait for the cutoff, then rescue only while the reserve remains."""
    if hard_deadline <= rescue_at:
        raise GuardianError("guardian hard deadline must follow rescue cutoff")
    while clock() < rescue_at:
        sleep(min(5.0, max(0.0, rescue_at - clock())))
    attempts = 0
    while clock() <= hard_deadline:
        if not state_path.exists():
            return {"state": "complete", "effects": "not-attempted"}
        attempts += 1
        result = runner(tuple(command), capture_output=True, text=True,
                        timeout=120, check=False)
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
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int)
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
    command = rescue_command(
        script=root / "full_inference_lab_runtime.py", state_root=args.state_root,
        owner_id=args.owner_id, lease_id=args.lease_id, generation=args.generation,
        cycle=args.cycle, model_sha256=args.model_sha256,
        binary_sha256=args.binary_sha256, unit_sha256=args.unit_sha256)
    result = run_guardian(
        state_path=args.state_root / "full-inference-drain.json",
        rescue_at=args.rescue_at, hard_deadline=args.hard_deadline, command=command)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
