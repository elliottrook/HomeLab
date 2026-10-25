"""Validate content-free custody manifests for the independent NLU holdout.

This module never reads case or label content. A valid sealed manifest proves
only that independently reviewed opaque artifacts have the required structure
and pinned provenance; it does not authorize evaluation, routing or egress.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

from nlu_threshold_policy import load_and_validate, sha256


SCHEMA = "aster-nlu-holdout-release.v1"
TARGET_CASES = 36
FAMILIES = (
    "household-command",
    "general-answer",
    "read-only-investigation",
    "change-request",
    "external-research",
    "unsupported",
)
ROLE_KEYS = (
    "case_custodian",
    "label_reviewer",
    "evaluation_operator",
    "score_reviewer",
)
TOP_KEYS = {
    "schema",
    "status",
    "release_id",
    "target_cases",
    "family_targets",
    "roles",
    "contract_sha256",
    "scorer_sha256",
    "threshold_policy_sha256",
    "development_nonoverlap_receipt_sha256",
    "cases",
    "release_sha256",
    "authority",
}
CASE_KEYS = {
    "id",
    "family",
    "case_sha256",
    "label_sha256",
    "review_receipt_sha256",
}
FORBIDDEN_KEYS = {
    "answer",
    "content",
    "entities",
    "label",
    "notes",
    "prompt",
    "reasoning",
    "request",
    "text",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def canonical_sha256(value: dict) -> str:
    copy_value = copy.deepcopy(value)
    copy_value.pop("release_sha256", None)
    raw = json.dumps(copy_value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def validate_release(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["release must be an object"]
    errors: list[str] = []
    extra = set(value) - TOP_KEYS
    if extra:
        errors.append("unexpected top-level fields; content is forbidden")
    if value.get("schema") != SCHEMA:
        errors.append("invalid release schema")
    if value.get("status") not in {"template", "sealed"}:
        errors.append("status must be template or sealed")
    if not isinstance(value.get("release_id"), str) or IDENTIFIER.fullmatch(value.get("release_id", "")) is None:
        errors.append("invalid release identifier")
    if value.get("target_cases") != TARGET_CASES:
        errors.append(f"target_cases must be {TARGET_CASES}")
    expected_targets = {family: TARGET_CASES // len(FAMILIES) for family in FAMILIES}
    if value.get("family_targets") != expected_targets:
        errors.append("family_targets must contain six cases for every family")
    if value.get("authority") != "not-granted":
        errors.append("release must not grant authority")

    roles = value.get("roles")
    if not isinstance(roles, dict) or set(roles) != set(ROLE_KEYS):
        errors.append("roles must contain exactly the four custody roles")
        roles = {}
    cases = value.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        cases = []

    digest_keys = (
        "contract_sha256",
        "scorer_sha256",
        "threshold_policy_sha256",
        "development_nonoverlap_receipt_sha256",
    )
    if value.get("status") == "template":
        if cases:
            errors.append("template must not contain cases")
        if any(roles.get(key) for key in ROLE_KEYS):
            errors.append("template must not name custody roles")
        if any(value.get(key) for key in digest_keys):
            errors.append("template must not claim frozen evidence digests")
        if "release_sha256" in value:
            errors.append("template must not contain release_sha256")
        return errors

    role_values = [roles.get(key) for key in ROLE_KEYS]
    if any(not isinstance(role, str) or IDENTIFIER.fullmatch(role) is None for role in role_values):
        errors.append("sealed release requires valid custody-role identifiers")
    elif len(set(role_values)) != len(role_values):
        errors.append("sealed release custody roles must be distinct")
    for key in digest_keys:
        if not _digest(value.get(key)):
            errors.append(f"sealed release requires {key}")

    if len(cases) != TARGET_CASES:
        errors.append(f"sealed release must contain exactly {TARGET_CASES} cases")
    seen: set[str] = set()
    family_counts = {family: 0 for family in FAMILIES}
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
        if family not in family_counts:
            errors.append(f"{case_id}: invalid request family")
        else:
            family_counts[family] += 1
        for key in ("case_sha256", "label_sha256", "review_receipt_sha256"):
            if not _digest(case.get(key)):
                errors.append(f"{case_id}: {key} must be a SHA-256 digest")
    if family_counts != expected_targets:
        errors.append("sealed release family counts do not match family_targets")

    release_digest = value.get("release_sha256")
    if not _digest(release_digest):
        errors.append("sealed release requires release_sha256")
    elif release_digest != canonical_sha256(value):
        errors.append("release_sha256 does not match canonical manifest")
    return errors


def validate_release_bundle(value: object, threshold_policy_raw: bytes) -> list[str]:
    """Validate a release and its exact frozen threshold-policy artifact."""
    errors = validate_release(value)
    policy, policy_errors = load_and_validate(threshold_policy_raw)
    errors.extend(f"threshold policy: {error}" for error in policy_errors)
    if isinstance(value, dict) and value.get("status") == "sealed":
        if value.get("threshold_policy_sha256") != sha256(threshold_policy_raw):
            errors.append("threshold policy digest does not match sealed release")
        if policy is not None and policy.get("status") != "frozen":
            errors.append("sealed release requires a frozen threshold policy")
    return errors
