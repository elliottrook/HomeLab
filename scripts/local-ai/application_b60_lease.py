"""Separate application-only B60 benchmark lease contract."""

from __future__ import annotations

from dataclasses import dataclass

APPLICATION_MODE = "application-b60-exclusive-v1"
ACCEPTED_BACKEND = "llama.cpp b11429 SYCL/Level Zero"
ALLOWED_CONSUMER_SERVICES = (("104", "aster-agent.service"), ("116", "aster-speech.service"))
FORBIDDEN_BACKEND_SERVICE = ("110", "aster-llama.service")


class ApplicationLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class SidecarObservation:
    source_digest: str
    uid: int
    worker_count: int
    port: int
    credential_denied: bool
    network_denied: bool
    started_within_lease: bool
    source_verified: bool


@dataclass(frozen=True)
class ApplicationLeaseReceipt:
    mode: str
    lease_id: str
    generation: int
    backup_receipt: str
    backend_identity: str
    llama_service_active: bool
    consumers_quiesced: tuple[tuple[str, str], ...]
    news_quiesced: bool
    sidecar: SidecarObservation


def command_for(vmid: str, unit: str, action: str) -> tuple[str, ...]:
    if (vmid, unit) not in ALLOWED_CONSUMER_SERVICES or action not in {"start", "stop"}:
        raise ApplicationLeaseError("application lease command is outside its consumer allowlist")
    return ("pct", "exec", vmid, "--", "systemctl", action, unit)


def validate(receipt: ApplicationLeaseReceipt, *, expected_lease_id: str, expected_generation: int) -> None:
    if receipt.mode != APPLICATION_MODE:
        raise ApplicationLeaseError("full-stop or unknown lease mode is not valid for application B60 work")
    if (receipt.lease_id, receipt.generation) != (expected_lease_id, expected_generation):
        raise ApplicationLeaseError("application lease identity does not match")
    if receipt.backend_identity != ACCEPTED_BACKEND or not receipt.llama_service_active:
        raise ApplicationLeaseError("accepted B60 backend must remain active")
    if receipt.consumers_quiesced != ALLOWED_CONSUMER_SERVICES or not receipt.news_quiesced:
        raise ApplicationLeaseError("application consumer isolation is incomplete")
    sidecar = receipt.sidecar
    if (sidecar.uid <= 0 or sidecar.worker_count != 1 or not 1 <= sidecar.port <= 65535
            or not sidecar.credential_denied or not sidecar.network_denied
            or not sidecar.started_within_lease or not sidecar.source_verified
            or len(sidecar.source_digest) != 64):
        raise ApplicationLeaseError("isolated sidecar observation is incomplete")
    if not receipt.backup_receipt or receipt.backup_receipt.startswith("full-stop:"):
        raise ApplicationLeaseError("application lease requires its own source-bound backup receipt")
