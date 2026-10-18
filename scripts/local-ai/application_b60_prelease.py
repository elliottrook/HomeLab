"""Source-bound offline producer for the application-only B60 pre-lease.

The adapter is deliberately an interface, not a live host implementation.
Production wiring must provide fixed read-only Proxmox/TrueNAS/LXC sources and
an owner-controlled clock before this candidate can be promoted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from application_b60_controller import ApplicationPreLease
from application_b60_lease import ACCEPTED_BACKEND, APPLICATION_MODE

BACKUP_SOURCE = "proxmox:backup-49999802-1365"
TRUENAS_SOURCE = "truenas:rsynctask-1"
MAC_SUBSET_SOURCE = "proxmox:mac-subset-observer-v1"
RUNTIME_SOURCE = "proxmox:lxc-runtime-observer-v1"
EXPECTED_GUESTS = ("104", "110", "116")


class PreLeaseSourceError(ValueError):
    pass


@dataclass(frozen=True)
class BackupObservation:
    source: str
    cycle: str
    completed_epoch: int
    receipt: str
    verified: bool


@dataclass(frozen=True)
class TrueNASObservation:
    source: str
    cycle: str
    task_one_completed_epoch: int
    schedules_fixed: bool
    verified: bool


@dataclass(frozen=True)
class MacSubsetObservation:
    source: str
    cycle: str
    guest_ids: tuple[str, ...]
    mirror_completed_epoch: int
    verified: bool


@dataclass(frozen=True)
class RuntimeObservation:
    source: str
    cycle: str
    backend_identity: str
    llama_service_active: bool
    consumers_healthy: bool
    news_quiesced: bool
    verified: bool


@dataclass(frozen=True)
class LeaseWindowObservation:
    lease_id: str
    generation: int
    now_epoch: int
    start_deadline_epoch: int
    restore_start_epoch: int
    restore_deadline_epoch: int


class PreLeaseSources(Protocol):
    def backup(self) -> BackupObservation: ...
    def truenas(self) -> TrueNASObservation: ...
    def mac_subset(self) -> MacSubsetObservation: ...
    def runtime(self) -> RuntimeObservation: ...
    def window(self) -> LeaseWindowObservation: ...


def _observed(source: str, expected: str, cycle: str, observed_cycle: str,
              observed_epoch: int, now_epoch: int, verified: bool) -> None:
    if source != expected or observed_cycle != cycle or not verified:
        raise PreLeaseSourceError("pre-lease source attestation is incomplete")
    if type(observed_epoch) is not int or observed_epoch > now_epoch:
        raise PreLeaseSourceError("pre-lease observation is stale or from the future")


def produce_prelease(sources: PreLeaseSources, *, cycle: str) -> ApplicationPreLease:
    """Collect and bind fixed source observations without contacting a host."""
    backup = sources.backup()
    truenas = sources.truenas()
    mac = sources.mac_subset()
    runtime = sources.runtime()
    window = sources.window()
    now = window.now_epoch
    _observed(backup.source, BACKUP_SOURCE, cycle, backup.cycle,
              backup.completed_epoch, now, backup.verified)
    _observed(truenas.source, TRUENAS_SOURCE, cycle, truenas.cycle,
              truenas.task_one_completed_epoch, now,
              truenas.schedules_fixed and truenas.verified)
    _observed(mac.source, MAC_SUBSET_SOURCE, cycle, mac.cycle,
              mac.mirror_completed_epoch, now,
              mac.guest_ids == EXPECTED_GUESTS and mac.verified)
    _observed(runtime.source, RUNTIME_SOURCE, cycle, runtime.cycle,
              now, now, runtime.verified)
    if not backup.receipt.startswith("application-chain:"):
        raise PreLeaseSourceError("backup receipt is not application-bound")
    if (runtime.backend_identity != ACCEPTED_BACKEND
            or not runtime.llama_service_active
            or not runtime.consumers_healthy
            or not runtime.news_quiesced):
        raise PreLeaseSourceError("runtime or consumer observation is incomplete")
    if (not isinstance(window.lease_id, str) or not window.lease_id
            or type(window.generation) is not int or window.generation < 1
            or not (now < window.start_deadline_epoch
                    <= window.restore_start_epoch < window.restore_deadline_epoch)):
        raise PreLeaseSourceError("lease window is invalid")
    return ApplicationPreLease(
        mode=APPLICATION_MODE, lease_id=window.lease_id,
        generation=window.generation, backup_receipt=backup.receipt,
        backend_identity=runtime.backend_identity,
        llama_service_active=runtime.llama_service_active,
        consumers_healthy=runtime.consumers_healthy,
        news_quiesced=runtime.news_quiesced, now_epoch=now,
        start_deadline_epoch=window.start_deadline_epoch,
        restore_start_epoch=window.restore_start_epoch,
        restore_deadline_epoch=window.restore_deadline_epoch)
