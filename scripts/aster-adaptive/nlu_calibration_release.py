"""Validate a content-free NLU calibration custody manifest.

The manifest binds opaque calibration cases to one candidate.  Numeric sample
requirements come only from an already registered threshold policy.  This
module never reads case text, labels, predictions, or the independent holdout.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

from nlu_threshold_policy import FAMILIES, load_and_validate, sha256


SCHEMA = "aster-nlu-calibration-release.v1"
ROLE_KEYS = ("case_custodian", "label_reviewer", "scoring_operator")
TOP_KEYS = {
    "schema", "status", "release_id", "target_cases", "family_targets",
    "roles", "candidate_bundle_sha256", "cases", "release_sha256",
    "authority",
}
CASE_KEYS = {"id", "family", "case_sha256", "label_sha256", "review_receipt_sha256"}
FORBIDDEN_KEYS = {
    "answer", "content", "entities", "label", "notes", "prediction",
    "prompt", "reasoning", "request", "route_score", "text",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("release_sha256", None)
    return hashlib.sha256(
        json.dumps(copied, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def validate_release(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["calibration release must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("calibration release fields must match the fixed schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid calibration release schema")
    if value.get("status") not in {"template", "sealed"}:
        errors.append("status must be template or sealed")
    if not isinstance(value.get("release_id"), str) or IDENTIFIER.fullmatch(
        value.get("release_id", "")
    ) is None:
        errors.append("invalid calibration release identifier")
    if value.get("authority") != "not-granted":
        errors.append("calibration release must not grant authority")
    roles = value.get("roles")
    if not isinstance(roles, dict) or set(roles) != set(ROLE_KEYS):
        errors.append("roles must contain exactly the calibration custody roles")
        roles = {}
    cases = value.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        cases = []

    if value.get("status") == "template":
        if value.get("target_cases") is not None or value.get("family_targets") is not None:
            errors.append("template must not claim sample targets")
        if any(roles.get(role) for role in ROLE_KEYS):
            errors.append("template must not name custody roles")
        if value.get("candidate_bundle_sha256"):
            errors.append("template must not claim a candidate digest")
        if cases:
            errors.append("template must not contain cases")
        if value.get("release_sha256"):
            errors.append("template must not claim a release digest")
        return errors

    target = value.get("target_cases")
    targets = value.get("family_targets")
    if type(target) is not int or target <= 0:
        errors.append("sealed release requires a positive target_cases")
    if (
        not isinstance(targets, dict)
        or set(targets) != set(FAMILIES)
        or any(type(count) is not int or count <= 0 for count in targets.values())
    ):
        errors.append("sealed release requires positive targets for every family")
        targets = {}
    elif type(target) is int and sum(targets.values()) != target:
        errors.append("family targets must sum to target_cases")
    role_values = [roles.get(role) for role in ROLE_KEYS]
    if any(not isinstance(role, str) or IDENTIFIER.fullmatch(role) is None for role in role_values):
        errors.append("sealed release requires valid custody-role identifiers")
    elif len(set(role_values)) != len(role_values):
        errors.append("sealed release custody roles must be distinct")
    if not _digest(value.get("candidate_bundle_sha256")):
        errors.append("sealed release requires candidate_bundle_sha256")
    if type(target) is int and len(cases) != target:
        errors.append("sealed release case count must equal target_cases")

    seen: set[str] = set()
    counts = {family: 0 for family in FAMILIES}
    for case in cases:
        if not isinstance(case, dict):
            errors.append("each case must be an object")
            continue
        case_id = case.get("id", "<missing>")
        forbidden = sorted(FORBIDDEN_KEYS & set(case))
        if forbidden:
            errors.append(f"{case_id}: content keys forbidden: {', '.join(forbidden)}")
        if set(case) != CASE_KEYS:
            errors.append(f"{case_id}: invalid case fields")
        if not isinstance(case_id, str) or IDENTIFIER.fullmatch(case_id) is None:
            errors.append("invalid case identifier")
        elif case_id in seen:
            errors.append(f"duplicate case identifier: {case_id}")
        else:
            seen.add(case_id)
        family = case.get("family")
        if family not in counts:
            errors.append(f"{case_id}: invalid request family")
        else:
            counts[family] += 1
        for key in ("case_sha256", "label_sha256", "review_receipt_sha256"):
            if not _digest(case.get(key)):
                errors.append(f"{case_id}: {key} must be a SHA-256 digest")
    if targets and counts != targets:
        errors.append("sealed release family counts do not match family_targets")
    if not _digest(value.get("release_sha256")):
        errors.append("sealed release requires release_sha256")
    elif value["release_sha256"] != canonical_sha256(value):
        errors.append("release_sha256 does not match canonical manifest")
    return errors


def validate_release_bundle(value: object, release_raw: bytes, policy_raw: bytes) -> list[str]:
    errors = validate_release(value)
    try:
        encoded_value = json.loads(release_raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("exact calibration release must be valid UTF-8 JSON")
    else:
        if encoded_value != value:
            errors.append("exact calibration release bytes do not match validated manifest")
    policy, policy_errors = load_and_validate(policy_raw)
    errors.extend(f"threshold policy: {error}" for error in policy_errors)
    if policy is not None and policy.get("status") != "registered":
        errors.append("calibration release requires a registered threshold policy")
    if isinstance(value, dict) and value.get("status") == "sealed" and policy is not None:
        if policy.get("calibration_artifact_sha256") != sha256(release_raw):
            errors.append("registered policy does not bind the exact calibration release")
        if value.get("candidate_bundle_sha256") != policy.get("candidate_bundle_sha256"):
            errors.append("calibration release candidate does not match registered policy")
        minimum = policy.get("minimum_calibration_cases")
        targets = value.get("family_targets")
        if type(minimum) is int and value.get("target_cases", 0) < minimum:
            errors.append("calibration release is below the registered total minimum")
        if isinstance(targets, dict) and isinstance(policy.get("minimum_cases_per_family"), dict):
            for family in FAMILIES:
                if targets.get(family, 0) < policy["minimum_cases_per_family"][family]:
                    errors.append(f"calibration release is below the registered {family} minimum")
    return errors
