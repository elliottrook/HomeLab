"""Validate sysadmin-incident intake structure and qualification eligibility."""

import argparse
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


def validate_for_qualification(value):
    """Reject structurally valid drafts that have not completed human review.

    ``validate_intake`` deliberately checks the shape of work-in-progress
    corpora so draft extensions can be tested offline.  Qualification is a
    separate boundary: a caller must not infer approval from schema validity.
    """
    errors = validate_intake(value)
    if value.get("status") != "development_intake_complete":
        errors.append("qualification requires status development_intake_complete")

    provenance = value.get("extension_provenance")
    if provenance is not None:
        claim = provenance.get("claim", "") if isinstance(provenance, dict) else ""
        if not isinstance(provenance, dict) or "not Jason-reviewed" in claim:
            errors.append("qualification rejects unreviewed extension provenance")

    for case in value.get("cases", []):
        identifier = case.get("id", "<missing id>")
        if case.get("reviewer") != "Jason":
            errors.append(f"{identifier}: qualification requires Jason review")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", nargs="?", type=Path,
        default=Path(__file__).with_name("sysadmin-incident-intake-v1.json"),
    )
    parser.add_argument(
        "--qualification", action="store_true",
        help="require completed human review rather than structural validity only",
    )
    args = parser.parse_args(argv)
    value = json.loads(args.path.read_text())
    errors = (validate_for_qualification(value) if args.qualification
              else validate_intake(value))
    if errors:
        raise SystemExit("\n".join(errors))
    state = "qualification eligible" if args.qualification else "structurally valid"
    print(f"sysadmin incident intake: {state}")


if __name__ == "__main__":
    main()
