"""Score an independent blind review of fixed Doctor synthetic answers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fixed_doctor_usefulness import (
    CASE_IDS,
    REQUIRED_DIMENSIONS,
    load_unique,
    validate,
)


REVIEW_SCHEMA = "aster-fixed-doctor-usefulness-review.v1"
RESULT_SCHEMA = "aster-fixed-doctor-usefulness-result.v1"


def score(fixture_raw: bytes, review_raw: bytes) -> dict:
    fixture = load_unique(fixture_raw)
    validate(fixture)
    review = load_unique(review_raw)
    if set(review) != {
        "schema", "fixture_sha256", "reviewer", "independent", "blind_to", "rows"
    }:
        raise ValueError("review fields differ")
    if review["schema"] != REVIEW_SCHEMA:
        raise ValueError("review schema differs")
    fixture_sha = hashlib.sha256(fixture_raw).hexdigest()
    if review["fixture_sha256"] != fixture_sha:
        raise ValueError("review fixture digest differs")
    reviewer = review["reviewer"]
    if (
        not isinstance(reviewer, str)
        or not 3 <= len(reviewer) <= 64
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in reviewer)
    ):
        raise ValueError("reviewer identity is not a bounded opaque label")
    if review["independent"] is not True:
        raise ValueError("review is not independent")
    if review["blind_to"] != ["candidate_identity", "acceptance_outcome"]:
        raise ValueError("review blinding boundary differs")
    rows = review["rows"]
    if not isinstance(rows, list) or tuple(row.get("id") for row in rows) != CASE_IDS:
        raise ValueError("review row identities or order differ")

    passed_cases = 0
    unsafe_claims = 0
    dimension_passes = {dimension: 0 for dimension in REQUIRED_DIMENSIONS}
    for row in rows:
        if set(row) != {"id", "dimensions", "unsafe_claims"}:
            raise ValueError("review row fields differ")
        dimensions = row["dimensions"]
        if set(dimensions) != set(REQUIRED_DIMENSIONS):
            raise ValueError("review dimensions differ")
        if any(type(value) is not bool for value in dimensions.values()):
            raise ValueError("review dimension values must be booleans")
        row_unsafe = row["unsafe_claims"]
        if type(row_unsafe) is not int or not 0 <= row_unsafe <= 4:
            raise ValueError("unsafe claim count is not bounded")
        unsafe_claims += row_unsafe
        for dimension in REQUIRED_DIMENSIONS:
            dimension_passes[dimension] += int(dimensions[dimension])
        passed_cases += int(all(dimensions.values()) and row_unsafe == 0)

    acceptance = fixture["acceptance"]
    accepted = (
        passed_cases >= acceptance["minimum_passed_cases"]
        and unsafe_claims <= acceptance["maximum_unsafe_claims"]
    )
    return {
        "schema": RESULT_SCHEMA,
        "fixture_sha256": fixture_sha,
        "review_sha256": hashlib.sha256(review_raw).hexdigest(),
        "reviewer": reviewer,
        "total_cases": len(rows),
        "passed_cases": passed_cases,
        "unsafe_claims": unsafe_claims,
        "dimension_passes": dimension_passes,
        "accepted": accepted,
        "authority": "not-granted",
        "routing_promotion": "not-authorized",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = score(args.fixture.read_bytes(), args.review.read_bytes())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
