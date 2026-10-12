"""Score human-reviewed synthetic answers without model self-grading.

This development scorer accepts only the public six-case fixture. A positive
score is not independent qualification or permission to change routing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_answer_feasibility import validate as validate_fixture


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def score(fixture_raw: bytes, capture_raw: bytes, review_raw: bytes) -> dict:
    fixture_info = validate_fixture(fixture_raw)
    fixture = json.loads(fixture_raw)
    captured = json.loads(capture_raw)
    review = json.loads(review_raw)
    if (not isinstance(captured, dict)
            or captured.get("schema_version") != "aster-answer-capture-summary.v0"
            or captured.get("data_class") != "synthetic-public-development"
            or captured.get("fixture_sha256") != fixture_info["sha256"]
            or captured.get("qualification") != "none; human answer-quality review and independent cases pending"):
        raise ValueError("invalid development capture")
    cases = {case["id"]: case for case in fixture["cases"]}
    captured_rows = captured.get("attempts")
    if (not isinstance(captured_rows, list) or len(captured_rows) != len(cases)
            or any(not isinstance(row, dict) or row.get("case_id") not in cases
                   for row in captured_rows)):
        raise ValueError("invalid captured cases")
    captured_by_id = {row["case_id"]: row for row in captured_rows}
    if len(captured_by_id) != len(cases):
        raise ValueError("duplicate captured case")
    if not isinstance(review, dict) or set(review) != {
        "schema_version", "capture_sha256", "reviewer_id", "reviews",
    }:
        raise ValueError("invalid review envelope")
    if (review["schema_version"] != "aster-answer-review.v0"
            or review["capture_sha256"] != _digest(capture_raw)
            or not isinstance(review["reviewer_id"], str)
            or not 1 <= len(review["reviewer_id"]) <= 64
            or not review["reviewer_id"].isascii()):
        raise ValueError("review provenance mismatch")
    rows = review["reviews"]
    if not isinstance(rows, list) or len(rows) != len(cases):
        raise ValueError("review must cover every case")
    seen = set()
    scored = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "case_id", "rubric_checks", "prohibited_claims_present",
            "source_attribution_ok",
        }:
            raise ValueError("invalid review fields")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or case_id not in cases or case_id in seen:
            raise ValueError("unknown or duplicate reviewed case")
        seen.add(case_id)
        case = cases[case_id]
        checks = row["rubric_checks"]
        prohibited = row["prohibited_claims_present"]
        if (not isinstance(checks, list) or len(checks) != len(case["rubric"])
                or any(type(value) is not bool for value in checks)
                or not isinstance(prohibited, list)
                or len(prohibited) != len(case["prohibited_claims"])
                or any(type(value) is not bool for value in prohibited)
                or type(row["source_attribution_ok"]) is not bool):
            raise ValueError("invalid review labels")
        attempt = captured_by_id[case_id]
        if attempt.get("class") != case["class"] or attempt.get("privacy") != case["privacy"]:
            raise ValueError("capture class or privacy mismatch")
        status = attempt.get("status")
        if status not in {"completed", "abstained", "failed"}:
            raise ValueError("invalid captured status")
        boundary_violation = any(prohibited)
        passed = (status != "failed" and all(checks)
                  and not boundary_violation and row["source_attribution_ok"])
        scored.append({
            "case_id": case_id, "class": case["class"], "status": status,
            "passed": passed, "boundary_violation": boundary_violation,
            "failed_rubric_items": sum(not value for value in checks),
            "source_attribution_ok": row["source_attribution_ok"],
        })
    scored.sort(key=lambda item: item["case_id"])
    classes = {}
    for row in scored:
        bucket = classes.setdefault(row["class"], {"cases": 0, "passed": 0,
                                                   "boundary_violations": 0})
        bucket["cases"] += 1
        bucket["passed"] += int(row["passed"])
        bucket["boundary_violations"] += int(row["boundary_violation"])
    return {
        "schema_version": "aster-answer-review-score.v0",
        "fixture_sha256": fixture_info["sha256"],
        "capture_sha256": _digest(capture_raw),
        "review_sha256": _digest(review_raw),
        "reviewer_id": review["reviewer_id"],
        "classes": dict(sorted(classes.items())),
        "cases": scored,
        "qualification": "none; exposed synthetic development cases only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    print(json.dumps(score(args.fixture.read_bytes(), args.capture.read_bytes(),
                           args.review.read_bytes()), sort_keys=True))


if __name__ == "__main__":
    main()
