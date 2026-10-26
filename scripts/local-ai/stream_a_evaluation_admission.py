"""Strict F4/F5 admission artifacts for the Stream A evaluation lease.

This module performs no host discovery and starts no services.  It only reads
or atomically writes bounded, canonical, root-custodied JSON artifacts whose
paths are fixed by the platform entry point.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AdmissionArtifactError(ValueError):
    pass


ADMISSION_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/admission.json")
F5_OBSERVATION_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/f5-observation.json")
ADMISSION_SCHEMA = "stream-a-evaluation-admission-v1"
F5_SCHEMA = "stream-a-evaluation-f5-observation-v1"
ADMISSION_PREFIX = "stream-a-evaluation-admission-sha256:"
BACKUP_PREFIX = "retained-archive-integrity-sha256:"
F2_PREFIX = "f2-result-sha256:"
F3_PREFIX = "f3-receipt-sha256:"
MAX_BYTES = 16 * 1024
MAX_FRESH_SECONDS = 15 * 60
EXPECTED_D4_DIGEST = "423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4"
EXPECTED_M3_DIGEST = "69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165"
EXPECTED_MODEL = "Qwen3.5-9B-Q4_K_M"
EXPECTED_BACKEND = "llama.cpp-b11429-SYCL-Level-Zero"
EXPECTED_BINARY_SHA256 = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
EXPECTED_UNIT_SHA256 = "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"
EXPECTED_AUTH_IDENTITY = "file:/etc/aster-llama-api-keys:ollama:ollama:0600"
_HEX = re.compile(r"^[0-9a-f]{64}$")
_DATE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")

ADMISSION_KEYS = {
    "schema", "cycle_date", "lease_id", "generation", "created_epoch",
    "expires_epoch", "backup_receipt", "f2_result_sha256",
    "f3_receipt_sha256", "f4_receipt_sha256", "f5_observation_sha256",
    "d4_run_digest", "m3_manifest_sha256", "model", "backend",
}
F5_KEYS = {
    "schema", "cycle_date", "observed_epoch", "expires_epoch",
    "f2_result_sha256", "f3_receipt_sha256", "f4_receipt_sha256",
    "lxc110_mirror_identity", "schedule_set_sha256", "model",
    "binary_sha256", "unit_sha256", "auth_identity",
    "consumer_baseline_sha256", "conflicting_lease", "conflicting_job",
}


@dataclass(frozen=True)
class BoundAdmission:
    value: dict[str, Any]
    digest: str
    receipt: str


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AdmissionArtifactError("artifact contains duplicate JSON keys")
        result[key] = value
    return result


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _secure_read(path: Path, *, required_uid: int = 0) -> tuple[dict[str, Any], bytes]:
    try:
        parent = path.parent.stat()
    except OSError as exc:
        raise AdmissionArtifactError("artifact parent cannot be inspected") from exc
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != required_uid
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise AdmissionArtifactError("artifact parent custody is weak")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise AdmissionArtifactError("artifact cannot be opened safely") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != required_uid
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                or info.st_size <= 0 or info.st_size > MAX_BYTES):
            raise AdmissionArtifactError("artifact custody or size is invalid")
        chunks = []
        remaining = MAX_BYTES + 1
        while remaining:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(fd)
    if len(raw) > MAX_BYTES:
        raise AdmissionArtifactError("artifact exceeds size bound")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionArtifactError("artifact JSON is invalid") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise AdmissionArtifactError("artifact is not canonical JSON")
    return value, raw


def _hex(value: object, field: str) -> None:
    if not isinstance(value, str) or _HEX.fullmatch(value) is None:
        raise AdmissionArtifactError(f"{field} is not a lowercase SHA-256")


def _fresh(created: object, expires: object, now_epoch: int) -> None:
    if type(created) is not int or type(expires) is not int or created <= 0:
        raise AdmissionArtifactError("artifact epochs are invalid")
    if created > now_epoch or expires < now_epoch:
        raise AdmissionArtifactError("artifact is future-dated or stale")
    if expires <= created or expires - created > MAX_FRESH_SECONDS:
        raise AdmissionArtifactError("artifact freshness window is invalid")


def validate_f5(value: dict[str, Any], *, now_epoch: int | None = None) -> None:
    if set(value) != F5_KEYS or value.get("schema") != F5_SCHEMA:
        raise AdmissionArtifactError("F5 observation schema is not exact")
    if not isinstance(value["cycle_date"], str) or _DATE.fullmatch(value["cycle_date"]) is None:
        raise AdmissionArtifactError("F5 cycle date is invalid")
    for field in ("f2_result_sha256", "f3_receipt_sha256", "f4_receipt_sha256",
                  "schedule_set_sha256", "binary_sha256", "unit_sha256",
                  "consumer_baseline_sha256"):
        _hex(value[field], field)
    if (not isinstance(value["lxc110_mirror_identity"], str)
            or not value["lxc110_mirror_identity"]
            or len(value["lxc110_mirror_identity"]) > 512):
        raise AdmissionArtifactError("lxc110_mirror_identity is invalid")
    if (value["model"] != EXPECTED_MODEL
            or value["binary_sha256"] != EXPECTED_BINARY_SHA256
            or value["unit_sha256"] != EXPECTED_UNIT_SHA256
            or value["auth_identity"] != EXPECTED_AUTH_IDENTITY):
        raise AdmissionArtifactError("F5 accepted runtime identity does not match")
    if value["conflicting_lease"] is not False or value["conflicting_job"] is not False:
        raise AdmissionArtifactError("F5 observed conflicting work")
    if now_epoch is not None:
        _fresh(value["observed_epoch"], value["expires_epoch"], now_epoch)


def validate_admission(value: dict[str, Any], *, now_epoch: int | None = None) -> None:
    if set(value) != ADMISSION_KEYS or value.get("schema") != ADMISSION_SCHEMA:
        raise AdmissionArtifactError("admission artifact schema is not exact")
    if not isinstance(value["cycle_date"], str) or _DATE.fullmatch(value["cycle_date"]) is None:
        raise AdmissionArtifactError("admission cycle date is invalid")
    if not isinstance(value["lease_id"], str) or not value["lease_id"]:
        raise AdmissionArtifactError("admission lease identity is invalid")
    if type(value["generation"]) is not int or value["generation"] < 1:
        raise AdmissionArtifactError("admission generation is invalid")
    if not isinstance(value["backup_receipt"], str) or not value["backup_receipt"].startswith(BACKUP_PREFIX):
        raise AdmissionArtifactError("admission backup receipt is invalid")
    _hex(value["backup_receipt"][len(BACKUP_PREFIX):], "backup_receipt")
    for field in ("f2_result_sha256", "f3_receipt_sha256", "f4_receipt_sha256",
                  "f5_observation_sha256", "d4_run_digest", "m3_manifest_sha256"):
        _hex(value[field], field)
    if (value["d4_run_digest"] != EXPECTED_D4_DIGEST
            or value["m3_manifest_sha256"] != EXPECTED_M3_DIGEST):
        raise AdmissionArtifactError("frozen workload digest does not match")
    if value["model"] != EXPECTED_MODEL or value["backend"] != EXPECTED_BACKEND:
        raise AdmissionArtifactError("accepted model/backend identity does not match")
    if now_epoch is not None:
        _fresh(value["created_epoch"], value["expires_epoch"], now_epoch)


def load_bound_admission(
        admission_path: Path, f5_path: Path, *, receipt: str,
        lease_id: str, generation: int, backup_receipt: str,
        f2_receipt: str, f3_receipt: str, now_epoch: int,
        require_fresh: bool, required_uid: int = 0) -> BoundAdmission:
    if not isinstance(receipt, str) or not receipt.startswith(ADMISSION_PREFIX):
        raise AdmissionArtifactError("admission receipt prefix is invalid")
    expected_digest = receipt[len(ADMISSION_PREFIX):]
    _hex(expected_digest, "admission_receipt")
    admission, raw = _secure_read(admission_path, required_uid=required_uid)
    validate_admission(admission, now_epoch=now_epoch if require_fresh else None)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_digest:
        raise AdmissionArtifactError("admission artifact digest does not match")
    if (admission["lease_id"] != lease_id or admission["generation"] != generation
            or admission["backup_receipt"] != backup_receipt
            or f2_receipt != F2_PREFIX + admission["f2_result_sha256"]
            or f3_receipt != F3_PREFIX + admission["f3_receipt_sha256"]):
        raise AdmissionArtifactError("admission identity or predecessor binding does not match")
    f5, f5_raw = _secure_read(f5_path, required_uid=required_uid)
    validate_f5(f5, now_epoch=now_epoch if require_fresh else None)
    if hashlib.sha256(f5_raw).hexdigest() != admission["f5_observation_sha256"]:
        raise AdmissionArtifactError("F5 observation digest does not match admission")
    if (f5["cycle_date"] != admission["cycle_date"]
            or f5["f2_result_sha256"] != admission["f2_result_sha256"]
            or f5["f3_receipt_sha256"] != admission["f3_receipt_sha256"]
            or f5["f4_receipt_sha256"] != admission["f4_receipt_sha256"]):
        raise AdmissionArtifactError("F5 observation cross-binding does not match")
    return BoundAdmission(admission, digest, receipt)


def atomic_write(path: Path, value: dict[str, Any], *, required_uid: int = 0) -> str:
    """Write a previously validated artifact without following path links."""
    if path.parent.stat().st_uid != required_uid or stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise AdmissionArtifactError("artifact parent custody is weak")
    raw = canonical_bytes(value)
    if len(raw) > MAX_BYTES:
        raise AdmissionArtifactError("artifact exceeds size bound")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return hashlib.sha256(raw).hexdigest()


def write_new_f5(path: Path, value: dict[str, Any], *, now_epoch: int,
                 required_uid: int = 0) -> str:
    """Validate and create one observation; existing evidence needs review."""
    validate_f5(value, now_epoch=now_epoch)
    if os.path.lexists(path):
        raise AdmissionArtifactError("F5 observation already exists")
    return atomic_write(path, value, required_uid=required_uid)


def write_new_admission(path: Path, value: dict[str, Any], *, now_epoch: int,
                        required_uid: int = 0) -> str:
    """Validate and create one admission; existing evidence needs review."""
    validate_admission(value, now_epoch=now_epoch)
    if os.path.lexists(path):
        raise AdmissionArtifactError("admission artifact already exists")
    return atomic_write(path, value, required_uid=required_uid)


def build_f5_observation(*, cycle_date: str, observed_epoch: int,
                         expires_epoch: int, f2_result_sha256: str,
                         f3_receipt_sha256: str, f4_receipt_sha256: str,
                         lxc110_mirror_identity: str,
                         schedule_set_sha256: str, binary_sha256: str,
                         unit_sha256: str, auth_identity: str,
                         consumer_baseline_sha256: str) -> dict[str, Any]:
    """Build the exact content-free F5 projection from trusted observations."""
    value = {
        "schema": F5_SCHEMA, "cycle_date": cycle_date,
        "observed_epoch": observed_epoch, "expires_epoch": expires_epoch,
        "f2_result_sha256": f2_result_sha256,
        "f3_receipt_sha256": f3_receipt_sha256,
        "f4_receipt_sha256": f4_receipt_sha256,
        "lxc110_mirror_identity": lxc110_mirror_identity,
        "schedule_set_sha256": schedule_set_sha256, "model": EXPECTED_MODEL,
        "binary_sha256": binary_sha256, "unit_sha256": unit_sha256,
        "auth_identity": auth_identity,
        "consumer_baseline_sha256": consumer_baseline_sha256,
        "conflicting_lease": False, "conflicting_job": False,
    }
    validate_f5(value, now_epoch=observed_epoch)
    return value


def build_admission(*, cycle_date: str, lease_id: str, generation: int,
                    created_epoch: int, expires_epoch: int,
                    backup_receipt: str, f2_bytes: bytes, f3_bytes: bytes,
                    f4_bytes: bytes, f5_bytes: bytes) -> dict[str, Any]:
    """Hash the exact retained predecessor bytes into one admission object."""
    try:
        f5 = json.loads(f5_bytes, object_pairs_hook=_unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionArtifactError("F5 bytes are invalid") from exc
    if not isinstance(f5, dict) or canonical_bytes(f5) != f5_bytes:
        raise AdmissionArtifactError("F5 bytes are not canonical")
    validate_f5(f5, now_epoch=created_epoch)
    digests = {
        "f2_result_sha256": hashlib.sha256(f2_bytes).hexdigest(),
        "f3_receipt_sha256": hashlib.sha256(f3_bytes).hexdigest(),
        "f4_receipt_sha256": hashlib.sha256(f4_bytes).hexdigest(),
    }
    if (f5["cycle_date"] != cycle_date
            or any(f5[field] != digest for field, digest in digests.items())):
        raise AdmissionArtifactError("F5 does not bind the supplied predecessor bytes")
    value = {
        "schema": ADMISSION_SCHEMA, "cycle_date": cycle_date,
        "lease_id": lease_id, "generation": generation,
        "created_epoch": created_epoch, "expires_epoch": expires_epoch,
        "backup_receipt": backup_receipt, **digests,
        "f5_observation_sha256": hashlib.sha256(f5_bytes).hexdigest(),
        "d4_run_digest": EXPECTED_D4_DIGEST,
        "m3_manifest_sha256": EXPECTED_M3_DIGEST,
        "model": EXPECTED_MODEL, "backend": EXPECTED_BACKEND,
    }
    validate_admission(value, now_epoch=created_epoch)
    return value
