"""Bind an explicit owner acceptance record to one exact NLU proposal."""

from __future__ import annotations

import copy
import hashlib
import json

from nlu_policy_decision import canonical_sha256 as decision_canonical_sha256
from nlu_policy_decision import load_and_validate
from nlu_threshold_policy import decode_unique_json, sha256


SCHEMA = "aster-nlu-policy-acceptance.v1"
TOP_KEYS = {
    "schema",
    "status",
    "decision_id",
    "proposal_artifact_sha256",
    "proposal_decision_sha256",
    "acceptance_scope",
    "authority",
    "acceptance_sha256",
}


def canonical_sha256(value: dict) -> str:
    copied = copy.deepcopy(value)
    copied.pop("acceptance_sha256", None)
    raw = json.dumps(copied, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_acceptance(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["policy acceptance must be an object"]
    errors: list[str] = []
    if set(value) != TOP_KEYS:
        errors.append("policy acceptance fields must match the fixed schema")
    if value.get("schema") != SCHEMA:
        errors.append("invalid policy acceptance schema")
    if value.get("status") != "accepted":
        errors.append("policy acceptance status must be accepted")
    if value.get("acceptance_scope") != "exact-proposal-values-only":
        errors.append("policy acceptance scope must be exact proposal values only")
    if value.get("authority") != "not-granted":
        errors.append("policy acceptance must not grant routing authority")
    for key in (
        "proposal_artifact_sha256",
        "proposal_decision_sha256",
        "acceptance_sha256",
    ):
        digest = value.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            errors.append(f"invalid {key}")
    if not isinstance(value.get("decision_id"), str) or not value.get("decision_id"):
        errors.append("policy acceptance requires a decision identifier")
    if isinstance(value.get("acceptance_sha256"), str) and value.get(
        "acceptance_sha256"
    ) != canonical_sha256(value):
        errors.append("acceptance_sha256 does not match canonical acceptance")
    return errors


def load_and_validate_acceptance(raw: bytes) -> tuple[dict | None, list[str]]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, ["policy acceptance must be valid unique-key UTF-8 JSON"]
    errors = validate_acceptance(value)
    return value if isinstance(value, dict) else None, errors


def accept_exact_proposal(proposal_raw: bytes, acceptance_raw: bytes) -> dict:
    proposal, proposal_errors = load_and_validate(proposal_raw)
    if proposal_errors or proposal is None or proposal.get("status") != "proposed":
        raise ValueError("owner acceptance requires one valid exact proposal")
    acceptance, acceptance_errors = load_and_validate_acceptance(acceptance_raw)
    if acceptance_errors or acceptance is None:
        raise ValueError("owner acceptance requires one valid exact acceptance record")
    if acceptance["proposal_artifact_sha256"] != sha256(proposal_raw):
        raise ValueError("acceptance record does not bind the exact proposal artifact")
    if acceptance["proposal_decision_sha256"] != proposal["decision_sha256"]:
        raise ValueError("acceptance record does not bind the proposal decision digest")
    if acceptance["decision_id"] != proposal["decision_id"]:
        raise ValueError("acceptance record does not bind the proposal identifier")

    accepted = copy.deepcopy(proposal)
    accepted["status"] = "accepted"
    accepted["acceptance_record_sha256"] = sha256(acceptance_raw)
    accepted["decision_sha256"] = decision_canonical_sha256(accepted)
    accepted_value, accepted_errors = load_and_validate(
        (json.dumps(accepted, sort_keys=True, separators=(",", ":")) + "\n").encode()
    )
    if accepted_errors or accepted_value is None:
        raise ValueError("exact acceptance did not produce a valid accepted decision")
    return accepted
