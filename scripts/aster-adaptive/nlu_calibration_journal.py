"""Validate the content-free NLU calibration attempt journal against a run."""

from __future__ import annotations

import json

from nlu_threshold_policy import decode_unique_json


START_KEYS = {
    "event", "schema", "candidate_bundle_sha256",
    "calibration_artifact_sha256", "planned", "authority",
}


def _rows(raw: bytes) -> list[dict]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("calibration journal must be UTF-8 JSONL") from error
    lines = text.splitlines()
    if not lines or any(not line for line in lines):
        raise ValueError("calibration journal must contain nonempty JSONL rows")
    rows = []
    for line in lines:
        try:
            value = decode_unique_json(line.encode())
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            raise ValueError("calibration journal rows must be unique-key JSON") from error
        if not isinstance(value, dict):
            raise ValueError("calibration journal rows must be objects")
        rows.append(value)
    return rows


def validate_journal(raw: bytes, run: dict) -> None:
    rows = _rows(raw)
    start = rows.pop(0)
    if set(start) != START_KEYS or start != {
        "event": "run_started",
        "schema": "aster-nlu-calibration-attempt-journal.v1",
        "candidate_bundle_sha256": run["candidate_bundle_sha256"],
        "calibration_artifact_sha256": run["calibration_artifact_sha256"],
        "planned": 60,
        "authority": "not-granted",
    }:
        raise ValueError("calibration journal start boundary changed")
    records = run["records"]
    if len(rows) != len(records) * 2 + 1:
        raise ValueError("calibration journal does not cover the exact run")
    seen: set[str] = set()
    for index, record in enumerate(records):
        started, recorded = rows[index * 2:index * 2 + 2]
        case_id = record["id"]
        if started != {"event": "attempt_started", "case_id": case_id}:
            raise ValueError("calibration journal attempt start mismatch")
        expected = {
            "event": "attempt_recorded",
            "case_id": case_id,
            "valid": record["valid"],
        }
        if not record["valid"]:
            if (
                record.get("failure"), record.get("error_type")
            ) != ("invalid_response", "response_invalid"):
                raise ValueError(
                    "infrastructure failure cannot have a complete calibration journal"
                )
            expected["error_type"] = record["error_type"]
        if recorded != expected:
            raise ValueError("calibration journal attempt result mismatch")
        if case_id in seen:
            raise ValueError("calibration journal repeats a case")
        seen.add(case_id)
    if rows[-1] != {
        "event": "run_finished", "attempted": len(records), "complete": True
    }:
        raise ValueError("calibration journal terminal boundary changed")
