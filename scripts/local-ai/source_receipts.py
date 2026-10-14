"""Candidate source-receipt adapters for lease admission.

These parsers validate provenance-shaped records without contacting systems or
claiming that a source was actually authenticated. Production wiring must
replace the synthetic constructors with fixed Proxmox/TrueNAS and Proxmox/LXC
read-only adapters.
"""

from __future__ import annotations

from dataclasses import dataclass

from admission_gate import (
    EXPECTED_BACKUP_SOURCE,
    EXPECTED_CONSUMERS,
    AdmissionEvidence,
    AdmissionEvidenceError,
)


EXPECTED_QUIESCENCE_SOURCE = "proxmox-owner:fixed-consumer-observer-v1"


@dataclass(frozen=True)
class BackupSourceReceipt:
    source: str
    chain_id: str
    completed_minute: int
    integrity_receipt: str
    integrity_verified: bool
    source_observed: bool


@dataclass(frozen=True)
class QuiescenceSourceReceipt:
    source: str
    observed_minute: int
    consumers: tuple[str, ...]
    news_quiesced: bool
    no_new_starts: bool
    source_observed: bool


def compose_candidate_evidence(
    backup: BackupSourceReceipt,
    quiescence: QuiescenceSourceReceipt,
    *,
    now_minute: int,
    window_end_minute: int,
    authenticated: bool = False,
) -> AdmissionEvidence:
    """Bind two source-shaped receipts into one candidate evidence object."""
    if backup.source != EXPECTED_BACKUP_SOURCE or backup.chain_id != EXPECTED_BACKUP_SOURCE:
        raise AdmissionEvidenceError("backup source or chain identity is not fixed")
    if not backup.source_observed or not backup.integrity_verified or not backup.integrity_receipt:
        raise AdmissionEvidenceError("backup source receipt is incomplete")
    if backup.completed_minute > now_minute:
        raise AdmissionEvidenceError("backup receipt is from the future")
    if quiescence.source != EXPECTED_QUIESCENCE_SOURCE or not quiescence.source_observed:
        raise AdmissionEvidenceError("quiescence source is not fixed and observed")
    if quiescence.observed_minute > now_minute:
        raise AdmissionEvidenceError("quiescence receipt is from the future")
    if quiescence.consumers != EXPECTED_CONSUMERS:
        raise AdmissionEvidenceError("quiescence consumer set is incomplete")
    if not quiescence.news_quiesced or not quiescence.no_new_starts:
        raise AdmissionEvidenceError("News or new-start quiescence is incomplete")
    if now_minute >= window_end_minute:
        raise AdmissionEvidenceError("admission window has closed")
    return AdmissionEvidence(
        source=EXPECTED_BACKUP_SOURCE,
        backup_receipt=backup.integrity_receipt,
        backup_completed_minute=backup.completed_minute,
        backup_verified=backup.integrity_verified,
        consumers_quiesced=quiescence.consumers,
        news_quiesced=quiescence.news_quiesced,
        source_observed=True,
        adapter_attested=authenticated,
    )
