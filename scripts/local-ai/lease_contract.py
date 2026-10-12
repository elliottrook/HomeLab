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
