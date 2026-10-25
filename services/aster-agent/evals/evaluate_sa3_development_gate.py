"""Apply one frozen D4 development rule to a model-blind review summary."""

import argparse
import hashlib
import json
from pathlib import Path

from prepare_sa3_development_review import RUBRIC, canonical_bytes


RULE_KEYS = {
    "schema", "status", "candidate_alias", "expected_run_digest",
    "expected_cases", "minimum_all_dimensions_passed",
    "minimum_dimension_pass_counts", "pass_outcome", "failure_outcome",
    "authority",
}
SUMMARY_KEYS = {
    "schema", "packet_sha256", "reviewer", "model_blind", "cases",
    "all_dimensions_passed", "dimension_pass_counts", "rows",
    "quality_gate", "limit", "run_digest", "candidate_alias",
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def evaluate(rule, summary, rule_raw=None):
    if (
        not isinstance(rule, dict)
        or set(rule) != RULE_KEYS
        or rule.get("schema") != "aster-d4-development-decision-rule.v1"
        or rule.get("status") != "frozen"
        or rule.get("authority") != "not-granted"
        or not isinstance(rule.get("candidate_alias"), str)
        or not rule["candidate_alias"].strip()
        or not isinstance(rule.get("expected_run_digest"), str)
        or len(rule["expected_run_digest"]) != 64
        or any(character not in "0123456789abcdef" for character in rule["expected_run_digest"])
        or type(rule.get("expected_cases")) is not int
        or rule["expected_cases"] <= 0
        or type(rule.get("minimum_all_dimensions_passed")) is not int
        or not 0 <= rule["minimum_all_dimensions_passed"] <= rule["expected_cases"]
        or set(rule.get("minimum_dimension_pass_counts", {})) != set(RUBRIC)
        or any(type(value) is not int or not 0 <= value <= rule["expected_cases"]
               for value in rule["minimum_dimension_pass_counts"].values())
        or not isinstance(rule.get("pass_outcome"), str)
        or not rule["pass_outcome"].strip()
        or not isinstance(rule.get("failure_outcome"), str)
        or not rule["failure_outcome"].strip()
    ):
        raise ValueError("invalid frozen development decision rule")
    if (
        not isinstance(summary, dict)
        or set(summary) != SUMMARY_KEYS
        or summary.get("schema") != "aster-d4-model-blind-review-summary.v1"
        or summary.get("model_blind") is not True
        or summary.get("run_digest") != rule["expected_run_digest"]
        or summary.get("candidate_alias") != rule["candidate_alias"]
        or summary.get("cases") != rule["expected_cases"]
        or type(summary.get("all_dimensions_passed")) is not int
        or set(summary.get("dimension_pass_counts", {})) != set(RUBRIC)
        or any(type(value) is not int or not 0 <= value <= rule["expected_cases"]
               for value in summary["dimension_pass_counts"].values())
        or not isinstance(summary.get("rows"), list)
        or len(summary["rows"]) != rule["expected_cases"]
    ):
        raise ValueError("review summary does not match frozen development rule")
    review_ids = []
    row_passes = 0
    for row in summary["rows"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"review_id", "all_dimensions_pass"}
            or not isinstance(row["review_id"], str)
            or type(row["all_dimensions_pass"]) is not bool
        ):
            raise ValueError("invalid bounded review row")
        review_ids.append(row["review_id"])
        row_passes += int(row["all_dimensions_pass"])
    if len(set(review_ids)) != rule["expected_cases"] or row_passes != summary["all_dimensions_passed"]:
        raise ValueError("review row identity or count mismatch")

    failed_dimensions = [
        field for field in RUBRIC
        if summary["dimension_pass_counts"][field]
        < rule["minimum_dimension_pass_counts"][field]
    ]
    passed = (
        summary["all_dimensions_passed"] >= rule["minimum_all_dimensions_passed"]
        and not failed_dimensions
    )
    encoded_rule = rule_raw if rule_raw is not None else canonical_bytes(rule)
    return {
        "schema": "aster-d4-development-gate-result.v1",
        "candidate_alias": rule["candidate_alias"],
        "run_digest": rule["expected_run_digest"],
        "rule_sha256": sha256(encoded_rule),
        "decision": "pass" if passed else "no-go",
        "outcome": rule["pass_outcome"] if passed else rule["failure_outcome"],
        "all_dimensions_passed": summary["all_dimensions_passed"],
        "failed_dimensions": failed_dimensions,
        "authority": "not-granted",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("rule", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--expected-rule-sha256", required=True)
    args = parser.parse_args(argv)
    rule_raw = args.rule.read_bytes()
    if sha256(rule_raw) != args.expected_rule_sha256:
        parser.error("development decision rule does not match the preregistered digest")
    result = evaluate(json.loads(rule_raw), json.loads(args.summary.read_text()), rule_raw)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
