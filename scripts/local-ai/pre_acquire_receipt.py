"""Durable, non-effect F4 receipt consumed before full-stop acquisition.

This receipt is deliberately distinct from the post-stop source receipt.  It
binds the retained archive digest to a proposed, non-isolated lease and the
03:05 runtime observation.  It may be written before F7/F8, but it never
creates a lease, lock, service stop, or permission to run lab work.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
import re

from lease_contract import (
    LeaseReceipt,
    validate_pre_acquire_receipt,
    validate_stream_pre_acquire_evidence,
)
from lease_watchdog import EXPECTED_SCHEDULES, Observation


SCHEMA = "aster-pre-acquire-receipt-v1"
RECEIPT_PATH = Path("/var/lib/local-ai-lab/pre-acquire-receipt.json")
MAX_RECEIPT_BYTES = 8192
MAX_AGE_SECONDS = 900
FIELDS = frozenset({"schema", "captured_epoch", "receipt", "observation"})
RECEIPT_FIELDS = frozenset({
    "lease_id", "generation", "issued_minute", "expires_minute",
    "backup_receipt", "model_identity", "backend_identity",
    "consumers_isolated", "scheduled_work_quiesced",
})
OBSERVATION_FIELDS = frozenset({
    "now_minute", "heartbeat_alive", "control_plane_healthy",
    "production_services_healthy", "accepted_gpu_visible", "schedule_restored",
    "schedule_points", "schedules_enabled", "exact_binary_verified",
    "model_verified", "unit_verified", "auth_verified",
})


class PreAcquireReceiptError(ValueError):
    pass


BACKUP_DIGEST = re.compile(r"retained-archive-integrity-sha256:[0-9a-f]{64}")


def _encode(receipt: LeaseReceipt, observation: Observation, *, captured_epoch: int,
            stream_evidence: bool) -> bytes:
    """Validate and serialize a non-effect proposal without claiming isolation."""
    if captured_epoch < 1:
        raise PreAcquireReceiptError("capture time is invalid")
    if receipt.consumers_isolated or receipt.scheduled_work_quiesced:
        raise PreAcquireReceiptError("pre-acquire receipt cannot claim isolation")
    validator = (validate_stream_pre_acquire_evidence if stream_evidence
                 else validate_pre_acquire_receipt)
    validator(
        receipt,
        now_minute=observation.now_minute,
        expected_backup_receipt=receipt.backup_receipt,
        watchdog_alive=observation.heartbeat_alive,
    )
    if observation.schedule_points != EXPECTED_SCHEDULES:
        raise PreAcquireReceiptError("pre-acquire schedule set is incomplete")
    if not all((
        observation.control_plane_healthy,
        observation.production_services_healthy,
        observation.accepted_gpu_visible,
        observation.schedule_restored,
        observation.schedules_enabled,
        observation.exact_binary_verified,
        observation.model_verified,
        observation.unit_verified,
        observation.auth_verified,
    )):
        raise PreAcquireReceiptError("pre-acquire runtime observation is incomplete")
    payload = {
        "schema": SCHEMA,
        "captured_epoch": captured_epoch,
        "receipt": {
            "lease_id": receipt.lease_id,
            "generation": receipt.generation,
            "issued_minute": receipt.issued_minute,
            "expires_minute": receipt.expires_minute,
            "backup_receipt": receipt.backup_receipt,
            "model_identity": receipt.model_identity,
            "backend_identity": receipt.backend_identity,
            "consumers_isolated": False,
            "scheduled_work_quiesced": False,
        },
        "observation": {
            "now_minute": observation.now_minute,
            "heartbeat_alive": observation.heartbeat_alive,
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
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise PreAcquireReceiptError("pre-acquire receipt exceeds size limit")
    return encoded


def encode(receipt: LeaseReceipt, observation: Observation, *, captured_epoch: int) -> bytes:
    return _encode(receipt, observation, captured_epoch=captured_epoch,
                   stream_evidence=False)


def encode_stream_evidence(receipt: LeaseReceipt, observation: Observation, *,
                           captured_epoch: int) -> bytes:
    """Encode non-effect Stream A evidence before the separate F6 gate."""
    return _encode(receipt, observation, captured_epoch=captured_epoch,
                   stream_evidence=True)


def _decode(payload: object, *, now_minute: int, now_epoch: int,
            max_age_seconds: int, stream_evidence: bool) -> tuple[LeaseReceipt, Observation, int]:
    """Decode and validate a fresh proposal before the controller is called."""
    if type(payload) is not dict or set(payload) != FIELDS or payload.get("schema") != SCHEMA:
        raise PreAcquireReceiptError("pre-acquire receipt schema differs")
    captured = payload["captured_epoch"]
    if type(captured) is not int or captured < 1 or captured > now_epoch or now_epoch - captured > max_age_seconds:
        raise PreAcquireReceiptError("pre-acquire receipt is stale or from the future")
    raw_receipt = payload["receipt"]
    raw_observation = payload["observation"]
    if type(raw_receipt) is not dict or set(raw_receipt) != RECEIPT_FIELDS:
        raise PreAcquireReceiptError("pre-acquire lease shape differs")
    if type(raw_observation) is not dict or set(raw_observation) != OBSERVATION_FIELDS:
        raise PreAcquireReceiptError("pre-acquire observation shape differs")
    if type(raw_observation["schedule_points"]) is not list or any(type(item) is not str for item in raw_observation["schedule_points"]):
        raise PreAcquireReceiptError("pre-acquire schedule shape differs")
    if not BACKUP_DIGEST.fullmatch(raw_receipt.get("backup_receipt", "")):
        raise PreAcquireReceiptError("pre-acquire backup binding differs")
    if any(type(raw_receipt[key]) is not expected for key, expected in (
        ("lease_id", str), ("generation", int), ("issued_minute", int),
        ("expires_minute", int), ("backup_receipt", str),
        ("model_identity", str), ("backend_identity", str),
        ("consumers_isolated", bool), ("scheduled_work_quiesced", bool),
    )):
        raise PreAcquireReceiptError("pre-acquire lease types differ")
    if any(type(raw_observation[key]) is not expected for key, expected in (
        ("now_minute", int), ("heartbeat_alive", bool),
        ("control_plane_healthy", bool), ("production_services_healthy", bool),
        ("accepted_gpu_visible", bool), ("schedule_restored", bool),
        ("schedules_enabled", bool), ("exact_binary_verified", bool),
        ("model_verified", bool), ("unit_verified", bool),
        ("auth_verified", bool),
    )):
        raise PreAcquireReceiptError("pre-acquire observation types differ")
    try:
        receipt = LeaseReceipt(
            lease_id=raw_receipt["lease_id"], generation=raw_receipt["generation"],
            issued_minute=raw_receipt["issued_minute"], expires_minute=raw_receipt["expires_minute"],
            backup_receipt=raw_receipt["backup_receipt"], model_identity=raw_receipt["model_identity"],
            backend_identity=raw_receipt["backend_identity"],
            consumers_isolated=raw_receipt["consumers_isolated"],
            scheduled_work_quiesced=raw_receipt["scheduled_work_quiesced"],
        )
        observation = Observation(
            now_minute=raw_observation["now_minute"], heartbeat_alive=raw_observation["heartbeat_alive"],
            control_plane_healthy=raw_observation["control_plane_healthy"],
            production_services_healthy=raw_observation["production_services_healthy"],
            accepted_gpu_visible=raw_observation["accepted_gpu_visible"],
            schedule_restored=raw_observation["schedule_restored"],
            schedule_points=tuple(raw_observation["schedule_points"]),
            schedules_enabled=raw_observation["schedules_enabled"],
            exact_binary_verified=raw_observation["exact_binary_verified"],
            model_verified=raw_observation["model_verified"],
            unit_verified=raw_observation["unit_verified"],
            auth_verified=raw_observation["auth_verified"],
        )
    except (TypeError, ValueError) as exc:
        raise PreAcquireReceiptError("pre-acquire receipt types differ") from exc
    if observation.now_minute != receipt.issued_minute:
        raise PreAcquireReceiptError("pre-acquire receipt and observation minute differ")
    validator = (validate_stream_pre_acquire_evidence if stream_evidence
                 else validate_pre_acquire_receipt)
    validator(
        receipt,
        now_minute=now_minute,
        expected_backup_receipt=receipt.backup_receipt,
        watchdog_alive=observation.heartbeat_alive,
    )
    if observation.schedule_points != EXPECTED_SCHEDULES:
        raise PreAcquireReceiptError("pre-acquire schedule set is incomplete")
    if not all((
        observation.control_plane_healthy,
        observation.production_services_healthy,
        observation.accepted_gpu_visible,
        observation.schedule_restored,
        observation.schedules_enabled,
        observation.exact_binary_verified,
        observation.model_verified,
        observation.unit_verified,
        observation.auth_verified,
    )):
        raise PreAcquireReceiptError("pre-acquire runtime observation is incomplete")
    return receipt, observation, captured


def decode(payload: object, *, now_minute: int, now_epoch: int,
           max_age_seconds: int = MAX_AGE_SECONDS) -> tuple[LeaseReceipt, Observation, int]:
    return _decode(payload, now_minute=now_minute, now_epoch=now_epoch,
                   max_age_seconds=max_age_seconds, stream_evidence=False)


def decode_stream_evidence(payload: object, *, now_minute: int, now_epoch: int,
                           max_age_seconds: int = MAX_AGE_SECONDS) -> tuple[LeaseReceipt, Observation, int]:
    """Decode non-effect Stream A evidence before the separate F6 gate."""
    return _decode(payload, now_minute=now_minute, now_epoch=now_epoch,
                   max_age_seconds=max_age_seconds, stream_evidence=True)


def save_root_owned(path: Path, payload: bytes) -> None:
    """Write once with root custody; an existing path requires review."""
    if os.geteuid() != 0:
        raise PreAcquireReceiptError("root identity is required")
    parent = path.parent
    parent_info = parent.lstat()
    if not stat.S_ISDIR(parent_info.st_mode) or parent_info.st_uid != 0 or stat.S_IMODE(parent_info.st_mode) != 0o700:
        raise PreAcquireReceiptError("receipt directory custody is invalid")
    if path.exists() or path.is_symlink():
        raise PreAcquireReceiptError("pre-acquire receipt already exists; operator review is required")
    descriptor, temporary = tempfile.mkstemp(prefix=".pre-acquire-receipt-", dir=parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_root_owned(path: Path, *, now_minute: int, now_epoch: int) -> tuple[LeaseReceipt, Observation, int]:
    parent = path.parent.lstat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0 or stat.S_IMODE(parent.st_mode) != 0o700:
        raise PreAcquireReceiptError("receipt directory custody is invalid")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
            raise PreAcquireReceiptError("receipt custody is invalid")
        raw = os.read(descriptor, MAX_RECEIPT_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise PreAcquireReceiptError("pre-acquire receipt exceeds size limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PreAcquireReceiptError("pre-acquire receipt cannot be decoded") from exc
    return decode(payload, now_minute=now_minute, now_epoch=now_epoch)
