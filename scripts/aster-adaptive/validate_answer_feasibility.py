"""Validate a public synthetic answer-feasibility fixture without model calls.

Structural validation is not a privacy review or semantic label adjudication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

CLASSES = {"grounded_public_fact", "private_calendar", "mixed_public_private",
           "homelab_status", "ambiguous_household"}
PRIVACY = {"public_synthetic", "local_only_synthetic", "local_join_synthetic",
           "sanitized_synthetic"}


def timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be UTC")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc


def text_list(value: object, minimum: int, maximum: int) -> bool:
    return (isinstance(value, list) and minimum <= len(value) <= maximum
            and all(isinstance(item, str) and 1 <= len(item) <= 500 for item in value))


def validate(raw: bytes) -> dict:
    fixture = json.loads(raw)
    if not isinstance(fixture, dict) or set(fixture) != {
        "schema_version", "data_class", "tool_mode", "purpose", "cases"}:
        raise ValueError("invalid fixture envelope")
    if (fixture["schema_version"] != "aster-answer-feasibility.v0"
            or fixture["data_class"] != "synthetic-public-development"
            or fixture["tool_mode"] != "disabled"
            or fixture["purpose"] != "adapter-and-rubric-feasibility-only"):
        raise ValueError("fixture scope changed")
    cases = fixture["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
        raise ValueError("invalid case count")
    ids = set()
    counts = {}
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id", "class", "request", "clock", "privacy", "context", "rubric", "prohibited_claims"}:
            raise ValueError("invalid case fields")
        case_id = case["id"]
        if (not isinstance(case_id, str) or not case_id.isascii()
                or not 1 <= len(case_id) <= 64 or case_id in ids):
            raise ValueError("invalid or duplicate case ID")
        ids.add(case_id)
        if case["class"] not in CLASSES or case["privacy"] not in PRIVACY:
            raise ValueError("unknown class or privacy tag")
        if not isinstance(case["request"], str) or not 1 <= len(case["request"]) <= 500:
            raise ValueError("invalid request")
        if not text_list(case["rubric"], 1, 6) or not text_list(case["prohibited_claims"], 1, 6):
            raise ValueError("invalid review rubric")
        now = timestamp(case["clock"])
        sources = case["context"]
        if not isinstance(sources, list) or len(sources) > 4:
            raise ValueError("invalid context count")
        source_ids = set()
        for source in sources:
            if not isinstance(source, dict) or set(source) != {"source_id", "observed_at", "text"}:
                raise ValueError("invalid source fields")
            source_id = source["source_id"]
            if (not isinstance(source_id, str) or not source_id.isascii()
                    or not 1 <= len(source_id) <= 64 or source_id in source_ids):
                raise ValueError("invalid or duplicate source ID")
            source_ids.add(source_id)
            if timestamp(source["observed_at"]) > now:
                raise ValueError("source observation is in the future")
            if not isinstance(source["text"], str) or not 1 <= len(source["text"]) <= 500:
                raise ValueError("invalid source text")
        counts[case["class"]] = counts.get(case["class"], 0) + 1
    return {"schema": fixture["schema_version"], "sha256": hashlib.sha256(raw).hexdigest(),
            "cases": len(cases), "classes": dict(sorted(counts.items())),
            "limits": "structural validation only; no privacy or answer-quality claim"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.fixture.read_bytes()), sort_keys=True))


if __name__ == "__main__":
    main()
