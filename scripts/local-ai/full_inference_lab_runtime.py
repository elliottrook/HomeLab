"""Trusted wall-clock/monotonic owner wrapper for the full-drain candidate."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cooperative_lab_host_adapter import CooperativeHostObserver
from full_inference_lab_session import (FullDrainError, FullDrainPaths,
    FullInferenceDrainController)
from full_inference_lab_sources import (AcceptedBaseline,
    LocalProxmoxFullDrainSourceProducer, TrustedOwnerAttestation)
from full_inference_lab_validator import LocalProxmoxFullDrainValidator
from full_inference_lab_workload import lab_cleanup_command, lab_is_absent


@dataclass
class TrustedDrainOwner:
    owner_id: str
    wall_clock: Callable[[], float] = time.time
    monotonic: Callable[[], float] = time.monotonic
    _last_monotonic: float | None = None

    def assert_present(self) -> None:
        if not self.owner_id:
            raise FullDrainError("owner identity is empty")
        current = self.monotonic()
        if self._last_monotonic is not None and current < self._last_monotonic:
            raise FullDrainError("trusted monotonic clock moved backwards")
        self._last_monotonic = current

    def now_epoch(self) -> int:
        self.assert_present()
        return int(self.wall_clock())

    def heartbeat(self, controller: FullInferenceDrainController) -> None:
        controller.heartbeat(self.now_epoch())

    def require_work_window(self, controller: FullInferenceDrainController) -> None:
        controller.require_work_window(self.now_epoch())


def _host_runner(argv, timeout: float):
    result = subprocess.run(tuple(argv), capture_output=True, text=True,
                            timeout=timeout, check=False)
    return result.returncode, result.stdout


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("start", "heartbeat", "resume", "restore"), required=True)
    parser.add_argument("--state-root", type=Path, default=Path("/var/lib/local-ai-lab"))
    parser.add_argument("--cycle")
    parser.add_argument("--session-start-epoch", type=int)
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--admin-path-evidence", default="")
    parser.add_argument("--lease-id")
    parser.add_argument("--generation", type=int)
    parser.add_argument("--model-sha256")
    parser.add_argument("--binary-sha256")
    parser.add_argument("--unit-sha256")
    parser.add_argument("--effect-authorized", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Pinned host command; effects require an explicit per-invocation flag."""
    args = _parser().parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "not-attempted", "state": "disabled"}, sort_keys=True))
        return 0
    if args.phase == "start":
        required = (args.cycle, args.session_start_epoch, args.admin_path_evidence,
                    args.model_sha256, args.binary_sha256, args.unit_sha256)
        if any(value in (None, "") for value in required):
            raise SystemExit("start requires cycle, session start, admin evidence and three baseline hashes")
    if args.phase in {"heartbeat", "resume", "restore"} and (not args.lease_id or args.generation is None):
        raise SystemExit("this phase requires the exact lease id and generation")
    paths = FullDrainPaths(args.state_root)
    runner = _host_runner
    observer = CooperativeHostObserver(runner)
    if args.phase == "start":
        baseline = AcceptedBaseline(args.model_sha256, args.binary_sha256, args.unit_sha256)
        producer = LocalProxmoxFullDrainSourceProducer(
            runner, baseline, TrustedOwnerAttestation(args.owner_id, args.admin_path_evidence))
        preflight = producer.collect(cycle=args.cycle, session_start_epoch=args.session_start_epoch)
        validator = LocalProxmoxFullDrainValidator(runner, baseline, cycle=args.cycle)
        controller = FullInferenceDrainController(
            paths, lambda command: runner(command, 30.0), observer=observer,
            validator=validator, owner_id=args.owner_id, allow_effects=True)
        plan = controller.begin(preflight)
        print(json.dumps({"effects": "drained", "lease_id": plan.lease_id,
                          "generation": plan.generation}, sort_keys=True))
        return 0
    controller = FullInferenceDrainController(
        paths, lambda command: runner(command, 30.0), observer=observer,
        owner_id=args.owner_id, allow_effects=True)
    plan = controller.resume_existing(lease_id=args.lease_id, generation=args.generation)
    if args.phase == "heartbeat":
        TrustedDrainOwner(args.owner_id).heartbeat(controller)
        print(json.dumps({"effects": "heartbeat", "lease_id": plan.lease_id}, sort_keys=True))
        return 0
    if args.phase == "resume":
        print(json.dumps({"effects": "not-attempted", "state": "resumed",
                          "lease_id": plan.lease_id}, sort_keys=True))
        return 0
    required = (args.cycle, args.model_sha256, args.binary_sha256, args.unit_sha256)
    if any(value in (None, "") for value in required):
        raise SystemExit("restore requires cycle and three baseline hashes")
    validator = LocalProxmoxFullDrainValidator(
        runner, AcceptedBaseline(args.model_sha256, args.binary_sha256, args.unit_sha256), cycle=args.cycle)
    controller.validator = validator
    runner(lab_cleanup_command(lease_id=plan.lease_id,
                               generation=plan.generation), 30.0)
    if not lab_is_absent(runner, lease_id=plan.lease_id,
                         generation=plan.generation):
        raise SystemExit("lab scope/listener/process absence is unproven; lock retained")
    controller.restore(plan, now_epoch=int(time.time()), owner_present=True)
    print(json.dumps({"effects": "restored", "lease_id": plan.lease_id}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
