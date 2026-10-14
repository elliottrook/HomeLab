"""Root-owned receipt envelope for the offline lease-admission candidate."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from admission_gate import AdmissionEvidence, AdmissionEvidenceError, validate_evidence_shape

BOUNDARY_MARKER = "aster-source-receipt-boundary-v1"
RECEIPT_MODE = 0o600


def _custody(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != RECEIPT_MODE:
        raise AdmissionEvidenceError("receipt custody is not root-owned mode 0600")


def write_receipt(path: Path, evidence: AdmissionEvidence, *, lease_id: str, generation: int, captured_epoch: int) -> None:
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
    temporary = path.with_name(path.name + ".new")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n")
    os.chmod(temporary, RECEIPT_MODE)
    os.replace(temporary, path)
    _custody(path)


def read_receipt(path: Path, *, lease_id: str, generation: int, now_minute: int, window_end_minute: int) -> str:
    _custody(path)
    payload = json.loads(path.read_text())
    if payload.get("boundary") != BOUNDARY_MARKER or payload.get("lease_id") != lease_id or payload.get("generation") != generation:
        raise AdmissionEvidenceError("receipt is not bound to the current lease")
    raw = payload.get("evidence", {})
    evidence = AdmissionEvidence(
        source=raw["source"], backup_receipt=raw["backup_receipt"],
        backup_completed_minute=raw["backup_completed_minute"], backup_verified=raw["backup_verified"],
        consumers_quiesced=tuple(raw["consumers_quiesced"]), news_quiesced=raw["news_quiesced"],
        source_observed=raw["source_observed"],
    )
    return validate_evidence_shape(evidence, now_minute=now_minute, window_end_minute=window_end_minute)
