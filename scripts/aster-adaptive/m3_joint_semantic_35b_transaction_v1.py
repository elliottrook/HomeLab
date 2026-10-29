"""Effect-order contract for one booked M3 35B public-gate transaction.

This module is deliberately pure: it cannot reserve Lab Hours, acquire a
lease, stop a service, restart a guest or call a model.  It fixes the sequence
that a later privileged driver must implement and the recovery sequence it
must use after any failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


MODEL_SHA256 = "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7"
RUNTIME_SHA256 = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
WORKLOAD = "m3-joint-semantic-35b-public-v1"
REQUEST_COUNT = 24
REQUEST_TIMEOUT_SECONDS = 90
MAX_TRANSACTION_SECONDS = 3_600
RESTORE_RESERVE_SECONDS = 900


class TransactionError(RuntimeError):
    pass


class RecoveryUncertain(TransactionError):
    pass


@dataclass(frozen=True)
class Admission:
    booking_id: str
    booking_workload: str
    now_epoch: int
    booking_end_epoch: int
    controller_deadline_epoch: int
    recovery_deadline_epoch: int
    reservation_confirmed: bool
    whole_host_lease_ready: bool
    shared_operation_lock_ready: bool
    restart_authorized: bool
    production_baseline_authenticated: bool
    watchdog_independent: bool

    def validate(self) -> None:
        if not self.booking_id or self.booking_workload != WORKLOAD:
            raise TransactionError("exact Lab Hours reservation is absent")
        if not (
            0 < self.now_epoch < self.controller_deadline_epoch
            <= self.booking_end_epoch <= self.recovery_deadline_epoch
        ):
            raise TransactionError("transaction timing is invalid")
        if self.recovery_deadline_epoch - self.now_epoch > MAX_TRANSACTION_SECONDS:
            raise TransactionError("transaction exceeds the bounded window")
        if self.recovery_deadline_epoch - self.controller_deadline_epoch < RESTORE_RESERVE_SECONDS:
            raise TransactionError("restoration reserve is insufficient")
        if not all((
            self.reservation_confirmed,
            self.whole_host_lease_ready,
            self.shared_operation_lock_ready,
            self.restart_authorized,
            self.production_baseline_authenticated,
            self.watchdog_independent,
        )):
            raise TransactionError("live prerequisites are incomplete")


@dataclass(frozen=True)
class Step:
    name: str
    effect: bool
    restart: bool = False
    model_requests: int = 0


FORWARD_STEPS = (
    Step("capture-exact-production-prestate", False),
    Step("persist-root-recovery-checkpoint", True),
    Step("arm-independent-recovery-owner", True),
    Step("claim-exact-lab-hours-booking", True),
    Step("acquire-whole-host-lease-and-shared-lock", True),
    Step("quiesce-registered-ai-consumers", True),
    Step("stop-lxc110-for-read-only-candidate-mount", True, restart=True),
    Step("add-exact-backup-excluded-read-only-35b-mount", True),
    Step("start-lxc110-with-candidate-mount", True, restart=True),
    Step("verify-artifact-runtime-auth-and-residency", False),
    Step("start-exact-transient-35b-public-gate-unit", True),
    Step("run-exact-public-gate", True, model_requests=REQUEST_COUNT),
    Step("freeze-content-free-public-summary", True),
    Step("stop-transient-35b-unit", True),
    Step("stop-lxc110-for-candidate-mount-removal", True, restart=True),
    Step("remove-only-exact-candidate-mount", True),
    Step("restore-root-custody-of-staged-artifact", True),
    Step("start-lxc110-in-captured-production-configuration", True, restart=True),
    Step("verify-exact-accepted-9b-sycl-production", False),
    Step("restore-registered-ai-consumers", True),
    Step("release-lock-lease-and-booking-after-proof", True),
    Step("disarm-recovery-owner-after-clean-proof", True),
)

RECOVERY_STEPS = (
    Step("stop-owned-transient-35b-unit-if-present", True),
    Step("stop-lxc110-if-exact-candidate-mount-present", True, restart=True),
    Step("remove-only-exact-candidate-mount-if-present", True),
    Step("restore-root-custody-of-staged-artifact", True),
    Step("start-lxc110-in-captured-production-configuration", True, restart=True),
    Step("verify-exact-accepted-9b-sycl-production", False),
    Step("restore-registered-ai-consumers", True),
    Step("release-lock-lease-and-booking-after-proof", True),
    Step("disarm-recovery-owner-after-clean-proof", True),
)


class Driver(Protocol):
    def apply(self, step: Step) -> None: ...
    def recover(self, steps: tuple[Step, ...]) -> bool: ...


def execute(admission: Admission, driver: Driver) -> None:
    admission.validate()
    try:
        for step in FORWARD_STEPS:
            driver.apply(step)
    except BaseException as error:
        try:
            restored = driver.recover(RECOVERY_STEPS)
        except BaseException as recovery_error:
            raise RecoveryUncertain("M3 recovery raised; retain state") from recovery_error
        if restored is not True:
            raise RecoveryUncertain("M3 recovery is unconfirmed; retain state") from error
        raise


def effect_summary() -> dict[str, object]:
    return {
        "schema": "aster-m3-joint-semantic-35b-transaction.v1",
        "workload": WORKLOAD,
        "model_sha256": MODEL_SHA256,
        "runtime_sha256": RUNTIME_SHA256,
        "requests": REQUEST_COUNT,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "max_transaction_seconds": MAX_TRANSACTION_SECONDS,
        "restore_reserve_seconds": RESTORE_RESERVE_SECONDS,
        "retries": 0,
        "promotion": False,
        "automatic_routing": "off",
    }

