"""Strict, secret-free boundary for the host-owned application lease receipt."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict

SCHEMA = "aster-application-receipt.v1"
MODE = "application-b60-exclusive-v1"
BACKEND = "llama.cpp b11429 SYCL/Level Zero"
CONSUMERS = (("104", "aster-agent.service"), ("116", "aster-speech.service"))


@dataclass(frozen=True)
class ApplicationReceipt:
    schema: str
    mode: str
    lease_id: str
    generation: int
    backup_receipt: str
    watchdog_deadline_minute: int
    backend_identity: str
    llama_service_active: bool
    exclusive_backend_claim: bool
    backend_listener_ipv4_only: bool
    consumers_quiesced: tuple[tuple[str, str], ...]
    news_quiesced: bool
    sidecar_source_digest: str
    sidecar_uid: int
    sidecar_worker_count: int
    sidecar_port: int
    sidecar_credential_denied: bool
    sidecar_network_denied: bool
    sidecar_started_within_lease: bool


def validate(receipt: ApplicationReceipt, *, expected_lease_id: str, expected_generation: int, now_minute: int) -> None:
    if receipt.schema != SCHEMA or receipt.mode != MODE:
        raise ValueError("application receipt schema or mode is invalid")
    if (receipt.lease_id, receipt.generation) != (expected_lease_id, expected_generation):
        raise ValueError("application receipt identity does not match")
    if not receipt.backup_receipt or receipt.backup_receipt.startswith("full-stop:"):
        raise ValueError("application receipt requires a distinct backup receipt")
    if now_minute > receipt.watchdog_deadline_minute:
        raise ValueError("application receipt is past its watchdog deadline")
    if (receipt.backend_identity != BACKEND or not receipt.llama_service_active
            or not receipt.exclusive_backend_claim or not receipt.backend_listener_ipv4_only):
        raise ValueError("backend is not host-attested and exclusively claimed")
    if receipt.consumers_quiesced != CONSUMERS or not receipt.news_quiesced:
        raise ValueError("consumer quiescence is incomplete")
    if (len(receipt.sidecar_source_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in receipt.sidecar_source_digest)
            or receipt.sidecar_uid <= 0 or receipt.sidecar_worker_count != 1
            or not 1 <= receipt.sidecar_port <= 65535
            or not receipt.sidecar_credential_denied
            or not receipt.sidecar_network_denied
            or not receipt.sidecar_started_within_lease):
        raise ValueError("sidecar host observation is incomplete")


def encode(receipt: ApplicationReceipt) -> str:
    """Encode deterministic receipt content; callers must persist atomically."""
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":")) + "\n"


def digest(receipt: ApplicationReceipt) -> str:
    return hashlib.sha256(encode(receipt).encode()).hexdigest()
