"""Prepare a candidate-blind review packet for fixed Doctor answers."""

from __future__ import annotations

import hashlib
import json

from fixed_doctor_usefulness import CASE_IDS, REQUIRED_DIMENSIONS
from fixed_doctor_usefulness_capture import FIXTURE_SHA256, load_fixture
from fixed_doctor_usefulness_score import PACKET_SCHEMA, REVIEW_SCHEMA


def _encode(value: dict) -> bytes:
    return (json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ) + "\n").encode()


def prepare(fixture_raw: bytes, attempts_raw: bytes) -> tuple[bytes, bytes]:
    fixture = load_fixture(fixture_raw)
    try:
        attempts = json.loads(attempts_raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("capture must be UTF-8 JSON") from error
    if (
        not isinstance(attempts, dict)
        or set(attempts) != {
            "schema", "fixture_sha256", "profile_sha256", "tool_mode",
            "authority", "attempts",
        }
        or attempts["schema"] != "aster-fixed-doctor-usefulness-capture.v1"
        or attempts["fixture_sha256"] != FIXTURE_SHA256
        or attempts["tool_mode"] != "disabled"
        or attempts["authority"] != "not-granted"
        or not isinstance(attempts["attempts"], list)
        or tuple(row.get("case_id") for row in attempts["attempts"]) != CASE_IDS
    ):
        raise ValueError("capture boundary differs")
    packet_cases = []
    for case, attempt in zip(fixture["cases"], attempts["attempts"]):
        if set(attempt) != {"case_id", "status", "answer", "error_code", "total_ms"}:
            raise ValueError("capture row fields differ")
        status = attempt["status"]
        if status == "completed":
            if (
                not isinstance(attempt["answer"], str)
                or not attempt["answer"].strip()
                or len(attempt["answer"].encode("utf-8")) > 16_000
                or attempt["error_code"] is not None
            ):
                raise ValueError("completed capture row differs")
        elif status in {"failed", "not_attempted"}:
            if attempt["answer"] is not None or not isinstance(attempt["error_code"], str):
                raise ValueError("incomplete capture row differs")
        else:
            raise ValueError("capture status differs")
        packet_cases.append({
            **case,
            "status": status,
            "answer": attempt["answer"],
            "error_code": attempt["error_code"],
        })
    packet = {
        "schema": PACKET_SCHEMA,
        "fixture_sha256": FIXTURE_SHA256,
        "attempts_sha256": hashlib.sha256(attempts_raw).hexdigest(),
        "qualification": "none; independent review pending",
        "cases": packet_cases,
    }
    packet_raw = _encode(packet)
    blank = {
        "schema": REVIEW_SCHEMA,
        "fixture_sha256": FIXTURE_SHA256,
        "packet_sha256": hashlib.sha256(packet_raw).hexdigest(),
        "reviewer": None,
        "independent": True,
        "blind_to": ["candidate_identity", "acceptance_outcome"],
        "rows": [
            {
                "id": case_id,
                "dimensions": {dimension: None for dimension in REQUIRED_DIMENSIONS},
                "unsafe_claims": None,
            }
            for case_id in CASE_IDS
        ],
    }
    return packet_raw, _encode(blank)
