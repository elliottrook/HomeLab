"""Validate and summarize a completed model-blind D4 development review."""

import argparse
import hashlib
import json
from pathlib import Path

from prepare_sa3_development_review import RUBRIC, canonical_bytes


def score(packet, review, packet_raw=None, expected_cases=12):
    schema = packet.get("schema") if isinstance(packet, dict) else None
    expected_packet_keys = {
        "schema", "candidate_alias", "model_identity_disclosed",
        "timing_disclosed", "ledger_sha256", "rubric", "cases",
    }
    if schema == "aster-d4-model-blind-review-packet.v2":
        expected_packet_keys.add("run_digest")
    if (
        not isinstance(packet, dict)
        or set(packet) != expected_packet_keys
        or schema not in {
            "aster-d4-model-blind-review-packet.v1",
            "aster-d4-model-blind-review-packet.v2",
        }
        or not isinstance(packet["candidate_alias"], str)
        or not packet["candidate_alias"].strip()
        or len(packet["candidate_alias"]) > 64
        or packet["model_identity_disclosed"] is not False
        or packet["timing_disclosed"] is not False
        or packet["rubric"] != list(RUBRIC)
        or not isinstance(packet["cases"], list)
        or len(packet["cases"]) != expected_cases
    ):
        raise ValueError("invalid model-blind packet")
    if schema == "aster-d4-model-blind-review-packet.v2" and (
        not isinstance(packet["run_digest"], str)
        or len(packet["run_digest"]) != 64
        or any(character not in "0123456789abcdef" for character in packet["run_digest"])
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
    result = {
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
    if schema == "aster-d4-model-blind-review-packet.v2":
        result.update(
            run_digest=packet["run_digest"],
            candidate_alias=packet["candidate_alias"],
        )
    return result


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
