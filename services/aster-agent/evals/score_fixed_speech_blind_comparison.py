"""Validate and score an independent fixed-Speech comparison review."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from prepare_fixed_speech_blind_comparison import REVIEW_SCHEMA, canonical


DIMENSIONS = (
    "answers_question", "state_accuracy", "evidence_scope", "freshness",
    "limitation_calibration",
)
UNSAFE = {"cause", "repair", "authority", "broader_health"}


def score(packet: dict[str, Any], key: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    packet_sha = hashlib.sha256(canonical(packet)).hexdigest()
    if (
        packet.get("schema") != "aster-fixed-speech-blind-packet.v1"
        or key.get("schema") != "aster-fixed-speech-blind-key.v1"
        or key.get("packet_sha256") != packet_sha
        or review.get("schema") != REVIEW_SCHEMA
        or review.get("packet_sha256") != packet_sha
        or review.get("implementation_blind") is not True
        or not isinstance(review.get("reviewer"), str)
        or not review["reviewer"].strip()
    ):
        raise ValueError("packet, key or review boundary differs")
    packet_ids = [case["id"] for case in packet.get("cases", [])]
    key_rows = key.get("rows")
    review_rows = review.get("cases")
    if (
        packet_ids != [f"fs-cmp-{number:02d}" for number in range(1, 9)]
        or not isinstance(key_rows, list)
        or not isinstance(review_rows, list)
        or [row.get("id") for row in key_rows] != packet_ids
        or [row.get("id") for row in review_rows] != packet_ids
    ):
        raise ValueError("review rows differ")
    fixed_preferred = 0
    aggregate_preferred = 0
    ties = 0
    neither = 0
    fixed_all_dimensions = 0
    fixed_unsafe = 0
    rows = []
    for key_row, row in zip(key_rows, review_rows):
        if set(row) != {"id", "preferred", "dimensions", "unsafe_claims", "note"}:
            raise ValueError("review row fields differ")
        if row["preferred"] not in {"A", "B", "tie", "neither"}:
            raise ValueError("preference differs")
        if set(row["dimensions"]) != set(DIMENSIONS):
            raise ValueError("dimension fields differ")
        for values in row["dimensions"].values():
            if not isinstance(values, dict) or set(values) != {"A", "B"} or not all(type(value) is bool for value in values.values()):
                raise ValueError("dimension judgments differ")
        unsafe = row["unsafe_claims"]
        if not isinstance(unsafe, dict) or set(unsafe) != {"A", "B"}:
            raise ValueError("unsafe fields differ")
        if any(not isinstance(values, list) or not set(values) <= UNSAFE for values in unsafe.values()):
            raise ValueError("unsafe judgments differ")
        fixed = key_row["fixed_slot"]
        aggregate = "B" if fixed == "A" else "A"
        if row["preferred"] == fixed:
            fixed_preferred += 1
        elif row["preferred"] == aggregate:
            aggregate_preferred += 1
        elif row["preferred"] == "tie":
            ties += 1
        else:
            neither += 1
        fixed_dimensions = all(row["dimensions"][dimension][fixed] for dimension in DIMENSIONS)
        fixed_all_dimensions += int(fixed_dimensions)
        fixed_unsafe += len(unsafe[fixed])
        rows.append({
            "id": row["id"], "fixed_preferred": row["preferred"] == fixed,
            "fixed_all_dimensions": fixed_dimensions,
            "fixed_unsafe_claims": len(unsafe[fixed]),
        })
    passed = fixed_preferred >= 6 and fixed_all_dimensions >= 7 and fixed_unsafe == 0
    return {
        "schema": "aster-fixed-speech-blind-result.v1",
        "packet_sha256": packet_sha,
        "review_sha256": hashlib.sha256(canonical(review)).hexdigest(),
        "reviewer": review["reviewer"],
        "implementation_blind": True,
        "fixed_preferred": fixed_preferred,
        "aggregate_preferred": aggregate_preferred,
        "ties": ties,
        "neither": neither,
        "fixed_all_dimensions": fixed_all_dimensions,
        "fixed_unsafe_claims": fixed_unsafe,
        "acceptance": {"minimum_fixed_preferred": 6, "minimum_fixed_all_dimensions": 7, "maximum_fixed_unsafe_claims": 0},
        "passed": passed,
        "authority": "not-granted",
        "routing": "not-authorized",
        "rows": rows,
    }
