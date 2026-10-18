"""Offline source-bound producer for the attended cooperative lab pilot.

The live adapter must populate these observations from fixed host commands and
``read_attested_source`` files.  This module accepts typed observations only;
it does not parse caller JSON or contact a host.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from application_b60_lease import ACCEPTED_BACKEND
from cooperative_lab_session import CooperativeLabPreflight
from application_b60_host_sources import AttestedSource

SOURCES = {
    "backup": "proxmox:backup-49999802-1365",
    "truenas": "truenas:rsynctask-1",
    "mac_subset": "proxmox:mac-subset-observer-v1",
    "runtime": "proxmox:lxc-runtime-observer-v1",
    "news": "proxmox:news-ingest-observer-v1",
}
EXPECTED_GUESTS = ("104", "110", "116")
MAX_SOURCE_AGE = {"backup": 15 * 60, "truenas": 15 * 60,
                  "mac_subset": 15 * 60, "runtime": 30, "news": 30}


class CooperativeSourceError(ValueError):
    pass


@dataclass(frozen=True)
class HostWindow:
    lease_id: str
    generation: int
    now_epoch: int
    session_start_epoch: int
    lab_end_epoch: int
    restore_deadline_epoch: int


def _source(bundle: Mapping[str, AttestedSource], name: str, cycle: str,
            now_epoch: int) -> dict[str, object]:
    value = bundle.get(name)
    if value is None or value.source != SOURCES[name] or value.cycle != cycle or not value.verified:
        raise CooperativeSourceError(f"{name} source attestation is incomplete")
    if value.observed_epoch > now_epoch:
        raise CooperativeSourceError(f"{name} source is from the future")
    if now_epoch - value.observed_epoch > MAX_SOURCE_AGE[name]:
        raise CooperativeSourceError(f"{name} source is stale")
    return value.payload


def produce_preflight(bundle: Mapping[str, AttestedSource], *, cycle: str,
                      window: HostWindow) -> CooperativeLabPreflight:
    """Build the lab preflight from independently attested host observations."""
    if set(bundle) != set(SOURCES):
        raise CooperativeSourceError("the source bundle is incomplete")
    if not window.lease_id or type(window.generation) is not int or window.generation < 1:
        raise CooperativeSourceError("host lease identity is invalid")
    backup = _source(bundle, "backup", cycle, window.now_epoch)
    truenas = _source(bundle, "truenas", cycle, window.now_epoch)
    mac = _source(bundle, "mac_subset", cycle, window.now_epoch)
    runtime = _source(bundle, "runtime", cycle, window.now_epoch)
    news = _source(bundle, "news", cycle, window.now_epoch)
    if not isinstance(backup.get("receipt"), str) or not backup["receipt"].startswith("application-chain:"):
        raise CooperativeSourceError("backup receipt is not application-bound")
    if truenas.get("schedules_fixed") is not True:
        raise CooperativeSourceError("TrueNAS schedule observation is not fixed")
    if tuple(mac.get("guest_ids", ())) != EXPECTED_GUESTS:
        raise CooperativeSourceError("Mac subset identity is incomplete")
    expected_runtime = {
        "backend_identity": ACCEPTED_BACKEND, "gpu_visible": True,
        "authentication_verified": True, "consumers_healthy": True,
        "news_timers_active": True, "deny_new_starts_supported": True,
    }
    if any(runtime.get(key) != value for key, value in expected_runtime.items()):
        raise CooperativeSourceError("runtime observation is incomplete")
    if type(runtime.get("direct_client_admission_enforced")) is not bool:
        raise CooperativeSourceError("direct-client admission proof is incomplete")
    next_ingest = news.get("next_ingest_epoch")
    if type(next_ingest) is not int or next_ingest <= window.now_epoch:
        raise CooperativeSourceError("next News ingest is not a future source observation")
    return CooperativeLabPreflight(
        mode="cooperative-lab-v1", lease_id=window.lease_id, generation=window.generation,
        backup_receipt=backup["receipt"], backend_identity=runtime["backend_identity"],
        gpu_visible=True, authentication_verified=True, source_verified=True,
        consumers_healthy=True, news_timers_active=True, deny_new_starts_supported=True,
        now_epoch=window.now_epoch, session_start_epoch=window.session_start_epoch,
        lab_end_epoch=window.lab_end_epoch, restore_deadline_epoch=window.restore_deadline_epoch,
        next_news_ingest_epoch=next_ingest,
        direct_client_admission_enforced=runtime["direct_client_admission_enforced"])
