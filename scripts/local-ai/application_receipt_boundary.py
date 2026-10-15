"""Strict, secret-free boundary for the host-owned application lease receipt."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, asdict
from pathlib import Path

SCHEMA = "aster-application-receipt.v1"
MODE = "application-b60-exclusive-v1"
BACKEND = "llama.cpp b11429 SYCL/Level Zero"
CONSUMERS = (("104", "aster-agent.service"), ("116", "aster-speech.service"))
ADMISSION_ENDPOINT = "http://192.168.70.10:19104/v1/chat/completions"
A1_PROFILE_SHA256 = "7caddc30074f5925722861c59f70733894037b9fc5b0865feb98bf9e08bbbfec"
A1_SIDECAR_SOURCE_DIGEST = "969b6db34e8fe0c00e9a5be6163a498bae5ccfd101e42f699bfafb39f4a8c403"
OWNER_RECEIPT_PATH = Path("/var/lib/local-ai-lab/application-b60/application-receipt.json")
LEASE_STATE_PATH = Path("/var/lib/local-ai-lab/application-b60/application-b60.json")
LEASE_LOCK_PATH = Path("/var/lib/local-ai-lab/application-b60/application-b60.lock")
WATCHDOG_STATUS_PATH = Path("/var/lib/local-ai-lab/application-b60/watchdog-status.json")


@dataclass(frozen=True)
class ApplicationReceipt:
    schema: str
    mode: str
    lease_id: str
    generation: int
    backup_receipt: str
    watchdog_deadline_epoch: int
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


def validate(receipt: ApplicationReceipt, *, expected_lease_id: str, expected_generation: int, now_epoch: int) -> None:
    if receipt.schema != SCHEMA or receipt.mode != MODE:
        raise ValueError("application receipt schema or mode is invalid")
    if (receipt.lease_id, receipt.generation) != (expected_lease_id, expected_generation):
        raise ValueError("application receipt identity does not match")
    if not receipt.backup_receipt or receipt.backup_receipt.startswith("full-stop:"):
        raise ValueError("application receipt requires a distinct backup receipt")
    if now_epoch > receipt.watchdog_deadline_epoch:
        raise ValueError("application receipt is past its watchdog deadline")
    if (receipt.backend_identity != BACKEND or not receipt.llama_service_active
            or not receipt.exclusive_backend_claim or not receipt.backend_listener_ipv4_only):
        raise ValueError("backend is not host-attested and exclusively claimed")
    if receipt.consumers_quiesced != CONSUMERS or not receipt.news_quiesced:
        raise ValueError("consumer quiescence is incomplete")
    if (receipt.sidecar_source_digest != A1_SIDECAR_SOURCE_DIGEST
            or receipt.sidecar_uid != 1904 or receipt.sidecar_worker_count != 1
            or receipt.sidecar_port != 19104
            or not receipt.sidecar_credential_denied
            or not receipt.sidecar_network_denied
            or not receipt.sidecar_started_within_lease):
        raise ValueError("sidecar host observation is incomplete")


def encode(receipt: ApplicationReceipt) -> str:
    """Encode deterministic receipt content; callers must persist atomically."""
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":")) + "\n"


def digest(receipt: ApplicationReceipt) -> str:
    return hashlib.sha256(encode(receipt).encode()).hexdigest()


def admission_payload(receipt: ApplicationReceipt, *, expected_lease_id: str,
                       expected_generation: int, now_epoch: int,
                       profile_sha256: str, endpoint: str = ADMISSION_ENDPOINT) -> dict[str, object]:
    """Create the exact content-free callback payload for the Mini runner.

    The caller must obtain ``receipt`` from the authenticated host-owned
    receipt boundary; this function only validates and projects it. It never
    accepts a caller-supplied boolean or arbitrary endpoint.
    """
    validate(receipt, expected_lease_id=expected_lease_id,
             expected_generation=expected_generation, now_epoch=now_epoch)
    if endpoint != ADMISSION_ENDPOINT or profile_sha256 != A1_PROFILE_SHA256:
        raise ValueError("A1 admission endpoint or profile pin is invalid")
    return {
        "schema": "aster-a1-admission.v1",
        "lease_id": receipt.lease_id,
        "generation": receipt.generation,
        "receipt_sha256": digest(receipt),
        "profile_sha256": profile_sha256,
        "endpoint": ADMISSION_ENDPOINT,
    }


def validate_active_lease(receipt: ApplicationReceipt, state: dict,
                          watchdog: dict, *, now_epoch: int) -> None:
    """Reject cached receipts unless the current host lease is still armed."""
    if (state.get("mode") != MODE or state.get("phase") != "sidecar-admitted"
            or state.get("armed") is not True
            or not isinstance(state.get("lease_id"), str)
            or state.get("lease_id") != receipt.lease_id
            or type(state.get("generation")) is not int
            or state.get("generation") != receipt.generation
            or not isinstance(state.get("restore_deadline_epoch"), int)
            or state["restore_deadline_epoch"] <= now_epoch
            or receipt.watchdog_deadline_epoch != state["restore_deadline_epoch"]):
        raise ValueError("application lease is not currently admitted")
    if (watchdog.get("schema") != "aster-application-watchdog-status.v1"
            or watchdog.get("state") != "healthy"
            or watchdog.get("lease_id") != receipt.lease_id
            or watchdog.get("generation") != receipt.generation
            or not isinstance(watchdog.get("valid_until_epoch"), int)
            or watchdog["valid_until_epoch"] <= now_epoch):
        raise ValueError("application watchdog is not current")


def active_admission_payload(receipt: ApplicationReceipt, state: dict,
                             watchdog: dict, *, now_epoch: int,
                             profile_sha256: str) -> dict[str, object]:
    validate_active_lease(receipt, state, watchdog, now_epoch=now_epoch)
    return admission_payload(receipt, expected_lease_id=receipt.lease_id,
                              expected_generation=receipt.generation,
                              now_epoch=now_epoch,
                              profile_sha256=profile_sha256)


def load_active_admission_payload(*, now_epoch: int,
                                  profile_sha256: str) -> dict[str, object]:
    """Load and validate the current host lease, lock, watchdog and receipt."""
    lock = LEASE_LOCK_PATH.lstat()
    if not (stat.S_ISDIR(lock.st_mode) and lock.st_uid == 0
            and lock.st_mode & 0o077 == 0):
        raise ValueError("application lease lock custody failed")
    state = json.loads(LEASE_STATE_PATH.read_text())
    watchdog = json.loads(WATCHDOG_STATUS_PATH.read_text())
    receipt = load_owner_receipt()
    return active_admission_payload(receipt, state, watchdog,
                                    now_epoch=now_epoch,
                                    profile_sha256=profile_sha256)


def load_owner_receipt(path: Path = OWNER_RECEIPT_PATH) -> ApplicationReceipt:
    """Load the host-produced receipt from its fixed root-owned custody path."""
    if path != OWNER_RECEIPT_PATH or path.is_symlink():
        raise ValueError("application receipt path is not fixed")
    info = path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
            or info.st_mode & 0o077 or info.st_size > 16_000):
        raise ValueError("application receipt custody failed")
    raw = path.read_bytes()
    value = json.loads(raw)
    if set(value) != set(ApplicationReceipt.__dataclass_fields__):
        raise ValueError("application receipt fields are not exact")
    value["consumers_quiesced"] = tuple(tuple(item) for item in value["consumers_quiesced"])
    return ApplicationReceipt(**value)
