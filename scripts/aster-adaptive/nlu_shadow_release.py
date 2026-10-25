"""Validate content-free, no-effect NLU shadow evidence."""

from __future__ import annotations

import copy
import hashlib
import json
import re

from nlu_threshold_policy import FAMILIES, decode_unique_json, load_and_validate, sha256
from nlu_candidate_bundle import validate_policy_binding
import nlu_calibration_corpus as corpus


SCHEMA = "aster-nlu-shadow-release.v1"
ROUTES = {"local", "codex", "clarify", "abstain", "deny"}
TOP_KEYS = {
    "schema", "status", "release_id", "source_class", "candidate_bundle_sha256",
    "threshold_policy_sha256", "case_count", "cases", "execution_attempted",
    "provider_egress_attempted", "release_sha256", "authority",
}
CASE_KEYS = {
    "id", "family", "interpretation_sha256", "proposal_sha256",
    "baseline_route", "candidate_route", "route_changed",
}
FORBIDDEN_KEYS = {
    "answer", "content", "entities", "notes", "prompt", "reasoning",
    "request", "text", "tool", "tool_arguments",
}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
INTERPRETATION_KEYS = {
    "schema_version", "request_id", "principal_ref", "request_family",
    "sensitivity", "capability_needs", "ambiguity", "disposition", "reason",
    "engine_digest", "policy_digest", "confidence", "authorization",
}
PROPOSAL_KEYS = {
    "schema_version", "request_id", "principal_ref", "interpretation_digest",
    "status", "backend_id", "egress", "reason", "policy_digest",
    "expires_at", "authorization",
}


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("release_sha256", None)
    return hashlib.sha256(
        json.dumps(copied, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _artifact(raw: bytes, name: str) -> tuple[dict | None, list[str]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, [f"{name} must be unique-key UTF-8 JSON"]
    if not isinstance(value, dict):
        return None, [f"{name} must be an object"]
    return value, []


def _validate_artifact_semantics(case: dict, interpretation_raw: bytes,
                                 proposal_raw: bytes, candidate: dict) -> list[str]:
    errors = []
    interpretation, parse_errors = _artifact(interpretation_raw, "interpretation")
    errors.extend(parse_errors)
    proposal, proposal_errors = _artifact(proposal_raw, "proposal")
    errors.extend(proposal_errors)
    if interpretation is None or proposal is None:
        return errors
    if set(interpretation) != INTERPRETATION_KEYS:
        errors.append("interpretation fields must match the fixed contract")
    else:
        try:
            label = {key: interpretation[key] for key in corpus.LABEL_KEYS}
            corpus._validate_label(label, case["family"])
        except (KeyError, TypeError, ValueError):
            errors.append("interpretation dimensions are invalid")
        expected = {
            "schema_version": "request-interpretation.v1",
            "request_id": case["id"],
            "engine_digest": "sha256:" + candidate.get("engine_sha256", ""),
            "policy_digest": "sha256:" + candidate.get("policy_sha256", ""),
            "confidence": None,
            "authorization": "not-granted",
        }
        if any(interpretation.get(key) != value for key, value in expected.items()):
            errors.append("interpretation provenance or authority is invalid")
        if not isinstance(interpretation.get("principal_ref"), str) or IDENTIFIER.fullmatch(
            interpretation.get("principal_ref", "")
        ) is None:
            errors.append("interpretation principal is invalid")
    if set(proposal) != PROPOSAL_KEYS:
        errors.append("proposal fields must match the fixed contract")
        return errors
    canonical_interpretation = json.dumps(
        interpretation, sort_keys=True, separators=(",", ":")
    ).encode()
    if proposal.get("schema_version") != "route-proposal.v1":
        errors.append("invalid proposal schema")
    if (
        proposal.get("request_id") != interpretation.get("request_id")
        or proposal.get("principal_ref") != interpretation.get("principal_ref")
        or proposal.get("policy_digest") != interpretation.get("policy_digest")
        or proposal.get("interpretation_digest") != "sha256:" + sha256(canonical_interpretation)
    ):
        errors.append("proposal does not bind the exact interpretation")
    if proposal.get("status") != case.get("candidate_route"):
        errors.append("proposal status does not match the shadow candidate route")
    if proposal.get("authorization") != "not-granted":
        errors.append("proposal cannot grant authority")
    if type(proposal.get("expires_at")) is not int or proposal["expires_at"] < 1:
        errors.append("proposal expiry is invalid")
    status = proposal.get("status")
    if status == "local":
        valid_shape = (
            isinstance(proposal.get("backend_id"), str)
            and IDENTIFIER.fullmatch(proposal["backend_id"]) is not None
            and proposal.get("egress") == "local"
            and proposal.get("reason") in {"deterministic-match", "local-capable"}
        )
    elif status == "codex":
        valid_shape = (
            isinstance(proposal.get("backend_id"), str)
            and IDENTIFIER.fullmatch(proposal["backend_id"]) is not None
            and proposal.get("egress") == "cloud"
            and proposal.get("reason") == "stronger-capability-required"
            and interpretation.get("sensitivity") != "personal"
        )
    elif status in {"clarify", "abstain", "deny"}:
        reasons = {
            "clarify": {"ambiguous"},
            "abstain": {"ambiguous", "unsupported"},
            "deny": {"policy-denied"},
        }
        valid_shape = (
            proposal.get("backend_id") is None
            and proposal.get("egress") == "none"
            and proposal.get("reason") in reasons[status]
        )
    else:
        valid_shape = False
    expected_status = {
        "route": {"local", "codex"}, "clarify": {"clarify"},
        "abstain": {"abstain"}, "deny": {"deny"},
    }.get(interpretation.get("disposition"), set())
    if not valid_shape or status not in expected_status:
        errors.append("proposal route semantics are invalid")
    return errors


def validate_release(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["shadow release must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("shadow release fields must match the fixed schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid shadow release schema")
    if value.get("status") not in {"template", "sealed"}:
        errors.append("status must be template or sealed")
    if not isinstance(value.get("release_id"), str) or IDENTIFIER.fullmatch(
        value.get("release_id", "")
    ) is None:
        errors.append("invalid shadow release identifier")
    if value.get("authority") != "not-granted":
        errors.append("shadow release must not grant authority")
    if value.get("execution_attempted") is not False:
        errors.append("shadow release must attest that execution was not attempted")
    if value.get("provider_egress_attempted") is not False:
        errors.append("shadow release must attest that provider egress was not attempted")
    cases = value.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        cases = []

    if value.get("status") == "template":
        for key in ("source_class", "candidate_bundle_sha256", "threshold_policy_sha256"):
            if value.get(key):
                errors.append(f"template must not claim {key}")
        if value.get("case_count") is not None:
            errors.append("template must not claim a case count")
        if cases:
            errors.append("template must not contain cases")
        if value.get("release_sha256"):
            errors.append("template must not claim a release digest")
        return errors

    if value.get("source_class") != "synthetic-S0":
        errors.append("initial shadow release permits synthetic-S0 evidence only")
    for key in ("candidate_bundle_sha256", "threshold_policy_sha256"):
        if not _digest(value.get(key)):
            errors.append(f"sealed shadow release requires {key}")
    if type(value.get("case_count")) is not int or value["case_count"] <= 0:
        errors.append("sealed shadow release requires a positive case count")
    elif len(cases) != value["case_count"]:
        errors.append("shadow case count mismatch")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("each shadow case must be an object")
            continue
        case_id = case.get("id", "<missing>")
        forbidden = sorted(FORBIDDEN_KEYS & set(case))
        if forbidden:
            errors.append(f"{case_id}: content keys forbidden: {', '.join(forbidden)}")
        if set(case) != CASE_KEYS:
            errors.append(f"{case_id}: invalid shadow case fields")
        if not isinstance(case_id, str) or IDENTIFIER.fullmatch(case_id) is None:
            errors.append("invalid shadow case identifier")
        elif case_id in seen:
            errors.append(f"duplicate shadow case identifier: {case_id}")
        else:
            seen.add(case_id)
        if case.get("family") not in FAMILIES:
            errors.append(f"{case_id}: invalid request family")
        for key in ("interpretation_sha256", "proposal_sha256"):
            if not _digest(case.get(key)):
                errors.append(f"{case_id}: {key} must be a SHA-256 digest")
        for key in ("baseline_route", "candidate_route"):
            if case.get(key) not in ROUTES:
                errors.append(f"{case_id}: invalid {key}")
        if type(case.get("route_changed")) is not bool:
            errors.append(f"{case_id}: route_changed must be boolean")
        elif case.get("baseline_route") in ROUTES and case.get("candidate_route") in ROUTES:
            if case["route_changed"] != (case["baseline_route"] != case["candidate_route"]):
                errors.append(f"{case_id}: route_changed does not match routes")
    if not _digest(value.get("release_sha256")):
        errors.append("sealed shadow release requires release_sha256")
    elif value["release_sha256"] != canonical_sha256(value):
        errors.append("release_sha256 does not match canonical manifest")
    return errors


def validate_release_bundle(
    value: object,
    policy_raw: bytes,
    candidate_raw: bytes,
    case_artifacts: dict[str, dict[str, bytes]],
) -> list[str]:
    errors = validate_release(value)
    policy, policy_errors = load_and_validate(policy_raw)
    errors.extend(f"threshold policy: {error}" for error in policy_errors)
    errors.extend(
        f"candidate binding: {error}"
        for error in validate_policy_binding(policy_raw, candidate_raw)
    )
    try:
        candidate = decode_unique_json(candidate_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        candidate = None
    if policy is not None and policy.get("status") != "frozen":
        errors.append("sealed shadow release requires a frozen threshold policy")
    if isinstance(value, dict) and value.get("status") == "sealed" and policy is not None:
        if value.get("threshold_policy_sha256") != sha256(policy_raw):
            errors.append("shadow release does not bind the exact threshold policy")
        if value.get("candidate_bundle_sha256") != policy.get("candidate_bundle_sha256"):
            errors.append("shadow candidate does not match frozen threshold policy")
        cases = value.get("cases") if isinstance(value.get("cases"), list) else []
        expected_ids = {
            case.get("id") for case in cases
            if isinstance(case, dict) and isinstance(case.get("id"), str)
        }
        if not isinstance(case_artifacts, dict) or set(case_artifacts) != expected_ids:
            errors.append("shadow artifacts must match every sealed case exactly")
        else:
            for case in cases:
                case_id = case["id"]
                artifacts = case_artifacts.get(case_id)
                if (
                    not isinstance(artifacts, dict)
                    or set(artifacts) != {"interpretation", "proposal"}
                    or not all(isinstance(raw, bytes) for raw in artifacts.values())
                ):
                    errors.append(f"{case_id}: invalid shadow artifacts")
                    continue
                for field, artifact in (
                    ("interpretation_sha256", artifacts["interpretation"]),
                    ("proposal_sha256", artifacts["proposal"]),
                ):
                    if case.get(field) != sha256(artifact):
                        errors.append(f"{case_id}: {field} does not match exact artifact")
                if isinstance(candidate, dict):
                    errors.extend(
                        f"{case_id}: {error}"
                        for error in _validate_artifact_semantics(
                            case, artifacts["interpretation"], artifacts["proposal"], candidate
                        )
                    )
    return errors
