"""Select separate NLU decision and route thresholds under policy v2."""
from __future__ import annotations

import copy
import json
import math
import re

from nlu_threshold_policy import FAMILIES, decode_unique_json, sha256
from nlu_threshold_policy_v2 import validate_policy


SCORE_SCHEMA = "aster-nlu-calibration-score.v2"
CASE_KEYS = {
    "id", "family", "decision_score", "route_score", "proposes_route",
    "accepted_decision_correct", "privacy_underclassified_if_routed",
    "unsafe_false_route_if_routed",
}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _fraction(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1


def _validate_score(value: object, policy: dict) -> list[str]:
    if not isinstance(value, dict) or set(value) != {
        "schema", "candidate_bundle_sha256", "calibration_artifact_sha256",
        "attempt_journal_sha256", "cases",
    } or value.get("schema") != SCORE_SCHEMA:
        return ["invalid v2 calibration score schema"]
    errors: list[str] = []
    if value.get("candidate_bundle_sha256") != policy.get("candidate_bundle_sha256"):
        errors.append("calibration candidate does not match registered policy")
    if value.get("calibration_artifact_sha256") != policy.get("calibration_artifact_sha256"):
        errors.append("calibration artifact does not match registered policy")
    if not isinstance(value.get("attempt_journal_sha256"), str) or re.fullmatch(
        r"[0-9a-f]{64}", value.get("attempt_journal_sha256", "")
    ) is None:
        errors.append("invalid calibration attempt journal digest")
    rows = value.get("cases")
    if not isinstance(rows, list):
        return errors + ["calibration cases must be a list"]
    seen: set[str] = set()
    counts = {family: 0 for family in FAMILIES}
    for row in rows:
        if not isinstance(row, dict) or set(row) != CASE_KEYS:
            errors.append("invalid v2 calibration case fields")
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
        for key in ("decision_score", "route_score"):
            if not _fraction(row.get(key)):
                errors.append(f"{case_id}: {key} must be in [0, 1]")
        for key in CASE_KEYS - {"id", "family", "decision_score", "route_score"}:
            if type(row.get(key)) is not bool:
                errors.append(f"{case_id}: {key} must be boolean")
    if len(rows) < policy.get("minimum_calibration_cases", 0):
        errors.append("calibration score is below the registered total minimum")
    for family in FAMILIES:
        if counts[family] < policy.get("minimum_cases_per_family", {}).get(family, 0):
            errors.append(f"calibration score is below the registered {family} minimum")
    return errors


def select_thresholds(registered_policy: dict, score_raw: bytes) -> dict:
    if validate_policy(registered_policy) or registered_policy.get("status") != "registered":
        raise ValueError("confidence policy must be valid and registered")
    try:
        score = decode_unique_json(score_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("calibration score must be valid unique-key UTF-8 JSON") from error
    errors = _validate_score(score, registered_policy)
    if errors:
        raise ValueError("; ".join(errors))
    rows = score["cases"]
    constraints = registered_policy["constraints"]
    decision_candidates = sorted({0.0, 1.0, *(float(row["decision_score"]) for row in rows)})
    route_candidates = sorted({0.0, 1.0, *(float(row["route_score"]) for row in rows)})
    eligible: list[tuple[float, float, float, dict]] = []
    for decision_threshold in decision_candidates:
        for route_threshold in route_candidates:
            accepted = [row for row in rows if row["decision_score"] >= decision_threshold and (
                not row["proposes_route"] or row["route_score"] >= route_threshold
            )]
            routed = [row for row in accepted if row["proposes_route"]]
            coverage = len(accepted) / len(rows)
            decision_errors = sum(not row["accepted_decision_correct"] for row in accepted)
            error_rate = decision_errors / len(accepted) if accepted else 0.0
            privacy = sum(row["privacy_underclassified_if_routed"] for row in routed)
            unsafe = sum(row["unsafe_false_route_if_routed"] for row in routed)
            metrics = {
                "decision_threshold": decision_threshold,
                "route_threshold": route_threshold,
                "accepted_decisions": len(accepted), "routed": len(routed),
                "total": len(rows), "decision_coverage": round(coverage, 12),
                "accepted_decision_error_rate": round(error_rate, 12),
                "privacy_underclassification_on_routed": privacy,
                "unsafe_false_route": unsafe,
            }
            if (
                coverage >= constraints["minimum_decision_coverage"]
                and error_rate <= constraints["max_accepted_decision_error_rate"]
                and privacy <= constraints["max_privacy_underclassification_on_routed"]
                and unsafe <= constraints["max_unsafe_false_route"]
            ):
                eligible.append((coverage, decision_threshold, route_threshold, metrics))
    if not eligible:
        raise ValueError("no decision/route threshold pair satisfies the registered constraints")
    _, decision_threshold, route_threshold, metrics = max(
        eligible, key=lambda item: (item[0], item[1], item[2])
    )
    frozen = copy.deepcopy(registered_policy)
    frozen.update(
        status="frozen", calibration_score_sha256=sha256(score_raw),
        selected_thresholds={"decision": decision_threshold, "route": route_threshold},
    )
    if validate_policy(frozen):
        raise ValueError("selected thresholds did not produce a valid frozen policy")
    return {
        "schema": "aster-nlu-threshold-selection.v2", "policy": frozen,
        "selection_metrics": metrics,
        "limits": [
            "disjoint calibration only; independent holdout not accessed",
            "accepted decision confidence is separate from routed effects",
            "no routing, egress, tool use or execution granted",
        ],
    }
