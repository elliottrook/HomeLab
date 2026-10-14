"""Authenticated-shape quiescence receipts from fixed Proxmox-owner probes."""

from __future__ import annotations

from dataclasses import dataclass

from admission_gate import EXPECTED_CONSUMERS, AdmissionEvidenceError
from source_receipts import EXPECTED_QUIESCENCE_SOURCE, QuiescenceSourceReceipt


@dataclass(frozen=True)
class ConsumerSnapshot:
    observed_minute: int
    observed_monotonic: int
    active_states: tuple[str, ...]
    active_enter_monotonic: tuple[int, ...]
    news_timer_active: bool
    no_new_starts_marker: str


def compose_quiescence_receipt(first: ConsumerSnapshot, second: ConsumerSnapshot) -> QuiescenceSourceReceipt:
    """Require two fixed-source samples with stable inactive state."""
    if second.observed_minute < first.observed_minute:
        raise AdmissionEvidenceError("quiescence samples are out of order")
    if second.observed_monotonic <= first.observed_monotonic:
        raise AdmissionEvidenceError("quiescence interval is not positive")
    if first.active_states != ("inactive",) * len(EXPECTED_CONSUMERS) or second.active_states != ("inactive",) * len(EXPECTED_CONSUMERS):
        raise AdmissionEvidenceError("a production consumer remained active")
    if first.news_timer_active or second.news_timer_active:
        raise AdmissionEvidenceError("News timer remained active")
    if first.active_enter_monotonic != second.active_enter_monotonic:
        raise AdmissionEvidenceError("consumer start markers changed during quiescence")
    if first.no_new_starts_marker != second.no_new_starts_marker:
        raise AdmissionEvidenceError("a new-start marker changed during quiescence")
    return QuiescenceSourceReceipt(
        source=EXPECTED_QUIESCENCE_SOURCE,
        observed_minute=second.observed_minute,
        consumers=EXPECTED_CONSUMERS,
        news_quiesced=True,
        no_new_starts=True,
        source_observed=True,
    )
