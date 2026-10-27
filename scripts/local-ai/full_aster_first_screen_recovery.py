"""Mount-aware recovery boundary for the full-Aster first screen.

The recovery coordinator is dependency-injected and has no CLI.  A later
guardian composition supplies fixed observations and command execution after
checking durable owner/lease identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

from full_aster_first_screen_candidate import (
    baseline_start_command, reset_failed_command, stop_command,
)


HOST_MODEL = "/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1/Qwen3.6-35B-A3B-Q4_K_M.gguf"
GUEST_MOUNT = "/opt/models/aster-first-screen"
MOUNT_VALUE = f"{HOST_MODEL},mp={GUEST_MOUNT},ro=1,backup=0"
MOUNT_KEY = "mp0"


class RecoveryError(RuntimeError):
    pass


class Observer(Protocol):
    def candidate_absent(self) -> bool: ...
    def mount_state(self) -> str: ...
    def guest_running(self) -> bool: ...
    def exact_baseline_restored(self) -> bool: ...


@dataclass(frozen=True)
class RecoveryIdentity:
    owner_id: str
    lease_id: str
    generation: int
    cycle: str
    model_sha256: str
    binary_sha256: str
    unit_sha256: str

    def validate(self) -> None:
        hashes = (self.model_sha256, self.binary_sha256, self.unit_sha256)
        if (not self.owner_id.startswith("aster-full-screen-owner-")
                or not self.lease_id.startswith(self.owner_id + ":")
                or type(self.generation) is not int or self.generation != 1
                or len(self.cycle) != 10
                or any(len(value) != 64 or set(value) - set("0123456789abcdef")
                       for value in hashes)):
            raise RecoveryError("recovery identity is invalid")


def shutdown_command() -> tuple[str, ...]:
    return ("pct", "shutdown", "110", "--timeout", "60")


def start_guest_command() -> tuple[str, ...]:
    return ("pct", "start", "110")


def delete_mount_command() -> tuple[str, ...]:
    return ("pct", "set", "110", "--delete", MOUNT_KEY)


def full_drain_rescue_command(identity: RecoveryIdentity) -> tuple[str, ...]:
    identity.validate()
    return (
        "/usr/bin/python3", "-B",
        "/usr/local/libexec/local-ai-lease/full-inference-pilot/full_inference_lab_runtime.py",
        "--phase", "rescue", "--state-root", "/var/lib/local-ai-lab",
        "--owner-id", identity.owner_id, "--lease-id", identity.lease_id,
        "--generation", str(identity.generation), "--cycle", identity.cycle,
        "--model-sha256", identity.model_sha256,
        "--binary-sha256", identity.binary_sha256,
        "--unit-sha256", identity.unit_sha256, "--effect-authorized",
    )


def recover(*, identity: RecoveryIdentity, observer: Observer,
            runner: Callable[[Sequence[str], float], None]) -> None:
    """Recover once; ambiguity retains state and prevents lease release."""
    identity.validate()
    runner(stop_command(), 30.0)
    runner(reset_failed_command(), 15.0)
    if not observer.candidate_absent():
        raise RecoveryError("candidate process or unit remains")

    mount = observer.mount_state()
    if mount not in {"exact", "absent"}:
        raise RecoveryError("LXC110 mount state is foreign or uncertain")
    if mount == "exact":
        if observer.guest_running():
            runner(shutdown_command(), 75.0)
            if observer.guest_running():
                raise RecoveryError("LXC110 did not stop for mount recovery")
        runner(delete_mount_command(), 30.0)
        if observer.mount_state() != "absent":
            raise RecoveryError("owned candidate mount was not removed")
    if not observer.guest_running():
        runner(start_guest_command(), 90.0)
        if not observer.guest_running():
            raise RecoveryError("LXC110 did not restart")

    runner(baseline_start_command(), 360.0)
    if not observer.exact_baseline_restored():
        raise RecoveryError("accepted 9B/SYCL baseline is not exact")
    runner(full_drain_rescue_command(identity), 180.0)
    if not observer.exact_baseline_restored():
        raise RecoveryError("production restoration drifted after lease rescue")
