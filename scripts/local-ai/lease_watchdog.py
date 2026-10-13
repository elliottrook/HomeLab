"""Pure watchdog and re-entry contract for the Local AI maintenance lease.

The platform adapter supplies observations and performs commands. This module
only decides whether admission may continue, whether restoration is required,
and when a lock may be released.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from lease_contract import LeaseError, LeaseReceipt, validate_receipt


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


@dataclass(frozen=True)
class WatchdogDecision:
    state: WatchdogState
    actions: tuple[str, ...]


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
        if not observation.accepted_gpu_visible or not observation.schedule_restored:
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
