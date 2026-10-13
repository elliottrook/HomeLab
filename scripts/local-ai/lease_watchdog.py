"""Pure watchdog and re-entry contract for the Local AI maintenance lease.

The platform adapter supplies observations and performs commands. This module
only decides whether admission may continue, whether restoration is required,
and when a lock may be released.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from lease_contract import LeaseError, LeaseReceipt, validate_receipt


EXPECTED_SCHEDULES = ("00:30", "01:00", "02:00", "03:00")


class WatchdogState(str, Enum):
    LEASED = "leased"
    RESTORING = "restoring"
    FAILED = "failed"
    READY = "ready"


@dataclass(frozen=True)
class Observation:
    now_minute: int
    heartbeat_alive: bool
    control_plane_healthy: bool
    production_services_healthy: bool
    accepted_gpu_visible: bool
    schedule_restored: bool
    schedule_points: tuple[str, ...] = EXPECTED_SCHEDULES


@dataclass(frozen=True)
class WatchdogDecision:
    state: WatchdogState
    actions: tuple[str, ...]


@dataclass(frozen=True)
class StatusReceipt:
    """Content-free status shared with authenticated consumers."""

    lease_id: str
    generation: int
    state: WatchdogState
    expires_minute: int
    model_identity: str
    backend_identity: str
    control_plane_healthy: bool
    production_services_healthy: bool
    accepted_gpu_visible: bool
    schedule_restored: bool
    failure_code: str | None


def status_receipt(receipt: LeaseReceipt, state: WatchdogState, observation: Observation, *, failure_code: str | None = None) -> dict[str, object]:
    """Return an allowlisted, content-free receipt suitable for API output."""

    value = StatusReceipt(
        lease_id=receipt.lease_id,
        generation=receipt.generation,
        state=state,
        expires_minute=receipt.expires_minute,
        model_identity=receipt.model_identity,
        backend_identity=receipt.backend_identity,
        control_plane_healthy=observation.control_plane_healthy,
        production_services_healthy=observation.production_services_healthy,
        accepted_gpu_visible=observation.accepted_gpu_visible,
        schedule_restored=observation.schedule_restored,
        failure_code=failure_code,
    )
    return asdict(value)


def decide(
    receipt: LeaseReceipt,
    observation: Observation,
    *,
    backup_receipt: str,
    current_state: WatchdogState,
) -> WatchdogDecision:
    """Return the fail-closed next step for one bounded observation."""

    if current_state == WatchdogState.READY:
        return WatchdogDecision(WatchdogState.READY, ("remain-ready",))

    if current_state == WatchdogState.LEASED:
        try:
            validate_receipt(
                receipt,
                now_minute=observation.now_minute,
                expected_backup_receipt=backup_receipt,
                watchdog_alive=observation.heartbeat_alive,
            )
        except LeaseError:
            return WatchdogDecision(
                WatchdogState.RESTORING,
                ("stop-new-lab-work", "persist-restore-intent", "restore-production"),
            )
        if not observation.control_plane_healthy:
            return WatchdogDecision(
                WatchdogState.RESTORING,
                ("stop-new-lab-work", "persist-restore-intent", "restore-production"),
            )
        return WatchdogDecision(WatchdogState.LEASED, ("permit-bounded-lab-work",))

    if current_state == WatchdogState.RESTORING:
        if not observation.control_plane_healthy or not observation.production_services_healthy:
            return WatchdogDecision(
                WatchdogState.FAILED,
                ("retain-lease-lock", "retain-restore-intent", "alert-operator"),
            )
        if (
            not observation.accepted_gpu_visible
            or not observation.schedule_restored
            or observation.schedule_points != EXPECTED_SCHEDULES
        ):
            return WatchdogDecision(
                WatchdogState.FAILED,
                ("retain-lease-lock", "retain-restore-intent", "alert-operator"),
            )
        return WatchdogDecision(
            WatchdogState.READY,
            ("verify-production-health", "record-post-restore-receipt", "release-lease-lock"),
        )

    return WatchdogDecision(
        WatchdogState.FAILED,
        ("retain-lease-lock", "retain-restore-intent", "alert-operator"),
    )
