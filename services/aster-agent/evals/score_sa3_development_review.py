"""Validate and summarize a completed model-blind D4 development review."""

import argparse
import hashlib
import json
from pathlib import Path

from prepare_sa3_development_review import RUBRIC, canonical_bytes


def score(packet, review, packet_raw=None, expected_cases=12):
    if (
        not isinstance(packet, dict)
        or set(packet) != {
            "schema", "candidate_alias", "model_identity_disclosed",
            "timing_disclosed", "ledger_sha256", "rubric", "cases",
        }
        or packet["schema"] != "aster-d4-model-blind-review-packet.v1"
        or packet["candidate_alias"] != "candidate-A"
        or packet["model_identity_disclosed"] is not False
        or packet["timing_disclosed"] is not False
        or packet["rubric"] != list(RUBRIC)
        or not isinstance(packet["cases"], list)
        or len(packet["cases"]) != expected_cases
    ):
        raise ValueError("invalid model-blind packet")
    packet_sha256 = hashlib.sha256(
        packet_raw if packet_raw is not None else canonical_bytes(packet)
    ).hexdigest()
    if (
        not isinstance(review, dict)
        or set(review) != {
            "schema", "packet_sha256", "reviewer", "model_blind", "cases",
        }
        or review["schema"] != "aster-d4-model-blind-review.v1"
        or review["packet_sha256"] != packet_sha256
        or not isinstance(review["reviewer"], str)
        or not review["reviewer"].strip()
        or review["model_blind"] is not True
        or not isinstance(review["cases"], list)
        or len(review["cases"]) != expected_cases
    ):
        raise ValueError("invalid completed review")
    packet_ids = [case.get("review_id") for case in packet["cases"]]
    review_ids = [case.get("review_id") for case in review["cases"]]
    if (
        packet_ids != review_ids
        or len(set(packet_ids)) != expected_cases
        or any(not isinstance(value, str) or not value for value in packet_ids)
    ):
        raise ValueError("review identity mismatch")
    counts = {field: 0 for field in RUBRIC}
    passed = 0
    rows = []
    for row in review["cases"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"review_id", "judgments", "notes"}
            or not isinstance(row["judgments"], dict)
            or set(row["judgments"]) != set(RUBRIC)
            or any(type(value) is not bool for value in row["judgments"].values())
            or not isinstance(row["notes"], str)
        ):
            raise ValueError("incomplete or invalid review judgment")
        for field in RUBRIC:
            counts[field] += int(row["judgments"][field])
        row_pass = all(row["judgments"].values())
        passed += int(row_pass)
        rows.append({"review_id": row["review_id"], "all_dimensions_pass": row_pass})
    return {
        "schema": "aster-d4-model-blind-review-summary.v1",
        "packet_sha256": packet_sha256,
        "reviewer": review["reviewer"],
        "model_blind": True,
        "cases": expected_cases,
        "all_dimensions_passed": passed,
        "dimension_pass_counts": counts,
        "rows": rows,
        "quality_gate": "not_defined_for_development_set",
        "limit": "development review only; no role, route, tool or deployment promotion",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args(argv)
    packet_raw = args.packet.read_bytes()
    result = score(json.loads(packet_raw), json.loads(args.review.read_text()), packet_raw)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
