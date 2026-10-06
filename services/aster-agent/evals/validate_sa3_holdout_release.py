"""Validate content-free SA3 holdout handoff manifests."""

import copy
import hashlib
import json
import re
from pathlib import Path


HASH = re.compile(r"^[0-9a-f]{64}$")
ROLE_KEYS = ("custodian_session", "review_session", "evaluation_session", "scoring_session")
CASE_KEYS = {"id", "family", "case_hash", "label_hash", "review_receipt_hash"}
TOP_KEYS = {"schema_version", "status", "release_id", "target_cases", "roles", "cases", "release_digest"}
FORBIDDEN_CONTENT_KEYS = {
    "allowed_observations", "case", "case_text", "evidence", "label",
    "prompt", "response", "symptom", "text",
}


def canonical_digest(value):
    payload = copy.deepcopy(value)
    payload.pop("release_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_release(value):
    if not isinstance(value, dict):
        return ["release must be an object"]
    errors = []
    if set(value) - TOP_KEYS:
        errors.append("unexpected top-level fields; content is forbidden")
    if value.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if value.get("status") not in {"template", "sealed"}:
        errors.append("status must be template or sealed")
    if not value.get("release_id"):
        errors.append("release_id is required")
    if value.get("target_cases") != 20:
        errors.append("target_cases must be 20")

    roles = value.get("roles")
    if not isinstance(roles, dict) or set(roles) != set(ROLE_KEYS):
        errors.append("roles must contain exactly the four custody-session keys")
        roles = {}
    cases = value.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        cases = []

    if value.get("status") == "template":
        if cases:
            errors.append("template must not contain cases")
        if any(roles.get(key) for key in ROLE_KEYS):
            errors.append("template must not name custody sessions")
        if "release_digest" in value:
            errors.append("template must not contain release_digest")
        return errors

    role_values = [roles.get(key, "") for key in ROLE_KEYS]
    if any(not isinstance(role, str) or not role.strip() for role in role_values):
        errors.append("sealed release requires all custody sessions")
    elif len(set(role_values)) != len(role_values):
        errors.append("sealed release custody sessions must be distinct")

    if len(cases) != value.get("target_cases"):
        errors.append("sealed release must contain exactly target_cases")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or any(not isinstance(item, str) or not item for item in identifiers):
        errors.append("every case requires an id")
    elif len(set(identifiers)) != len(identifiers):
        errors.append("case ids must be unique")

    for case in cases:
        if not isinstance(case, dict):
            errors.append("each case must be an object")
            continue
        forbidden = sorted(FORBIDDEN_CONTENT_KEYS & set(case))
        if forbidden:
            errors.append(f"{case.get('id', '<missing id>')}: content keys forbidden: {', '.join(forbidden)}")
        missing = sorted(CASE_KEYS - set(case))
        if missing:
            errors.append(f"{case.get('id', '<missing id>')}: missing {', '.join(missing)}")
        extra = sorted(set(case) - CASE_KEYS)
        if extra:
            errors.append(f"{case.get('id', '<missing id>')}: unexpected keys: {', '.join(extra)}")
        for key in ("case_hash", "label_hash", "review_receipt_hash"):
            if key in case and (not isinstance(case[key], str) or not HASH.fullmatch(case[key])):
                errors.append(f"{case.get('id', '<missing id>')}: {key} must be a SHA-256 digest")

    digest = value.get("release_digest")
    if not isinstance(digest, str) or not HASH.fullmatch(digest):
        errors.append("sealed release requires a SHA-256 release_digest")
    elif digest != canonical_digest(value):
        errors.append("release_digest does not match canonical manifest")
    return errors


def main():
    path = Path(__file__).with_name("sa3-holdout-release-template.json")
    errors = validate_release(json.loads(path.read_text()))
    if errors:
        raise SystemExit("\n".join(errors))
    print("SA3 holdout release manifest: valid")


if __name__ == "__main__":
    main()
