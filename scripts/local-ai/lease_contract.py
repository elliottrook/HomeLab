"""Pure planning contract for the Local AI exclusive maintenance lease.

This module intentionally has no Proxmox, systemd, SSH or network side effects.
It validates the preconditions and emits an ordered action plan for a future
operator/controller adapter. Deployment remains a separate authorization gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LeaseError(ValueError):
    """The requested lease cannot safely be planned."""


class LeaseState(str, Enum):
    READY = "ready"
    LEASED = "leased"
    RESTORING = "restoring"
    FAILED = "failed"


@dataclass(frozen=True)
class BackupChain:
    completed: bool
    verified: bool
    completed_minute: int


@dataclass(frozen=True)
class LeaseRequest:
    now_minute: int
    window_end_minute: int
    backup: BackupChain
    production_active: bool
    conflicting_job_active: bool
    host_lock_available: bool


@dataclass(frozen=True)
class LeasePlan:
    state: LeaseState
    actions: tuple[str, ...]


@dataclass(frozen=True)
class LeaseReceipt:
    """Durable, non-secret admission facts bound to one lab lease."""

    lease_id: str
    generation: int
    issued_minute: int
    expires_minute: int
    backup_receipt: str
    model_identity: str
    backend_identity: str
    consumers_isolated: bool
    scheduled_work_quiesced: bool


ACCEPTED_MODEL = "Qwen3.5 9B Q4_K_M"
ACCEPTED_BACKEND = "llama.cpp b11429 SYCL/Level Zero"


def _validate_identity_and_backup(
    receipt: LeaseReceipt,
    *,
    now_minute: int,
    expected_backup_receipt: str,
    watchdog_alive: bool,
    require_watchdog: bool = True,
) -> None:
    if not receipt.lease_id or receipt.generation < 1:
        raise LeaseError("lease receipt identity is invalid")
    if receipt.issued_minute > now_minute:
        raise LeaseError("lease receipt is from the future")
    if receipt.expires_minute <= now_minute:
        raise LeaseError("lease receipt has expired")
    if receipt.expires_minute <= receipt.issued_minute:
        raise LeaseError("lease receipt expiry is invalid")
    if receipt.backup_receipt != expected_backup_receipt:
        raise LeaseError("lease receipt is not bound to the verified backup")
    if receipt.model_identity != ACCEPTED_MODEL:
        raise LeaseError("lease model identity is not the accepted 9B baseline")
    if receipt.backend_identity != ACCEPTED_BACKEND:
        raise LeaseError("lease backend identity is not the accepted SYCL baseline")
    if require_watchdog and not watchdog_alive:
        raise LeaseError("independent lease watchdog is not alive")


def validate_receipt(
    receipt: LeaseReceipt,
    *,
    now_minute: int,
    expected_backup_receipt: str,
    watchdog_alive: bool,
) -> None:
    """Validate a durable admitted lease after stable isolation is observed."""
    _validate_identity_and_backup(
        receipt, now_minute=now_minute,
        expected_backup_receipt=expected_backup_receipt,
        watchdog_alive=watchdog_alive,
    )
    if not receipt.consumers_isolated:
        raise LeaseError("production consumers are not isolated")
    if not receipt.scheduled_work_quiesced:
        raise LeaseError("scheduled work is not quiesced")


def validate_pre_acquire_receipt(
    receipt: LeaseReceipt,
    *,
    now_minute: int,
    expected_backup_receipt: str,
    watchdog_alive: bool,
) -> None:
    """Validate a proposed lease before any consumer has been stopped.

    The admission receipt is deliberately stricter after the controller has
    observed stable isolation. A caller cannot assert that future isolation
    has already happened in order to pass the pre-acquire gate.
    """
    if receipt.consumers_isolated or receipt.scheduled_work_quiesced:
        raise LeaseError("pre-acquire receipt cannot claim completed isolation")
    _validate_identity_and_backup(
        receipt, now_minute=now_minute,
        expected_backup_receipt=expected_backup_receipt,
        watchdog_alive=watchdog_alive,
    )


def validate_stream_pre_acquire_evidence(
    receipt: LeaseReceipt,
    *,
    now_minute: int,
    expected_backup_receipt: str,
    watchdog_alive: bool,
) -> None:
    """Validate Stream A evidence before its separate F6 watchdog gate.

    This is not valid for acquisition.  The effectful controller continues to
    use ``validate_pre_acquire_receipt`` and therefore requires a live
    independent watchdog before any consumer effect.
    """
    if receipt.consumers_isolated or receipt.scheduled_work_quiesced:
        raise LeaseError("pre-acquire receipt cannot claim completed isolation")
    _validate_identity_and_backup(
        receipt, now_minute=now_minute,
        expected_backup_receipt=expected_backup_receipt,
        watchdog_alive=watchdog_alive,
        require_watchdog=False,
    )


def plan_acquire(request: LeaseRequest) -> LeasePlan:
    """Return an ordered, side-effect-free acquisition plan."""

    if request.now_minute >= request.window_end_minute:
        raise LeaseError("exclusive lab window has already closed")
    if not request.backup.completed or not request.backup.verified:
        raise LeaseError("verified backup chain is required before lab lease")
    if request.backup.completed_minute > request.now_minute:
        raise LeaseError("backup completion is in the future")
    if request.production_active:
        raise LeaseError("production workload must be drained before lease")
    if request.conflicting_job_active:
        raise LeaseError("conflicting backup or scheduled job is active")
    if not request.host_lock_available:
        raise LeaseError("host lease lock is unavailable")

    return LeasePlan(
        state=LeaseState.LEASED,
        actions=(
            "acquire-host-lock",
            "record-pre-lab-checkpoint",
            "drain-nonessential-guests-and-timers",
            "verify-control-plane-survival-set",
            "permit-lab-maintenance-and-restart",
        ),
    )


def plan_release(*, health_verified: bool, restore_complete: bool) -> LeasePlan:
    """Return the ordered release plan; never claim success before health."""

    if not restore_complete:
        return LeasePlan(
            state=LeaseState.RESTORING,
            actions=("restore-accepted-v1-service", "verify-production-health"),
        )
    if not health_verified:
        return LeasePlan(
            state=LeaseState.FAILED,
            actions=("retain-degraded-state", "alert-operator", "keep-lease-held"),
        )
    return LeasePlan(
        state=LeaseState.READY,
        actions=(
            "verify-production-health",
            "release-host-lock",
            "record-post-lab-checkpoint",
        ),
    )
