"""Validate one content-free NLU candidate bundle and its policy binding."""

from __future__ import annotations

import copy
import hashlib
import json
import re

from nlu_threshold_policy import (
    decode_unique_json,
    load_and_validate as load_threshold_policy,
    sha256,
)


SCHEMA = "aster-nlu-candidate-bundle.v1"
TOP_KEYS = {
    "schema", "status", "candidate_id", "engine_class", "engine_sha256",
    "policy_sha256", "contract_sha256", "adapter_sha256",
    "runtime_profile_sha256", "egress", "tool_mode", "case_data_included",
    "bundle_sha256", "authority",
}
ENGINE_EGRESS = {
    "deterministic": "none",
    "local_model": "local",
    "cloud_model": "cloud",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("bundle_sha256", None)
    raw = json.dumps(copied, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_bundle(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["candidate bundle must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("candidate bundle fields must match the fixed schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid candidate bundle schema")
    if value.get("status") not in {"template", "sealed"}:
        errors.append("status must be template or sealed")
    if not isinstance(value.get("candidate_id"), str) or IDENTIFIER.fullmatch(
        value.get("candidate_id", "")
    ) is None:
        errors.append("invalid candidate identifier")
    if value.get("tool_mode") != "disabled":
        errors.append("NLU candidate tools must remain disabled")
    if value.get("case_data_included") is not False:
        errors.append("candidate bundle must not contain case data")
    if value.get("authority") != "not-granted":
        errors.append("candidate bundle must not grant authority")

    digest_keys = (
        "engine_sha256", "policy_sha256", "contract_sha256",
        "adapter_sha256", "runtime_profile_sha256",
    )
    if value.get("status") == "template":
        if value.get("engine_class") or value.get("egress"):
            errors.append("template must not claim an engine or egress class")
        if any(value.get(key) for key in digest_keys):
            errors.append("template must not claim component digests")
        if value.get("bundle_sha256"):
            errors.append("template must not claim a bundle digest")
        return errors

    engine_class = value.get("engine_class")
    if engine_class not in ENGINE_EGRESS:
        errors.append("sealed candidate requires a supported engine class")
    elif value.get("egress") != ENGINE_EGRESS[engine_class]:
        errors.append("candidate engine and egress classes do not match")
    for key in digest_keys:
        if not _digest(value.get(key)):
            errors.append(f"sealed candidate requires {key}")
    if not _digest(value.get("bundle_sha256")):
        errors.append("sealed candidate requires bundle_sha256")
    elif value["bundle_sha256"] != canonical_sha256(value):
        errors.append("bundle_sha256 does not match canonical manifest")
    return errors


def load_and_validate(raw: bytes) -> tuple[dict | None, list[str]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["candidate bundle must be valid UTF-8 JSON"]
    errors = validate_bundle(value)
    return value if isinstance(value, dict) else None, errors


def validate_policy_binding(policy_raw: bytes, candidate_raw: bytes) -> list[str]:
    """Prove that a registered/frozen policy names this exact sealed bundle."""
    errors: list[str] = []
    policy, policy_errors = load_threshold_policy(policy_raw)
    errors.extend(f"threshold policy: {error}" for error in policy_errors)
    candidate, candidate_errors = load_and_validate(candidate_raw)
    errors.extend(f"candidate bundle: {error}" for error in candidate_errors)
    if policy is not None and policy.get("status") not in {"registered", "frozen"}:
        errors.append("candidate binding requires a registered or frozen policy")
    if candidate is not None and candidate.get("status") != "sealed":
        errors.append("candidate binding requires a sealed candidate bundle")
    if policy is not None and candidate is not None:
        if policy.get("candidate_bundle_sha256") != sha256(candidate_raw):
            errors.append("threshold policy does not bind the exact candidate bundle")
    return errors
