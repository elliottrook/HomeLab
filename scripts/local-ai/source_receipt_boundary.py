"""Root-owned receipt envelope for the offline lease-admission candidate."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

from admission_gate import AdmissionEvidence, AdmissionEvidenceError, validate_evidence_shape
from fixed_source_adapters import FixedSourceAdapters

BOUNDARY_MARKER = "aster-source-receipt-boundary-v1"
RECEIPT_MODE = 0o600


def _parent_custody(path: Path) -> None:
    parent = path.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise AdmissionEvidenceError("receipt directory custody is not root-owned mode 0700")


def _custody(path: Path) -> None:
    _parent_custody(path)
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != RECEIPT_MODE):
        raise AdmissionEvidenceError("receipt custody is not root-owned mode 0600")


def _write_envelope(path: Path, evidence: AdmissionEvidence, *, lease_id: str, generation: int, captured_epoch: int) -> None:
    if os.geteuid() != 0:
        raise PermissionError("receipt writer must run as root")
    if not lease_id or generation < 1 or captured_epoch < 1:
        raise ValueError("receipt identity is incomplete")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = {
        "boundary": BOUNDARY_MARKER,
        "lease_id": lease_id,
        "generation": generation,
        "captured_epoch": captured_epoch,
        "evidence": {
            "source": evidence.source,
            "backup_receipt": evidence.backup_receipt,
            "backup_completed_minute": evidence.backup_completed_minute,
            "backup_verified": evidence.backup_verified,
            "consumers_quiesced": list(evidence.consumers_quiesced),
            "news_quiesced": evidence.news_quiesced,
            "source_observed": evidence.source_observed,
        },
    }
    _parent_custody(path)
    if path.exists() or path.is_symlink():
        _custody(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".source-receipt-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            os.fchmod(stream.fileno(), RECEIPT_MODE)
            stream.write(json.dumps(payload, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    _custody(path)


def produce_candidate_receipt(path: Path, adapters: FixedSourceAdapters, *, lease_id: str, generation: int, date_prefix: str, lease_issued_epoch: int, now_minute: int, window_end_minute: int, captured_epoch: int, expected_backup_receipt: str) -> None:
    """Acquire fixed-source evidence before writing the candidate envelope."""
    if os.geteuid() != 0:
        raise PermissionError("receipt producer must run as root")
    evidence = adapters.evidence_from_retained(date_prefix=date_prefix, lease_issued_epoch=lease_issued_epoch, now_minute=now_minute, window_end_minute=window_end_minute)
    if not expected_backup_receipt or evidence.backup_receipt != expected_backup_receipt:
        raise AdmissionEvidenceError("post-stop backup receipt differs from acquired lease")
    _write_envelope(path, evidence, lease_id=lease_id, generation=generation, captured_epoch=captured_epoch)


def read_receipt(path: Path, *, lease_id: str, generation: int, now_minute: int, window_end_minute: int, now_epoch: int, max_age_seconds: int = 900) -> str:
    _custody(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, "r") as stream:
            payload = json.load(stream)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    if payload.get("boundary") != BOUNDARY_MARKER or payload.get("lease_id") != lease_id or payload.get("generation") != generation:
        raise AdmissionEvidenceError("receipt is not bound to the current lease")
    captured_epoch = payload.get("captured_epoch")
    if not isinstance(captured_epoch, int) or captured_epoch > now_epoch or now_epoch - captured_epoch > max_age_seconds:
        raise AdmissionEvidenceError("receipt is stale or from the future")
    raw = payload.get("evidence", {})
    evidence = AdmissionEvidence(
        source=raw["source"], backup_receipt=raw["backup_receipt"],
        backup_completed_minute=raw["backup_completed_minute"], backup_verified=raw["backup_verified"],
        consumers_quiesced=tuple(raw["consumers_quiesced"]), news_quiesced=raw["news_quiesced"],
        source_observed=raw["source_observed"],
    )
    return validate_evidence_shape(evidence, now_minute=now_minute, window_end_minute=window_end_minute)
