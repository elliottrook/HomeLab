"""Build a registered NLU threshold policy from exact accepted inputs."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from nlu_calibration_release import validate_release
from nlu_candidate_bundle import load_and_validate as load_candidate
from nlu_policy_decision import load_and_validate as load_decision
from nlu_threshold_policy import (
    FAMILIES,
    decode_unique_json,
    sha256,
    validate_policy,
)


SCHEMA = "aster-nlu-policy-registration.v1"
TOP_KEYS = {
    "schema",
    "decision_artifact_sha256",
    "candidate_bundle_sha256",
    "calibration_artifact_sha256",
    "policy",
    "authority",
}


def validate_registration(value: object) -> list[str]:
    """Validate a content-free registration envelope and its internal bindings."""
    if not isinstance(value, dict):
        return ["policy registration must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("policy registration fields must match the fixed schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid policy registration schema")
    if value.get("authority") != "not-granted":
        errors.append("policy registration must not grant authority")
    for key in (
        "decision_artifact_sha256",
        "candidate_bundle_sha256",
        "calibration_artifact_sha256",
    ):
        digest = value.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            errors.append(f"invalid {key}")

    registered = value.get("policy")
    policy_errors = validate_policy(registered)
    errors.extend(f"registered policy: {error}" for error in policy_errors)
    if isinstance(registered, dict):
        if registered.get("status") != "registered":
            errors.append("registration envelope requires registered policy status")
        if registered.get("candidate_bundle_sha256") != value.get(
            "candidate_bundle_sha256"
        ):
            errors.append("registration candidate binding mismatch")
        if registered.get("calibration_artifact_sha256") != value.get(
            "calibration_artifact_sha256"
        ):
            errors.append("registration calibration binding mismatch")
        if registered.get("authority") != value.get("authority"):
            errors.append("registration authority binding mismatch")
    return errors


def load_and_validate(raw: bytes) -> tuple[dict | None, list[str]]:
    """Decode one registration while rejecting duplicate JSON keys."""
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        return None, [f"invalid registration JSON: {error}"]
    errors = validate_registration(value)
    return (value if isinstance(value, dict) else None), errors


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_new_private(path: Path, payload: bytes) -> None:
    """Create one owner-only registration artifact without replacing evidence."""
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


def register_policy(
    decision_raw: bytes,
    candidate_raw: bytes,
    calibration_raw: bytes,
) -> dict:
    decision, decision_errors = load_decision(decision_raw)
    if decision_errors or decision is None or decision.get("status") != "accepted":
        raise ValueError("policy registration requires an accepted exact decision")
    candidate, candidate_errors = load_candidate(candidate_raw)
    if candidate_errors or candidate is None or candidate.get("status") != "sealed":
        raise ValueError("policy registration requires a sealed exact candidate")
    try:
        calibration = decode_unique_json(calibration_raw)
    except ValueError as error:
        raise ValueError("policy registration requires a valid calibration release") from error
    calibration_errors = validate_release(calibration)
    if calibration_errors or calibration.get("status") != "sealed":
        raise ValueError("policy registration requires a sealed calibration release")

    candidate_sha256 = sha256(candidate_raw)
    if calibration.get("candidate_bundle_sha256") != candidate_sha256:
        raise ValueError("calibration release does not bind the exact candidate")
    if calibration.get("target_cases", 0) < decision["minimum_calibration_cases"]:
        raise ValueError("calibration release is below the accepted total minimum")
    targets = calibration.get("family_targets", {})
    for family in FAMILIES:
        if targets.get(family, 0) < decision["minimum_cases_per_family"][family]:
            raise ValueError(
                f"calibration release is below the accepted {family} minimum"
            )

    registered = {
        "schema": "aster-nlu-threshold-policy.v1",
        "status": "registered",
        "policy_id": "nlu-threshold-policy-v1",
        "contract_schema": "request-interpretation.v1",
        "selection_partition": "disjoint-calibration",
        "score_semantics": "evaluation-only-route-eligibility",
        "selection_rule": decision["selection_rule"],
        "constraints": copy.deepcopy(decision["constraints"]),
        "tie_breaker": decision["tie_breaker"],
        "minimum_calibration_cases": decision["minimum_calibration_cases"],
        "minimum_cases_per_family": copy.deepcopy(
            decision["minimum_cases_per_family"]
        ),
        "candidate_bundle_sha256": candidate_sha256,
        "calibration_artifact_sha256": sha256(calibration_raw),
        "calibration_score_sha256": "",
        "selected_threshold": None,
        "holdout_accessed": False,
        "authority": "not-granted",
    }
    if validate_policy(registered):
        raise ValueError("accepted inputs did not produce a valid registered policy")
    result = {
        "schema": SCHEMA,
        "decision_artifact_sha256": sha256(decision_raw),
        "candidate_bundle_sha256": candidate_sha256,
        "calibration_artifact_sha256": sha256(calibration_raw),
        "policy": registered,
        "authority": "not-granted",
    }
    if validate_registration(result):
        raise ValueError("accepted inputs did not produce a valid registration")
    return result
