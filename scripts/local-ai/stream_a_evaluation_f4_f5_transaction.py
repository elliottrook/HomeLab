"""Pure builder for one Stream A F4/F5/admission transaction.

The caller must supply already trusted, content-free source observations.  This
module has no filesystem, command, network, systemd, lease, or model effects.
It makes the cross-artifact byte bindings deterministic before a separately
reviewed root entry point is allowed to collect or write live evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from lease_watchdog import EXPECTED_SCHEDULES, Observation
from stream_a_evaluation_admission import (
    ADMISSION_PREFIX,
    EXPECTED_AUTH_IDENTITY,
    EXPECTED_BINARY_SHA256,
    EXPECTED_UNIT_SHA256,
    build_admission,
    build_f5_observation,
    canonical_bytes,
)


class TransactionError(ValueError):
    pass


_CYCLE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
_NONCE = re.compile(r"^[0-9a-f]{16}$")
_LEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{0,159}$")
MAX_FRESH_SECONDS = 15 * 60
ACCEPTED_MODEL = "Qwen3.5 9B Q4_K_M"
ACCEPTED_BACKEND = "llama.cpp b11429 SYCL/Level Zero"
F4_SCHEMA = "aster-pre-acquire-receipt-v1"


@dataclass(frozen=True)
class TransactionArtifacts:
    lease_id: str
    generation: int
    f4_bytes: bytes
    f5_bytes: bytes
    admission_bytes: bytes
    admission_receipt: str


def _encode_f4(*, lease_id: str, observed_epoch: int,
               observed_minute: int, expires_minute: int,
               backup_receipt: str, observation: Observation) -> bytes:
    if (observation.now_minute != observed_minute
            or observation.schedule_points != EXPECTED_SCHEDULES
            or observation.heartbeat_alive is not False
            or not all((
                observation.control_plane_healthy,
                observation.production_services_healthy,
                observation.accepted_gpu_visible,
                observation.schedule_restored,
                observation.schedules_enabled,
                observation.exact_binary_verified,
                observation.model_verified,
                observation.unit_verified,
                observation.auth_verified,
            ))):
        raise TransactionError("F4 production observation is incomplete")
    return canonical_bytes({
        "schema": F4_SCHEMA,
        "captured_epoch": observed_epoch,
        "receipt": {
            "lease_id": lease_id, "generation": 1,
            "issued_minute": observed_minute,
            "expires_minute": expires_minute,
            "backup_receipt": backup_receipt,
            "model_identity": ACCEPTED_MODEL,
            "backend_identity": ACCEPTED_BACKEND,
            "consumers_isolated": False,
            "scheduled_work_quiesced": False,
        },
        "observation": {
            "now_minute": observation.now_minute,
            "heartbeat_alive": False,
            "control_plane_healthy": observation.control_plane_healthy,
            "production_services_healthy": observation.production_services_healthy,
            "accepted_gpu_visible": observation.accepted_gpu_visible,
            "schedule_restored": observation.schedule_restored,
            "schedule_points": list(observation.schedule_points),
            "schedules_enabled": observation.schedules_enabled,
            "exact_binary_verified": observation.exact_binary_verified,
            "model_verified": observation.model_verified,
            "unit_verified": observation.unit_verified,
            "auth_verified": observation.auth_verified,
        },
    })


def _digest(value: object) -> str:
    return hashlib.sha256(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()


def build_transaction(
    *,
    cycle_date: str,
    nonce: str,
    observed_epoch: int,
    observed_minute: int,
    f2_bytes: bytes,
    f3_bytes: bytes,
    backup_receipt: str,
    observation: Observation,
    lxc110_mirror_identity: str,
    lease_id: str | None = None,
) -> TransactionArtifacts:
    """Build exact canonical bytes without writing or performing an effect."""
    if _CYCLE.fullmatch(cycle_date) is None or _NONCE.fullmatch(nonce) is None:
        raise TransactionError("cycle or nonce is invalid")
    if (type(observed_epoch) is not int or observed_epoch <= 0
            or type(observed_minute) is not int
            or observation.now_minute != observed_minute):
        raise TransactionError("observation time is invalid")
    if not isinstance(f2_bytes, bytes) or not f2_bytes or not isinstance(f3_bytes, bytes) or not f3_bytes:
        raise TransactionError("predecessor bytes are missing")
    if not isinstance(lxc110_mirror_identity, str) or not lxc110_mirror_identity:
        raise TransactionError("LXC110 mirror identity is missing")

    lease_id = f"stream-a-evaluation-{cycle_date}-{nonce}" if lease_id is None else lease_id
    if not isinstance(lease_id, str) or _LEASE_ID.fullmatch(lease_id) is None:
        raise TransactionError("lease identity is invalid")
    expires_epoch = observed_epoch + MAX_FRESH_SECONDS
    expires_minute = observed_minute + MAX_FRESH_SECONDS // 60
    f4_bytes = _encode_f4(
        lease_id=lease_id, observed_epoch=observed_epoch,
        observed_minute=observed_minute, expires_minute=expires_minute,
        backup_receipt=backup_receipt, observation=observation)
    schedule_digest = _digest(list(EXPECTED_SCHEDULES))
    baseline_digest = _digest({
        "control_plane_healthy": observation.control_plane_healthy,
        "production_services_healthy": observation.production_services_healthy,
        "accepted_gpu_visible": observation.accepted_gpu_visible,
        "schedule_restored": observation.schedule_restored,
        "schedules_enabled": observation.schedules_enabled,
        "exact_binary_verified": observation.exact_binary_verified,
        "model_verified": observation.model_verified,
        "unit_verified": observation.unit_verified,
        "auth_verified": observation.auth_verified,
    })
    f5 = build_f5_observation(
        cycle_date=cycle_date,
        observed_epoch=observed_epoch,
        expires_epoch=expires_epoch,
        f2_result_sha256=hashlib.sha256(f2_bytes).hexdigest(),
        f3_receipt_sha256=hashlib.sha256(f3_bytes).hexdigest(),
        f4_receipt_sha256=hashlib.sha256(f4_bytes).hexdigest(),
        lxc110_mirror_identity=lxc110_mirror_identity,
        schedule_set_sha256=schedule_digest,
        binary_sha256=EXPECTED_BINARY_SHA256,
        unit_sha256=EXPECTED_UNIT_SHA256,
        auth_identity=EXPECTED_AUTH_IDENTITY,
        consumer_baseline_sha256=baseline_digest,
    )
    f5_bytes = canonical_bytes(f5)
    admission = build_admission(
        cycle_date=cycle_date,
        lease_id=lease_id,
        generation=1,
        created_epoch=observed_epoch,
        expires_epoch=expires_epoch,
        backup_receipt=backup_receipt,
        f2_bytes=f2_bytes,
        f3_bytes=f3_bytes,
        f4_bytes=f4_bytes,
        f5_bytes=f5_bytes,
    )
    admission_bytes = canonical_bytes(admission)
    admission_receipt = ADMISSION_PREFIX + hashlib.sha256(admission_bytes).hexdigest()
    return TransactionArtifacts(
        lease_id, 1, f4_bytes, f5_bytes, admission_bytes, admission_receipt)
