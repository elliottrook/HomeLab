"""Offline persistent-supervisor coordination candidate for the full drain."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, FrozenSet, Sequence

from full_inference_lab_session import (FullDrainError, FullDrainPlan,
    FullDrainPreflight, FullInferenceDrainController)
from full_inference_lab_workload import (lab_cleanup_command, lab_is_absent,
    run_fixed_smoke, run_fixed_smoke_bounded)


class SupervisorError(FullDrainError):
    pass


@dataclass(frozen=True)
class GpuUser:
    pid: int
    starttime: int
    cgroup: str
    executable: str


def require_known_gpu_users(users: FrozenSet[GpuUser], allowed: FrozenSet[GpuUser]) -> None:
    unknown = users - allowed
    if unknown:
        raise SupervisorError("unlisted GPU consumer detected")


@dataclass(frozen=True)
class WatchdogDecision:
    action: str
    reason: str


def watchdog_decision(*, now_epoch: int, heartbeat_epoch: int,
                      heartbeat_timeout: int, hard_deadline_epoch: int,
                      owner_alive: bool, owner_identity_ok: bool) -> WatchdogDecision:
    if now_epoch >= hard_deadline_epoch:
        return WatchdogDecision("recover", "hard-deadline")
    if not owner_alive or not owner_identity_ok:
        return WatchdogDecision("recover", "owner-lost")
    if now_epoch - heartbeat_epoch > heartbeat_timeout:
        return WatchdogDecision("recover", "heartbeat-stale")
    return WatchdogDecision("observe", "healthy")


class PersistentFullDrainSupervisor:
    """Keep the controller alive across workload and restore phases.

    The caller supplies only fixed observers/runners. This class has no
    unattended authority and is disabled unless its host service is separately
    reviewed and enabled.
    """

    def __init__(self, controller: FullInferenceDrainController, *,
                 workload_runner: Callable[[Sequence[str], float], tuple[int, str]],
                 production_masked: Callable[[], bool],
                 lab_absent: Callable[[], bool],
                 gpu_users: Callable[[], FrozenSet[GpuUser]],
                 allowed_gpu_users: FrozenSet[GpuUser],
                 wall_clock: Callable[[], int]):
        self.controller = controller
        self.workload_runner = workload_runner
        self.production_masked = production_masked
        self.lab_absent = lab_absent
        self.gpu_users = gpu_users
        self.allowed_gpu_users = allowed_gpu_users
        self.wall_clock = wall_clock
        self.plan: FullDrainPlan | None = None
        self.preflight: FullDrainPreflight | None = None
        self.before_users: FrozenSet[GpuUser] = frozenset()
        self.active = False

    def begin(self, preflight: FullDrainPreflight) -> FullDrainPlan:
        self.preflight = preflight
        was_clear = not self.controller.paths.state.exists() and not self.controller.paths.lock.exists()
        try:
            self.plan = self.controller.begin(preflight)
            self.before_users = self.gpu_users()
            require_known_gpu_users(self.before_users, self.allowed_gpu_users)
            self.active = True
            return self.plan
        except BaseException:
            if was_clear and self.controller.paths.state.exists() and self.controller.paths.lock.exists():
                if self.controller._exclusion is not None:
                    self.controller._exclusion.__exit__(None, None, None)
                    self.controller._exclusion = None
                try:
                    import json
                    state = json.loads(self.controller.paths.state.read_text(encoding="utf-8"))
                    plan = self.controller.resume_existing(
                        lease_id=state["lease_id"], generation=int(state["generation"]))
                    self.controller.restore(plan, now_epoch=self.wall_clock(), owner_present=True)
                except BaseException:
                    self.active = False
                    raise
            self.active = False
            raise

    def heartbeat(self, now_epoch: int) -> None:
        if not self.active or self.plan is None:
            raise SupervisorError("supervisor is not active")
        self.controller.heartbeat(now_epoch)
        self.controller.require_work_window(now_epoch)

    def run_smoke(self) -> dict[str, object]:
        if not self.active or self.plan is None or self.preflight is None:
            raise SupervisorError("supervisor is not active")
        if self.wall_clock() >= self.preflight.lab_end_epoch:
            raise SupervisorError("hard lab cutoff has passed")
        try:
            if not self.production_masked():
                raise SupervisorError("production llama service is not masked and inactive")
            require_known_gpu_users(self.gpu_users(), self.allowed_gpu_users)
            receipt = run_fixed_smoke(self.workload_runner,
                                      lease_id=self.plan.lease_id,
                                      generation=self.plan.generation)
            require_known_gpu_users(self.gpu_users(), self.allowed_gpu_users)
            if not self.lab_absent():
                raise SupervisorError("lab process or listener remains after workload")
            return receipt
        except BaseException:
            self.restore(now_epoch=self.wall_clock(), owner_present=True)
            raise

    def run_smoke_bounded(self, *, heartbeat: Callable[[], None],
                          monotonic: Callable[[], float] = time.monotonic) -> dict[str, object]:
        if not self.active or self.plan is None or self.preflight is None:
            raise SupervisorError("supervisor is not active")
        try:
            if not self.production_masked():
                raise SupervisorError("production llama service is not masked and inactive")
            require_known_gpu_users(self.gpu_users(), self.allowed_gpu_users)
            remaining = max(0.0, float(self.preflight.lab_end_epoch - self.wall_clock()))
            monotonic_deadline = monotonic() + min(300.0, remaining)
            def guarded_heartbeat() -> None:
                if self.wall_clock() >= self.preflight.lab_end_epoch:
                    raise SupervisorError("hard lab cutoff has passed")
                heartbeat()
            receipt = run_fixed_smoke_bounded(
                heartbeat=guarded_heartbeat, deadline=monotonic_deadline,
                monotonic=monotonic, lease_id=self.plan.lease_id,
                generation=self.plan.generation)
            require_known_gpu_users(self.gpu_users(), self.allowed_gpu_users)
            if not self.lab_absent():
                raise SupervisorError("lab process or listener remains after workload")
            return receipt
        except BaseException:
            self.restore(now_epoch=self.wall_clock(), owner_present=True)
            raise

    def restore(self, *, now_epoch: int, owner_present: bool) -> None:
        if not self.active or self.plan is None:
            raise SupervisorError("supervisor is not active")
        if not self.lab_absent():
            raise SupervisorError("lab process or listener remains; retain lock")
        self.controller.restore(self.plan, now_epoch=now_epoch, owner_present=owner_present)
        self.active = False


def recovery_only(controller: FullInferenceDrainController, *, lease_id: str,
                  generation: int, restore_now_epoch: int,
                  cleanup_runner: Callable[[Sequence[str], float], tuple[int, str]],
                  lab_absent: Callable[[], bool]) -> FullDrainPlan:
    """Clean up the fixed lab scope, prove absence, then restore only."""
    plan = controller.resume_existing(lease_id=lease_id, generation=generation)
    cleanup_runner(
        lab_cleanup_command(lease_id=plan.lease_id, generation=plan.generation), 30.0)
    if not lab_absent():
        raise SupervisorError("lab scope/listener/process/GPU absence is unproven; lock retained")
    controller.restore(plan, now_epoch=restore_now_epoch, owner_present=True)
    return plan
