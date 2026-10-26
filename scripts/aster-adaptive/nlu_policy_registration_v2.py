"""Register confidence-policy v2 against one exact candidate and calibration."""
from __future__ import annotations

import copy
import json

from nlu_calibration_release import validate_release
from nlu_candidate_bundle import load_and_validate as load_candidate
from nlu_policy_acceptance_v2 import accept_exact_proposal, canonical_json
from nlu_threshold_policy import FAMILIES, decode_unique_json, sha256
from nlu_threshold_policy_v2 import SCHEMA as POLICY_SCHEMA, validate_policy


SCHEMA = "aster-nlu-policy-registration.v2"


def register_policy(
    proposal_raw: bytes, acceptance_raw: bytes, candidate_raw: bytes,
    calibration_raw: bytes,
) -> dict:
    try:
        decision = accept_exact_proposal(proposal_raw, acceptance_raw)
    except ValueError as error:
        raise ValueError("v2 registration requires exact owner acceptance") from error
    candidate, candidate_errors = load_candidate(candidate_raw)
    if candidate_errors or candidate is None or candidate.get("status") != "sealed":
        raise ValueError("v2 registration requires a sealed exact candidate")
    try:
        calibration = decode_unique_json(calibration_raw)
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError("v2 registration requires a valid calibration release") from error
    if validate_release(calibration) or calibration.get("status") != "sealed":
        raise ValueError("v2 registration requires a sealed calibration release")
    candidate_sha = sha256(candidate_raw)
    if calibration.get("candidate_bundle_sha256") != candidate_sha:
        raise ValueError("calibration release does not bind the exact candidate")
    if calibration.get("target_cases", 0) < decision["minimum_calibration_cases"]:
        raise ValueError("calibration release is below the accepted total minimum")
    for family in FAMILIES:
        if calibration.get("family_targets", {}).get(family, 0) < decision["minimum_cases_per_family"][family]:
            raise ValueError(f"calibration release is below the accepted {family} minimum")

    registered = {
        "schema": POLICY_SCHEMA, "status": "registered",
        "policy_id": "nlu-confidence-policy-v2",
        "contract_schema": "request-interpretation.v1",
        "selection_partition": "disjoint-calibration",
        "coverage_semantics": decision["coverage_semantics"],
        "route_effect_semantics": decision["route_effect_semantics"],
        "selection_rule": decision["selection_rule"],
        "constraints": copy.deepcopy(decision["constraints"]),
        "tie_breaker": decision["tie_breaker"],
        "minimum_calibration_cases": decision["minimum_calibration_cases"],
        "minimum_cases_per_family": copy.deepcopy(decision["minimum_cases_per_family"]),
        "candidate_bundle_sha256": candidate_sha,
        "calibration_artifact_sha256": sha256(calibration_raw),
        "calibration_score_sha256": "", "selected_thresholds": None,
        "holdout_accessed": False, "authority": "not-granted",
    }
    errors = validate_policy(registered)
    if errors:
        raise ValueError("accepted v2 inputs did not produce a valid registered policy")
    return {
        "schema": SCHEMA,
        "decision_artifact_sha256": sha256(canonical_json(decision)),
        "candidate_bundle_sha256": candidate_sha,
        "calibration_artifact_sha256": sha256(calibration_raw),
        "policy": registered, "authority": "not-granted",
    }
