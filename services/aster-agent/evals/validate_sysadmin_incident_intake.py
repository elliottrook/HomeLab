"""Validate the reviewed sysadmin-incident intake before it is used as evaluation input."""

import json
from collections import Counter
from pathlib import Path


def validate_intake(value):
    required = set(value.get("required_fields", []))
    cases = value.get("cases", [])
    errors = []

    if value.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not required:
        errors.append("required_fields must not be empty")

    identifiers = [case.get("id") for case in cases]
    if any(not identifier for identifier in identifiers):
        errors.append("every case needs an id")
    if len(identifiers) != len(set(identifiers)):
        errors.append("case ids must be unique")

    split_counts = Counter()
    for case in cases:
        missing = sorted(required - set(case))
        if missing:
            errors.append(f"{case.get('id', '<missing id>')}: missing {', '.join(missing)}")
            continue
        split = case["split"]
        if split not in {"development", "holdout"}:
            errors.append(f"{case['id']}: invalid split {split!r}")
            continue
        split_counts[split] += 1
        if not case["reviewer"] or not case["reviewed_at"]:
            errors.append(f"{case['id']}: reviewer and reviewed_at are required")
        if "advisory" not in case["permitted_outcome"].lower():
            errors.append(f"{case['id']}: permitted_outcome must remain advisory")

    if split_counts["development"] > value.get("development_target", 0):
        errors.append("development case count exceeds development_target")
    if value.get("status") == "development_intake_complete" and split_counts["development"] != value.get("development_target", 0):
        errors.append("complete development intake must equal development_target")
    if split_counts["holdout"] > value.get("holdout_target", 0):
        errors.append("holdout case count exceeds holdout_target")
    return errors


def main():
    path = Path(__file__).with_name("sysadmin-incident-intake-v1.json")
    errors = validate_intake(json.loads(path.read_text()))
    if errors:
        raise SystemExit("\n".join(errors))
    print("sysadmin incident intake: valid")


if __name__ == "__main__":
    main()
