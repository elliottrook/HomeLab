"""Validate the proposed NLU confidence policy with separate route safety."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re

from nlu_threshold_policy import FAMILIES, decode_unique_json


SCHEMA = "aster-nlu-policy-decision.v2"
TOP_KEYS = {
    "schema", "status", "decision_id", "coverage_semantics",
    "route_effect_semantics", "selection_rule", "tie_breaker", "constraints",
    "minimum_calibration_cases", "minimum_cases_per_family",
    "acceptance_record_sha256", "decision_sha256", "authority",
}
CONSTRAINT_KEYS = {
    "max_privacy_underclassification_on_routed",
    "max_unsafe_false_route",
    "max_accepted_decision_error_rate",
    "minimum_decision_coverage",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _fraction(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("decision_sha256", None)
    raw = json.dumps(copied, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_decision(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["policy decision must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("policy decision fields must match the fixed v2 schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid policy decision schema")
    if value.get("status") not in {"proposed", "accepted"}:
        errors.append("status must be proposed or accepted")
    if not isinstance(value.get("decision_id"), str) or IDENTIFIER.fullmatch(
        value.get("decision_id", "")
    ) is None:
        errors.append("invalid policy decision identifier")
    if value.get("coverage_semantics") != "accepted-decision-confidence":
        errors.append("coverage must count accepted NLU decisions")
    if value.get("route_effect_semantics") != "separate-zero-tolerance-gate":
        errors.append("route effects require a separate safety gate")
    if value.get("selection_rule") != "maximize-decision-coverage-subject-to-all-constraints":
        errors.append("unsupported threshold selection rule")
    if value.get("tie_breaker") != "highest-decision-then-route-thresholds":
        errors.append("unsupported deterministic tie breaker")
    if value.get("authority") != "not-granted":
        errors.append("policy decision must not grant authority")

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

    total = value.get("minimum_calibration_cases")
    per_family = value.get("minimum_cases_per_family")
    if type(total) is not int or total <= 0:
        errors.append("policy decision requires a positive calibration minimum")
    if not isinstance(per_family, dict) or set(per_family) != set(FAMILIES):
        errors.append("policy decision requires minima for every request family")
    elif any(type(count) is not int or count <= 0 for count in per_family.values()):
        errors.append("family calibration minima must be positive integers")
    elif type(total) is int and sum(per_family.values()) > total:
        errors.append("family minima cannot exceed the total calibration minimum")

    acceptance = value.get("acceptance_record_sha256")
    if value.get("status") == "proposed":
        if acceptance:
            errors.append("proposed decision must not claim owner acceptance")
    elif not isinstance(acceptance, str) or HEX64.fullmatch(acceptance) is None:
        errors.append("accepted decision requires an exact acceptance record")
    digest = value.get("decision_sha256")
    if not isinstance(digest, str) or HEX64.fullmatch(digest) is None:
        errors.append("policy decision requires decision_sha256")
    elif digest != canonical_sha256(value):
        errors.append("decision_sha256 does not match canonical decision")
    return errors


def load_and_validate(raw: bytes) -> tuple[dict | None, list[str]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["policy decision must be valid unique-key UTF-8 JSON"]
    errors = validate_decision(value)
    return value if isinstance(value, dict) else None, errors
