"""Trusted wall-clock/monotonic owner wrapper for the full-drain candidate."""

from __future__ import annotations

import argparse
import json
import os
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
from full_inference_lab_supervisor import (GpuUser, PersistentFullDrainSupervisor,
                                            SupervisorError)
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


def _gpu_users() -> frozenset[GpuUser]:
    """Read render-node holders directly; inspection errors are not absence."""
    users: set[GpuUser] = set()
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(proc.name)
            matched = False
            for fd in (proc / "fd").iterdir():
                try:
                    if os.readlink(fd) == "/dev/dri/renderD128":
                        matched = True
                        break
                except FileNotFoundError:
                    continue
                except PermissionError as exc:
                    raise SupervisorError("GPU fd observation was not permitted") from exc
            if not matched:
                continue
            stat = (proc / "stat").read_text(encoding="ascii")
            starttime = int(stat.rsplit(")", 1)[1].split()[19])
            cgroup = (proc / "cgroup").read_text(encoding="utf-8").strip()
            executable = os.readlink(proc / "exe")
            users.add(GpuUser(pid, starttime, cgroup, executable))
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as exc:
            raise SupervisorError("GPU user observation failed") from exc
    return frozenset(users)


def _production_masked(runner: Callable[..., tuple[int, str]]) -> bool:
    active = runner(("pct", "exec", "110", "--", "systemctl", "is-active",
                     "aster-llama.service"), 5.0)
    enabled = runner(("pct", "exec", "110", "--", "systemctl", "is-enabled",
                      "aster-llama.service"), 5.0)
    return active[0] != 0 and enabled[1].strip() in {"masked", "masked-runtime"}


def _accepted_gpu_baseline(users: frozenset[GpuUser]) -> frozenset[GpuUser]:
    """Validate production identity, then require no holders after drain."""
    if len(users) > 1 or any(not user.executable.endswith(
            "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server")
            or not user.cgroup.endswith(
                "/lxc/110/ns/system.slice/aster-llama.service")
            for user in users):
        raise SupervisorError("pre-existing GPU holder is outside the accepted production identity")
    return frozenset()


def _run_pilot(args: argparse.Namespace, paths: FullDrainPaths, *,
               runner: Callable[..., tuple[int, str]] = _host_runner,
               gpu_users: Callable[[], frozenset[GpuUser]] = _gpu_users,
               wall_clock: Callable[[], float] = time.time) -> int:
    baseline = AcceptedBaseline(args.model_sha256, args.binary_sha256, args.unit_sha256)
    producer = LocalProxmoxFullDrainSourceProducer(
        runner, baseline, TrustedOwnerAttestation(args.owner_id, args.admin_path_evidence),
        wall_clock=wall_clock)
    preflight = producer.collect(cycle=args.cycle, session_start_epoch=args.session_start_epoch)
    controller = FullInferenceDrainController(
        paths, lambda command: runner(command, 30.0), observer=CooperativeHostObserver(runner),
        validator=LocalProxmoxFullDrainValidator(runner, baseline, cycle=args.cycle),
        owner_id=args.owner_id, allow_effects=True)
    allowed_gpu_users = _accepted_gpu_baseline(gpu_users())
    current_plan: dict[str, object] = {}

    def lab_absent() -> bool:
        plan = current_plan.get("plan")
        if plan is None:
            return True
        return lab_is_absent(runner, lease_id=plan.lease_id, generation=plan.generation)

    supervisor = PersistentFullDrainSupervisor(
        controller, workload_runner=runner,
        production_masked=lambda: _production_masked(runner),
        lab_absent=lab_absent, gpu_users=gpu_users,
        allowed_gpu_users=allowed_gpu_users, wall_clock=lambda: int(wall_clock()))
    owner = TrustedDrainOwner(args.owner_id, wall_clock=wall_clock)
    plan = supervisor.begin(preflight)
    current_plan["plan"] = plan
    try:
        receipt = supervisor.run_smoke_bounded(
            heartbeat=lambda: supervisor.heartbeat(owner.now_epoch()))
        supervisor.restore(now_epoch=owner.now_epoch(), owner_present=True)
    except BaseException:
        if supervisor.active:
            try:
                supervisor.restore(now_epoch=owner.now_epoch(), owner_present=True)
            except BaseException:
                pass
        raise
    print(json.dumps({"effects": "pilot-complete", "lease_id": plan.lease_id,
                      "generation": plan.generation,
                      "receipt": {"profile": receipt["profile"],
                                  "request_count": receipt["request_count"],
                                  "exit_status": receipt["exit_status"]}}, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("pilot", "start", "heartbeat", "resume", "restore"), required=True)
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
    if args.phase == "pilot":
        required = (args.cycle, args.session_start_epoch, args.admin_path_evidence,
                    args.model_sha256, args.binary_sha256, args.unit_sha256)
        if any(value in (None, "") for value in required):
            raise SystemExit("pilot requires cycle, session start, admin evidence and three baseline hashes")
    if args.phase in {"heartbeat", "resume", "restore"} and (not args.lease_id or args.generation is None):
        raise SystemExit("this phase requires the exact lease id and generation")
    paths = FullDrainPaths(args.state_root)
    runner = _host_runner
    observer = CooperativeHostObserver(runner)
    if args.phase == "pilot":
        return _run_pilot(args, paths, runner=runner)
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
