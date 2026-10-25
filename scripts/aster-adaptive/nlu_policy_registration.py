"""Build a registered NLU threshold policy from exact accepted inputs."""

from __future__ import annotations

import copy

from nlu_calibration_release import validate_release
from nlu_candidate_bundle import load_and_validate as load_candidate
from nlu_policy_decision import load_and_validate as load_decision
from nlu_threshold_policy import (
    FAMILIES,
    decode_unique_json,
    sha256,
    validate_policy,
)


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
    return {
        "schema": "aster-nlu-policy-registration.v1",
        "decision_artifact_sha256": sha256(decision_raw),
        "candidate_bundle_sha256": candidate_sha256,
        "calibration_artifact_sha256": sha256(calibration_raw),
        "policy": registered,
        "authority": "not-granted",
    }
