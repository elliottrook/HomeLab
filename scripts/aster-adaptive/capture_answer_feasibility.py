"""Project synthetic answer attempts into a content-free development record.

This is a structural capture check, not a semantic scorer or release gate.
It accepts only the public synthetic fixture and never emits answer text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from validate_answer_feasibility import validate as validate_fixture

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
STATUSES = {"completed", "abstained", "failed"}
ERROR_CODES = {"timeout", "unavailable", "invalid_output", "other"}


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _milliseconds(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 600_000:
        raise ValueError("invalid duration")
    return value


def capture(fixture_raw: bytes, attempts_raw: bytes) -> dict:
    fixture_info = validate_fixture(fixture_raw)
    fixture = json.loads(fixture_raw)
    attempts = json.loads(attempts_raw)
    if not isinstance(attempts, dict) or set(attempts) != {
        "schema_version", "fixture_sha256", "candidate_profile_sha256",
        "tool_mode", "attempts",
    }:
        raise ValueError("invalid capture envelope")
    if (attempts["schema_version"] != "aster-answer-capture.v0"
            or attempts["fixture_sha256"] != fixture_info["sha256"]
            or attempts["tool_mode"] != "disabled"
            or not isinstance(attempts["candidate_profile_sha256"], str)
            or not HEX64.fullmatch(attempts["candidate_profile_sha256"])):
        raise ValueError("capture scope or provenance mismatch")
    case_map = {case["id"]: case for case in fixture["cases"]}
    rows = attempts["attempts"]
    if not isinstance(rows, list) or len(rows) != len(case_map):
        raise ValueError("capture must cover each fixture case once")
    seen = set()
    projected = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "case_id", "status", "answer", "source_ids", "error_code",
            "route_ms", "context_ms", "inference_ms", "total_ms",
        }:
            raise ValueError("invalid attempt fields")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or case_id not in case_map or case_id in seen:
            raise ValueError("unknown or duplicate case")
        seen.add(case_id)
        status = row["status"]
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("invalid status")
        answer = row["answer"]
        if not isinstance(answer, str) or len(answer.encode("utf-8")) > 16_000:
            raise ValueError("invalid answer")
        if (status == "completed" and not answer.strip()) or (status == "failed" and answer):
            raise ValueError("answer/status mismatch")
        code = row["error_code"]
        if (status == "failed" and (not isinstance(code, str) or code not in ERROR_CODES)) or (status != "failed" and code is not None):
            raise ValueError("error/status mismatch")
        source_ids = row["source_ids"]
        permitted = {source["source_id"] for source in case_map[case_id]["context"]}
        if (not isinstance(source_ids, list)
                or any(not isinstance(source_id, str) for source_id in source_ids)
                or len(source_ids) != len(set(source_ids))
                or any(source_id not in permitted for source_id in source_ids)):
            raise ValueError("unknown or duplicate source attribution")
        timing = {field: _milliseconds(row[field]) for field in
                  ("route_ms", "context_ms", "inference_ms", "total_ms")}
        if timing["total_ms"] < max(timing["route_ms"], timing["context_ms"],
                                     timing["inference_ms"]):
            raise ValueError("total duration shorter than a component")
        projected.append({
            "case_id": case_id,
            "class": case_map[case_id]["class"],
            "privacy": case_map[case_id]["privacy"],
            "status": status,
            "answer_bytes": len(answer.encode("utf-8")),
            "source_ids": source_ids,
            "error_code": code,
            **timing,
            "human_review": "pending",
        })
    projected.sort(key=lambda item: item["case_id"])
    return {
        "schema_version": "aster-answer-capture-summary.v0",
        "data_class": "synthetic-public-development",
        "fixture_sha256": fixture_info["sha256"],
        "attempts_sha256": _digest(attempts_raw),
        "candidate_profile_sha256": attempts["candidate_profile_sha256"],
        "attempts": projected,
        "qualification": "none; human answer-quality review and independent cases pending",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("attempts", type=Path)
    args = parser.parse_args()
    print(json.dumps(capture(args.fixture.read_bytes(), args.attempts.read_bytes()),
                     sort_keys=True))


if __name__ == "__main__":
    main()
