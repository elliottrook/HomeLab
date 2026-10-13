"""Source-bound gate for any Aster benchmark using the shared lease.

The effect controller is not itself a backup or scheduler authority. Aster
benchmark admission must present this evidence object from reviewed source
adapters; hand-entered booleans or a bare backup string are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass


class AdmissionEvidenceError(ValueError):
    """The benchmark lacks independently sourced admission evidence."""


EXPECTED_BACKUP_SOURCE = "proxmox:backup-49999802-1365+truenas:1,3,2"
EXPECTED_CONSUMERS = ("aster-agent", "aster-llama", "aster-speech", "news")


@dataclass(frozen=True)
class AdmissionEvidence:
    source: str
    backup_receipt: str
    backup_completed_minute: int
    backup_verified: bool
    consumers_quiesced: tuple[str, ...]
    news_quiesced: bool
    source_observed: bool


def require_aster_benchmark(evidence: AdmissionEvidence | None, *, now_minute: int, window_end_minute: int) -> str:
    """Return the source-bound receipt or refuse the shared Aster benchmark."""
    if evidence is None:
        raise AdmissionEvidenceError("source-bound admission evidence is required")
    if evidence.source != EXPECTED_BACKUP_SOURCE or not evidence.source_observed:
        raise AdmissionEvidenceError("backup evidence source is not independently verified")
    if not evidence.backup_receipt or not evidence.backup_verified:
        raise AdmissionEvidenceError("verified backup receipt is required")
    if evidence.backup_completed_minute > now_minute:
        raise AdmissionEvidenceError("backup completion is from the future")
    if now_minute >= window_end_minute:
        raise AdmissionEvidenceError("benchmark window has closed")
    if not evidence.news_quiesced:
        raise AdmissionEvidenceError("News schedule quiescence is required")
    if evidence.consumers_quiesced != EXPECTED_CONSUMERS:
        raise AdmissionEvidenceError("all production consumers must be isolated")
    return evidence.backup_receipt
