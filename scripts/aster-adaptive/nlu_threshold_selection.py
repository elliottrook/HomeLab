"""Select an NLU route threshold from a disjoint content-free calibration score.

The selector consumes one already registered policy.  It cannot change its
constraints, candidate, sample minima, or calibration artifact, and it never
reads the independent holdout.  Its output is a frozen policy plus bounded
selection metrics; neither artifact grants routing authority.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import re
from pathlib import Path

from nlu_threshold_policy import (
    FAMILIES,
    decode_unique_json,
    load_and_validate,
    sha256,
    validate_policy,
)


SCORE_SCHEMA = "aster-nlu-calibration-score.v1"
TOP_KEYS = {
    "schema", "candidate_bundle_sha256", "calibration_artifact_sha256",
    "attempt_journal_sha256", "cases",
}
CASE_KEYS = {
    "id",
    "family",
    "route_score",
    "safe_and_correct_if_routed",
    "privacy_underclassified",
    "unsafe_false_route_if_routed",
}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _fraction(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1


def _validate_score(value: object, policy: dict) -> list[str]:
    if not isinstance(value, dict):
        return ["calibration score must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS or value.get("schema") != SCORE_SCHEMA:
        errors.append("invalid calibration score schema")
    if value.get("candidate_bundle_sha256") != policy.get("candidate_bundle_sha256"):
        errors.append("calibration candidate does not match registered policy")
    if value.get("calibration_artifact_sha256") != policy.get("calibration_artifact_sha256"):
        errors.append("calibration artifact does not match registered policy")
    journal_sha = value.get("attempt_journal_sha256")
    if not isinstance(journal_sha, str) or re.fullmatch(r"[0-9a-f]{64}", journal_sha) is None:
        errors.append("invalid calibration attempt journal digest")
    rows = value.get("cases")
    if not isinstance(rows, list):
        return errors + ["calibration cases must be a list"]
    seen: set[str] = set()
    counts = {family: 0 for family in FAMILIES}
    for row in rows:
        if not isinstance(row, dict) or set(row) != CASE_KEYS:
            errors.append("invalid calibration case fields")
            continue
        case_id = row.get("id")
        if not isinstance(case_id, str) or IDENTIFIER.fullmatch(case_id) is None:
            errors.append("invalid calibration case identifier")
        elif case_id in seen:
            errors.append(f"duplicate calibration case identifier: {case_id}")
        else:
            seen.add(case_id)
        family = row.get("family")
        if family not in counts:
            errors.append(f"{case_id}: invalid request family")
        else:
            counts[family] += 1
        if not _fraction(row.get("route_score")):
            errors.append(f"{case_id}: route_score must be in [0, 1]")
        for key in (
            "safe_and_correct_if_routed",
            "privacy_underclassified",
            "unsafe_false_route_if_routed",
        ):
            if type(row.get(key)) is not bool:
                errors.append(f"{case_id}: {key} must be boolean")
    minimum = policy.get("minimum_calibration_cases")
    if type(minimum) is int and len(rows) < minimum:
        errors.append("calibration score is below the registered total minimum")
    per_family = policy.get("minimum_cases_per_family")
    if isinstance(per_family, dict):
        for family in FAMILIES:
            if counts[family] < per_family.get(family, 0):
                errors.append(f"calibration score is below the registered {family} minimum")
    return errors


def select_threshold(registered_policy: dict, score_raw: bytes) -> dict:
    policy_errors = validate_policy(registered_policy)
    if policy_errors or registered_policy.get("status") != "registered":
        raise ValueError("threshold policy must be valid and registered")
    try:
        score = decode_unique_json(score_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("calibration score must be valid UTF-8 JSON") from error
    score_errors = _validate_score(score, registered_policy)
    if score_errors:
        raise ValueError("; ".join(score_errors))

    rows = score["cases"]
    constraints = registered_policy["constraints"]
    candidates = sorted({0.0, 1.0, *(float(row["route_score"]) for row in rows)})
    eligible: list[tuple[float, float, dict]] = []
    for threshold in candidates:
        routed = [row for row in rows if row["route_score"] >= threshold]
        coverage = len(routed) / len(rows)
        errors = sum(not row["safe_and_correct_if_routed"] for row in routed)
        error_rate = errors / len(routed) if routed else 0.0
        metrics = {
            "threshold": threshold,
            "routed": len(routed),
            "total": len(rows),
            "coverage": round(coverage, 12),
            "selective_error_rate": round(error_rate, 12),
            "privacy_underclassification": sum(row["privacy_underclassified"] for row in routed),
            "unsafe_false_route": sum(row["unsafe_false_route_if_routed"] for row in routed),
        }
        if (
            coverage >= constraints["minimum_coverage"]
            and error_rate <= constraints["max_selective_error_rate"]
            and metrics["privacy_underclassification"] <= constraints["max_privacy_underclassification"]
            and metrics["unsafe_false_route"] <= constraints["max_unsafe_false_route"]
        ):
            eligible.append((metrics["coverage"], threshold, metrics))
    if not eligible:
        raise ValueError("no calibration threshold satisfies the registered constraints")
    _, threshold, metrics = max(eligible, key=lambda item: (item[0], item[1]))
    frozen = copy.deepcopy(registered_policy)
    frozen.update(
        status="frozen",
        calibration_score_sha256=sha256(score_raw),
        selected_threshold=threshold,
    )
    if validate_policy(frozen):
        raise ValueError("selected threshold did not produce a valid frozen policy")
    return {
        "schema": "aster-nlu-threshold-selection.v1",
        "policy": frozen,
        "selection_metrics": metrics,
        "limits": [
            "disjoint calibration selection only; independent holdout not accessed",
            "evaluation score is not authorization or calibrated execution confidence",
            "no routing, egress, tool use or execution granted",
        ],
    }


def canonical_json(value: object) -> bytes:
    """Encode a selection artifact deterministically for independent hashing."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_new_private(path: Path, payload: bytes) -> None:
    """Create one owner-only output without replacing prior evidence."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze an NLU threshold from a registered policy and content-free calibration score."
    )
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        policy_raw = args.policy.read_bytes()
    except OSError as error:
        parser.error(f"cannot read registered policy: {error}")
    registered_policy, policy_errors = load_and_validate(policy_raw)
    if policy_errors or registered_policy is None:
        parser.error("cannot read registered policy: " + "; ".join(policy_errors))
    try:
        score_raw = args.score.read_bytes()
    except OSError as error:
        parser.error(f"cannot read calibration score: {error}")

    try:
        result = select_threshold(registered_policy, score_raw)
        output_raw = canonical_json(result)
        write_new_private(args.output, output_raw)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(json.dumps({
        "schema": result["schema"],
        "status": result["policy"]["status"],
        "selected_threshold": result["policy"]["selected_threshold"],
        "output_sha256": sha256(output_raw),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
