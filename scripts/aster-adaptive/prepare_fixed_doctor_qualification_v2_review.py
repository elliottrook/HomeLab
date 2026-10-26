"""Build a candidate-blind review packet for deterministic fixed Doctor v2."""
from __future__ import annotations

import hashlib
import json

from fixed_doctor_qualification_v2 import CASE_IDS, REQUIRED_DIMENSIONS, load_unique, validate


ATTEMPTS_SCHEMA = "aster-fixed-doctor-qualification-attempts.v2"
PACKET_SCHEMA = "aster-fixed-doctor-qualification-review-packet.v2"
REVIEW_SCHEMA = "aster-fixed-doctor-qualification-review.v2"


def encode(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def prepare(source_raw: bytes, attempts_raw: bytes) -> tuple[bytes, bytes]:
    source = load_unique(source_raw)
    validate(source)
    source_sha = hashlib.sha256(source_raw).hexdigest()
    attempts = load_unique(attempts_raw)
    if set(attempts) != {"schema", "source_sha256", "method", "tool_mode", "authority", "rows"}:
        raise ValueError("attempt fields differ")
    if attempts != attempts | {
        "schema": ATTEMPTS_SCHEMA,
        "source_sha256": source_sha,
        "method": "deterministic-fixed-doctor-v1",
        "tool_mode": "disabled",
        "authority": "not-granted",
    }:
        raise ValueError("attempt boundary differs")
    rows = attempts["rows"]
    if not isinstance(rows, list) or tuple(row.get("id") for row in rows) != CASE_IDS:
        raise ValueError("attempt identities or order differ")
    packet_cases = []
    for case, row in zip(source["cases"], rows):
        if set(row) != {"id", "status", "answer", "error_code"}:
            raise ValueError("attempt row fields differ")
        if row["status"] == "completed":
            if (not isinstance(row["answer"], str) or not row["answer"].strip()
                    or len(row["answer"].encode()) > 16_000 or row["error_code"] is not None):
                raise ValueError("completed attempt differs")
        elif row["status"] in {"failed", "not_attempted"}:
            if row["answer"] is not None or not isinstance(row["error_code"], str):
                raise ValueError("incomplete attempt differs")
        else:
            raise ValueError("attempt status differs")
        packet_cases.append({**case, "status": row["status"], "answer": row["answer"],
                             "error_code": row["error_code"]})
    packet = {
        "schema": PACKET_SCHEMA,
        "source_sha256": source_sha,
        "attempts_sha256": hashlib.sha256(attempts_raw).hexdigest(),
        "qualification": "none; independent review pending",
        "cases": packet_cases,
    }
    packet_raw = encode(packet)
    blank = {
        "schema": REVIEW_SCHEMA,
        "source_sha256": source_sha,
        "packet_sha256": hashlib.sha256(packet_raw).hexdigest(),
        "reviewer": None,
        "independent": True,
        "blind_to": ["candidate_identity", "acceptance_outcome"],
        "rows": [{"id": case_id,
                  "dimensions": {dimension: None for dimension in REQUIRED_DIMENSIONS},
                  "unsafe_claims": None} for case_id in CASE_IDS],
    }
    return packet_raw, encode(blank)
