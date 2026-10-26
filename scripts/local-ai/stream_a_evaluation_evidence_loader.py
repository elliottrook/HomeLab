"""Fail-closed loader for one accepted Stream A evaluation evidence set.

The loader has no write or service effects.  It rereads the fixed root-owned
F2/F3/F4/F5/admission artifacts, revalidates the retained archives against the
current Proxmox inventory, and returns only the content-free identities needed
to build ``LivePlan``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Callable

from f2_scheduled_release_candidate import LOCAL_ZONE, SCHEMA as F2_SCHEMA, _validate_projection
from pre_acquire_receipt import (
    decode_stream_evidence as decode_f4,
    encode_stream_evidence as encode_f4,
)
from retained_archive_integrity import (
    MAX_RECEIPT_BYTES as MAX_F3_BYTES,
    fixed_proxmox_inventory,
    fixed_resolve,
    verify as verify_f3,
)
from stream_a_evaluation_admission import (
    ADMISSION_PREFIX,
    F2_PREFIX,
    F3_PREFIX,
    load_bound_admission,
)
from stream_a_evaluation_live_plan import AcceptedEvidence


class EvidenceLoadError(ValueError):
    pass


MAX_F2_BYTES = 16 * 1024
MAX_F4_BYTES = 16 * 1024
_CYCLE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
_NONCE = re.compile(r"^[0-9a-f]{16}$")
_ADMISSION = re.compile(r"^stream-a-evaluation-admission-sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class EvidencePaths:
    f2_root: Path = Path("/var/lib/local-ai-lab/f2-scheduled")
    f3: Path = Path("/var/lib/local-ai-lab/archive-integrity.json")
    f4: Path = Path("/var/lib/local-ai-lab/pre-acquire-receipt.json")
    runtime: Path = Path("/var/lib/local-ai-lab/stream-a-evaluation")

    @property
    def f5(self) -> Path:
        return self.runtime / "f5-observation.json"

    @property
    def admission(self) -> Path:
        return self.runtime / "admission.json"


@dataclass(frozen=True)
class EvidenceExpectation:
    cycle_date: str
    nonce: str
    admission_receipt: str

    @property
    def lease_id(self) -> str:
        return f"stream-a-evaluation-{self.cycle_date}-{self.nonce}"

    def validate(self) -> None:
        if (_CYCLE.fullmatch(self.cycle_date) is None
                or _NONCE.fullmatch(self.nonce) is None
                or _ADMISSION.fullmatch(self.admission_receipt) is None):
            raise EvidenceLoadError("expected evidence identity is invalid")


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise EvidenceLoadError("evidence contains duplicate JSON keys")
        value[key] = item
    return value


def _read(path: Path, *, maximum: int, required_uid: int) -> bytes:
    try:
        parent = path.parent.stat()
    except OSError as error:
        raise EvidenceLoadError("evidence parent cannot be inspected") from error
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != required_uid
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise EvidenceLoadError("evidence parent custody is weak")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise EvidenceLoadError("evidence cannot be opened safely") from error
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != required_uid
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                or not 0 < info.st_size <= maximum):
            raise EvidenceLoadError("evidence custody or size is invalid")
        raw = os.read(descriptor, maximum + 1)
        if len(raw) != info.st_size:
            raise EvidenceLoadError("evidence changed while being read")
        return raw
    finally:
        os.close(descriptor)


def _json(raw: bytes, *, canonical_newline: bool) -> dict[str, object]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceLoadError("evidence is not unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise EvidenceLoadError("evidence is not an object")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    if canonical_newline:
        encoded += b"\n"
    if encoded != raw:
        raise EvidenceLoadError("evidence is not canonical JSON")
    return value


def _cross_bind_archives(f2: dict[str, object], f3: dict[str, object]) -> None:
    fields = (
        "vmid", "volid", "size", "ctime", "test_started_epoch",
        "test_finished_epoch", "test_elapsed_ms", "test_exit",
    )
    f2_rows = f2.get("result", {}).get("archives", [])
    f3_rows = f3.get("archives", [])
    if (not isinstance(f2_rows, list) or not isinstance(f3_rows, list)
            or len(f2_rows) != 3 or len(f3_rows) != 3):
        raise EvidenceLoadError("F2/F3 archive sets are incomplete")
    try:
        left = tuple(tuple(row[field] for field in fields) for row in f2_rows)
        right = tuple(tuple(row[field] for field in fields) for row in f3_rows)
    except (KeyError, TypeError) as error:
        raise EvidenceLoadError("F2/F3 archive row schema is invalid") from error
    if left != right:
        raise EvidenceLoadError("F2 and F3 archive rows do not match exactly")


def load_accepted_evidence(
    expectation: EvidenceExpectation,
    *,
    now_epoch: int,
    now_minute: int,
    paths: EvidencePaths = EvidencePaths(),
    inventory: Callable[[], list[dict]] = fixed_proxmox_inventory,
    resolve: Callable[[str], str] = fixed_resolve,
    lstat: Callable[[str], os.stat_result] = os.lstat,
    required_uid: int = 0,
) -> AcceptedEvidence:
    """Return one fully rebound evidence identity or fail before any effect."""
    expectation.validate()
    if type(now_epoch) is not int or now_epoch <= 0 or type(now_minute) is not int:
        raise EvidenceLoadError("evidence observation time is invalid")
    local_cycle = datetime.fromtimestamp(now_epoch, LOCAL_ZONE).strftime("%Y-%m-%d")
    if local_cycle != expectation.cycle_date:
        raise EvidenceLoadError("evidence cycle is not current")

    f2_path = paths.f2_root / f"{expectation.cycle_date}.json"
    f2_raw = _read(f2_path, maximum=MAX_F2_BYTES, required_uid=required_uid)
    f2 = _json(f2_raw, canonical_newline=True)
    if (set(f2) != {"schema", "cycle", "phase", "state", "error_class",
                   "first_failure_phase", "failure_class", "result"}
            or f2.get("schema") != F2_SCHEMA
            or f2.get("cycle") != expectation.cycle_date
            or f2.get("phase") != "final" or f2.get("state") != "complete"
            or any(f2.get(key) != "" for key in (
                "error_class", "first_failure_phase", "failure_class"))):
        raise EvidenceLoadError("F2 is not an exact current-cycle success")
    try:
        _validate_projection(f2["result"], expectation.cycle_date)
    except Exception as error:
        raise EvidenceLoadError("F2 projection is invalid") from error

    f3_raw = _read(paths.f3, maximum=MAX_F3_BYTES, required_uid=required_uid)
    f3 = _json(f3_raw, canonical_newline=False)
    _cross_bind_archives(f2, f3)
    try:
        backup_receipt = verify_f3(
            f3, inventory(), date=expectation.cycle_date.replace("-", "_"),
            now_epoch=now_epoch, resolve=resolve, lstat=lstat,
        )
    except Exception as error:
        raise EvidenceLoadError("F3 retained archive receipt is invalid") from error
    f2_receipt = F2_PREFIX + hashlib.sha256(f2_raw).hexdigest()
    f3_receipt = F3_PREFIX + hashlib.sha256(f3_raw).hexdigest()

    f4_raw = _read(paths.f4, maximum=MAX_F4_BYTES, required_uid=required_uid)
    f4 = _json(f4_raw, canonical_newline=True)
    try:
        receipt, observation, captured = decode_f4(
            f4, now_minute=now_minute, now_epoch=now_epoch)
        if encode_f4(receipt, observation, captured_epoch=captured) != f4_raw:
            raise EvidenceLoadError("F4 canonical bytes changed after validation")
    except Exception as error:
        if isinstance(error, EvidenceLoadError):
            raise
        raise EvidenceLoadError("F4 pre-acquire receipt is invalid") from error
    if (receipt.lease_id != expectation.lease_id or receipt.generation != 1
            or receipt.backup_receipt != backup_receipt):
        raise EvidenceLoadError("F4 lease or backup binding does not match")

    try:
        bound = load_bound_admission(
            paths.admission, paths.f5,
            receipt=expectation.admission_receipt,
            lease_id=expectation.lease_id, generation=1,
            backup_receipt=backup_receipt,
            f2_receipt=f2_receipt, f3_receipt=f3_receipt,
            now_epoch=now_epoch, require_fresh=True,
            required_uid=required_uid,
        )
    except Exception as error:
        raise EvidenceLoadError("F5/admission binding is invalid") from error
    if (bound.value["cycle_date"] != expectation.cycle_date
            or bound.value["f4_receipt_sha256"] != hashlib.sha256(f4_raw).hexdigest()):
        raise EvidenceLoadError("admission cycle or F4 digest does not match")

    accepted = AcceptedEvidence(
        cycle_date=expectation.cycle_date,
        nonce=expectation.nonce,
        now_epoch=now_epoch,
        backup_receipt=backup_receipt,
        f2_receipt=f2_receipt,
        f3_receipt=f3_receipt,
        admission_receipt=expectation.admission_receipt,
    )
    accepted.validate()
    return accepted
