"""Validate NLU confidence policy v2 registration and threshold state."""
from __future__ import annotations

import json
import math
import re

from nlu_threshold_policy import FAMILIES, decode_unique_json, sha256


SCHEMA = "aster-nlu-threshold-policy.v2"
TOP_KEYS = {
    "schema", "status", "policy_id", "contract_schema", "selection_partition",
    "coverage_semantics", "route_effect_semantics", "selection_rule",
    "constraints", "tie_breaker", "minimum_calibration_cases",
    "minimum_cases_per_family", "candidate_bundle_sha256",
    "calibration_artifact_sha256", "calibration_score_sha256",
    "selected_thresholds", "holdout_accessed", "authority",
}
CONSTRAINT_KEYS = {
    "max_privacy_underclassification_on_routed", "max_unsafe_false_route",
    "max_accepted_decision_error_rate", "minimum_decision_coverage",
}
THRESHOLD_KEYS = {"decision", "route"}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _fraction(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def validate_policy(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["threshold policy must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("threshold policy fields must match the fixed v2 schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid threshold policy schema")
    if value.get("status") not in {"registered", "frozen"}:
        errors.append("status must be registered or frozen")
    if not isinstance(value.get("policy_id"), str) or IDENTIFIER.fullmatch(value.get("policy_id", "")) is None:
        errors.append("invalid threshold policy identifier")
    if value.get("contract_schema") != "request-interpretation.v1":
        errors.append("unsupported NLU contract schema")
    if value.get("selection_partition") != "disjoint-calibration":
        errors.append("threshold selection must use disjoint calibration evidence")
    if value.get("coverage_semantics") != "accepted-decision-confidence":
        errors.append("coverage must count accepted decisions")
    if value.get("route_effect_semantics") != "separate-zero-tolerance-gate":
        errors.append("route effects require a separate safety gate")
    if value.get("selection_rule") != "maximize-decision-coverage-subject-to-all-constraints":
        errors.append("unsupported threshold selection rule")
    if value.get("tie_breaker") != "highest-decision-then-route-thresholds":
        errors.append("unsupported deterministic tie breaker")
    if value.get("holdout_accessed") is not False:
        errors.append("threshold policy must attest that holdout was not accessed")
    if value.get("authority") != "not-granted":
        errors.append("threshold policy must not grant authority")

    constraints = value.get("constraints")
    if not isinstance(constraints, dict) or set(constraints) != CONSTRAINT_KEYS:
        errors.append("invalid v2 safety constraints")
        constraints = {}
    if constraints.get("max_privacy_underclassification_on_routed") != 0:
        errors.append("routed privacy underclassification tolerance must be zero")
    if constraints.get("max_unsafe_false_route") != 0:
        errors.append("unsafe false-route tolerance must be zero")
    if not _fraction(constraints.get("max_accepted_decision_error_rate")) or constraints.get(
        "max_accepted_decision_error_rate", 1
    ) >= 1:
        errors.append("accepted decisions require a non-vacuous error limit")
    if not _fraction(constraints.get("minimum_decision_coverage")) or constraints.get(
        "minimum_decision_coverage", 0
    ) <= 0:
        errors.append("decision coverage must be positive")

    minimum = value.get("minimum_calibration_cases")
    per_family = value.get("minimum_cases_per_family")
    if type(minimum) is not int or minimum <= 0:
        errors.append("policy requires a positive calibration sample minimum")
    if not isinstance(per_family, dict) or set(per_family) != set(FAMILIES):
        errors.append("policy requires minima for every request family")
    elif any(type(count) is not int or count <= 0 for count in per_family.values()):
        errors.append("family calibration minima must be positive integers")
    elif type(minimum) is int and sum(per_family.values()) > minimum:
        errors.append("family minima cannot exceed the total calibration minimum")
    for key in ("candidate_bundle_sha256", "calibration_artifact_sha256"):
        if not _digest(value.get(key)):
            errors.append(f"policy requires {key}")

    if value.get("status") == "registered":
        if value.get("calibration_score_sha256"):
            errors.append("registered policy must not claim calibration_score_sha256")
        if value.get("selected_thresholds") is not None:
            errors.append("registered policy must not claim selected thresholds")
    else:
        if not _digest(value.get("calibration_score_sha256")):
            errors.append("frozen policy requires calibration_score_sha256")
        thresholds = value.get("selected_thresholds")
        if not isinstance(thresholds, dict) or set(thresholds) != THRESHOLD_KEYS:
            errors.append("frozen policy requires decision and route thresholds")
        elif not all(_fraction(thresholds[key]) for key in THRESHOLD_KEYS):
            errors.append("frozen thresholds must be in [0, 1]")
    return errors


def load_and_validate(raw: bytes) -> tuple[dict | None, list[str]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["threshold policy must be valid unique-key UTF-8 JSON"]
    errors = validate_policy(value)
    return value if isinstance(value, dict) else None, errors
