"""Validate the preregistered NLU abstention-threshold policy.

The policy is evaluation metadata.  It cannot grant routing, egress, tool use,
or authority.  A template fixes the required fields without claiming that a
threshold was selected.  A frozen policy must bind a disjoint calibration
artifact and candidate bundle before the independent holdout is opened.
"""
from __future__ import annotations

import hashlib
import json
import math
import re


SCHEMA = "aster-nlu-threshold-policy.v1"
FAMILIES = (
    "household-command",
    "general-answer",
    "read-only-investigation",
    "change-request",
    "external-research",
    "unsupported",
)
TOP_KEYS = {
    "schema",
    "status",
    "policy_id",
    "contract_schema",
    "selection_partition",
    "score_semantics",
    "selection_rule",
    "constraints",
    "tie_breaker",
    "minimum_calibration_cases",
    "minimum_cases_per_family",
    "candidate_bundle_sha256",
    "calibration_artifact_sha256",
    "calibration_score_sha256",
    "selected_threshold",
    "holdout_accessed",
    "authority",
}
CONSTRAINT_KEYS = {
    "max_privacy_underclassification",
    "max_unsafe_false_route",
    "max_selective_error_rate",
    "minimum_coverage",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fraction(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def validate_policy(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["threshold policy must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("threshold policy fields must match the fixed schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid threshold policy schema")
    if value.get("status") not in {"template", "frozen"}:
        errors.append("status must be template or frozen")
    if not isinstance(value.get("policy_id"), str) or IDENTIFIER.fullmatch(value.get("policy_id", "")) is None:
        errors.append("invalid threshold policy identifier")
    if value.get("contract_schema") != "request-interpretation.v1":
        errors.append("unsupported NLU contract schema")
    if value.get("selection_partition") != "disjoint-calibration":
        errors.append("threshold selection must use disjoint calibration evidence")
    if value.get("score_semantics") != "evaluation-only-route-eligibility":
        errors.append("unsupported score semantics")
    if value.get("selection_rule") != "maximize-coverage-subject-to-all-constraints":
        errors.append("unsupported threshold selection rule")
    if value.get("tie_breaker") != "highest-threshold-then-lexical-candidate-digest":
        errors.append("unsupported deterministic tie breaker")
    if value.get("holdout_accessed") is not False:
        errors.append("threshold policy must attest that holdout was not accessed")
    if value.get("authority") != "not-granted":
        errors.append("threshold policy must not grant authority")

    constraints = value.get("constraints")
    if not isinstance(constraints, dict) or set(constraints) != CONSTRAINT_KEYS:
        errors.append("invalid threshold safety constraints")
        constraints = {}

    if value.get("status") == "template":
        if any(constraints.get(key) is not None for key in CONSTRAINT_KEYS):
            errors.append("template must not claim accepted threshold constraints")
        if value.get("minimum_calibration_cases") is not None:
            errors.append("template must not claim a calibration sample minimum")
        if value.get("minimum_cases_per_family") is not None:
            errors.append("template must not claim family sample minima")
        for key in (
            "candidate_bundle_sha256",
            "calibration_artifact_sha256",
            "calibration_score_sha256",
        ):
            if value.get(key):
                errors.append(f"template must not claim {key}")
        if value.get("selected_threshold") is not None:
            errors.append("template must not claim a selected threshold")
        return errors

    if constraints.get("max_privacy_underclassification") != 0:
        errors.append("frozen policy must allow zero privacy underclassification")
    if constraints.get("max_unsafe_false_route") != 0:
        errors.append("frozen policy must allow zero unsafe false routes")
    for key in ("max_selective_error_rate", "minimum_coverage"):
        if not _fraction(constraints.get(key)):
            errors.append(f"frozen policy requires bounded {key}")
    minimum = value.get("minimum_calibration_cases")
    per_family = value.get("minimum_cases_per_family")
    if type(minimum) is not int or minimum <= 0:
        errors.append("frozen policy requires a positive calibration sample minimum")
    if not isinstance(per_family, dict) or set(per_family) != set(FAMILIES):
        errors.append("frozen policy requires minima for every request family")
    elif any(type(count) is not int or count <= 0 for count in per_family.values()):
        errors.append("family calibration minima must be positive integers")
    elif type(minimum) is int and sum(per_family.values()) > minimum:
        errors.append("family minima cannot exceed the total calibration minimum")
    for key in (
        "candidate_bundle_sha256",
        "calibration_artifact_sha256",
        "calibration_score_sha256",
    ):
        if not _digest(value.get(key)):
            errors.append(f"frozen policy requires {key}")
    if not _fraction(value.get("selected_threshold")):
        errors.append("frozen policy requires a threshold in [0, 1]")
    return errors


def load_and_validate(raw: bytes) -> tuple[dict | None, list[str]]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, ["threshold policy must be valid UTF-8 JSON"]
    errors = validate_policy(value)
    return value if isinstance(value, dict) else None, errors
