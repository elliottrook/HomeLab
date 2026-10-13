"""Durable, secret-free lease admission record helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdmissionRecord:
    lease_id: str
    generation: int
    state: str
    issued_minute: int
    expires_minute: int
    backup_receipt: str
    model_identity: str
    backend_identity: str
    consumers_isolated: bool
    scheduled_work_quiesced: bool


def encode(record: AdmissionRecord) -> str:
    """Encode one deterministic record for an atomic on-host state file."""

    return json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n"


def decode(payload: str) -> AdmissionRecord:
    """Decode only the bounded admission schema; reject extra fields."""

    value = json.loads(payload)
    expected = set(AdmissionRecord.__dataclass_fields__)
    if set(value) != expected:
        raise ValueError("admission record schema mismatch")
    return AdmissionRecord(**value)


def expired(record: AdmissionRecord, now_minute: int) -> bool:
    return now_minute >= record.expires_minute
