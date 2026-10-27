"""Pure transaction contract for the first full-Aster challenger screen.

This module has no command runner or CLI.  It fixes the only permitted effect
order and the recovery order so a later root composition can be reviewed and
tested without granting restart or model-call authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


MODEL_PATH = "/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1/Qwen3.6-35B-A3B-Q4_K_M.gguf"
MODEL_BYTES = 20_419_565_568
MODEL_SHA256 = "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7"
BASELINE_MODEL_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
RUNTIME_SHA256 = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
UNIT_SHA256 = "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"
MOUNT_KEY = "mp0"
GUEST_MODEL_PATH = "/opt/models/aster-first-screen/Qwen3.6-35B-A3B-Q4_K_M.gguf"
MAX_OUTAGE_SECONDS = 5_400
RESTORE_RESERVE_SECONDS = 900
REQUEST_COUNT = 2
REQUEST_TIMEOUT_SECONDS = 60


class TransactionError(RuntimeError):
    pass


class RecoveryUncertain(TransactionError):
    pass


@dataclass(frozen=True)
class ScreenAdmission:
    cycle_date: str
    f2_sha256: str
    f3_sha256: str
    f4_sha256: str
    f5_sha256: str
    admission_sha256: str
    now_epoch: int
    evidence_expires_epoch: int
    restore_deadline_epoch: int
    competing_work_absent: bool
    watchdog_independent: bool
    baseline_authenticated: bool

    def validate(self) -> None:
        values = (self.f2_sha256, self.f3_sha256, self.f4_sha256,
                  self.f5_sha256, self.admission_sha256)
        if (len(self.cycle_date) != 10
                or any(len(value) != 64 or set(value) - set("0123456789abcdef")
                       for value in values)):
            raise TransactionError("admission identity is invalid")
        if not (0 < self.now_epoch < self.evidence_expires_epoch
                < self.restore_deadline_epoch):
            raise TransactionError("admission timing is invalid")
        if self.restore_deadline_epoch - self.now_epoch > MAX_OUTAGE_SECONDS:
            raise TransactionError("outage window exceeds the owner budget")
        if self.restore_deadline_epoch - self.evidence_expires_epoch \
                < RESTORE_RESERVE_SECONDS:
            raise TransactionError("restoration reserve is insufficient")
        if not (self.competing_work_absent and self.watchdog_independent
                and self.baseline_authenticated):
            raise TransactionError("live prerequisites are incomplete")


@dataclass(frozen=True)
class Step:
    name: str
    effect: bool
    restart: bool = False
    model_request: bool = False


FORWARD_STEPS = (
    Step("capture-exact-prestate", False),
    Step("persist-recovery-checkpoint", True),
    Step("arm-independent-owner-and-watchdog", True),
    Step("acquire-whole-host-evaluation-lease", True),
    Step("quiesce-registered-consumers", True),
    Step("stop-lxc110-for-read-only-mount", True, restart=True),
    Step("add-fixed-read-only-backup-excluded-mount", True),
    Step("start-lxc110-with-candidate-mount", True, restart=True),
    Step("verify-mounted-artifact-and-accepted-runtime", False),
    Step("stop-accepted-baseline-before-candidate", True),
    Step("start-fixed-transient-candidate-unit", True),
    Step("verify-candidate-load-and-residency", False),
    Step("run-synthetic-request-1", True, model_request=True),
    Step("run-synthetic-request-2", True, model_request=True),
    Step("stop-transient-candidate-unit", True),
    Step("stop-lxc110-for-mount-removal", True, restart=True),
    Step("remove-only-fixed-candidate-mount", True),
    Step("start-lxc110-in-captured-configuration", True, restart=True),
    Step("verify-exact-9b-sycl-auth-and-schedules", False),
    Step("restore-registered-consumers", True),
    Step("release-lease-after-independent-proof", True),
    Step("disarm-watchdog-after-clean-recovery", True),
)

RECOVERY_STEPS = (
    Step("stop-transient-candidate-if-owned", True),
    Step("stop-lxc110-if-candidate-mount-present", True, restart=True),
    Step("remove-only-fixed-candidate-mount-if-present", True),
    Step("start-lxc110-in-captured-configuration", True, restart=True),
    Step("verify-exact-9b-sycl-auth-and-schedules", False),
    Step("restore-registered-consumers", True),
    Step("release-lease-after-independent-proof", True),
    Step("disarm-watchdog-after-clean-recovery", True),
)


class Driver(Protocol):
    def apply(self, step: Step) -> None: ...
    def recover(self, steps: tuple[Step, ...]) -> bool: ...


def execute(admission: ScreenAdmission, driver: Driver) -> None:
    """Run once; every failure enters the fixed recovery sequence without retry."""
    admission.validate()
    try:
        for step in FORWARD_STEPS:
            driver.apply(step)
    except BaseException as error:
        try:
            restored = driver.recover(RECOVERY_STEPS)
        except BaseException as recovery_error:
            raise RecoveryUncertain("screen recovery raised; retain state") from recovery_error
        if restored is not True:
            raise RecoveryUncertain("screen recovery is unconfirmed; retain state") from error
        raise


def effect_summary() -> dict[str, object]:
    return {
        "schema": "aster-full-path-first-screen-transaction.v1",
        "model_path": MODEL_PATH,
        "model_bytes": MODEL_BYTES,
        "model_sha256": MODEL_SHA256,
        "guest_model_path": GUEST_MODEL_PATH,
        "mount_key": MOUNT_KEY,
        "baseline_model_sha256": BASELINE_MODEL_SHA256,
        "runtime_sha256": RUNTIME_SHA256,
        "unit_sha256": UNIT_SHA256,
        "requests": REQUEST_COUNT,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "max_outage_seconds": MAX_OUTAGE_SECONDS,
        "restore_reserve_seconds": RESTORE_RESERVE_SECONDS,
        "retries": 0,
        "promotion": False,
    }
