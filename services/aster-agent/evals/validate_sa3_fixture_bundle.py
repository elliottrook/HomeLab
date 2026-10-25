"""Validate a source-bound, synthetic SA3 development fixture bundle."""

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from sa3_investigation import _validated_case


SHA256 = re.compile(r"[a-f0-9]{64}\Z")
BASE_TOP_LEVEL_FIELDS = {
    "schema",
    "classification",
    "status",
    "source_corpus_sha256",
    "source_plan_sha256",
    "source_case_sha256",
    "model_calls_authorized",
    "tool_calls_authorized",
    "cases",
}
REVIEW_FIELDS = {"reviewed_by", "reviewed_at", "fixture_source_sha256"}


def _canonical_sha256(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def review_source_sha256(value):
    """Digest the exact reviewable content, excluding its later acceptance record."""
    draft = copy.deepcopy(value)
    draft.pop("fixture_review", None)
    draft["status"] = "draft_fixtures_require_jason_review"
    return _canonical_sha256(draft)


def validate_bundle(value, source_corpus, source_plan):
    errors = []
    if (
        not isinstance(value, dict)
        or set(value) not in (BASE_TOP_LEVEL_FIELDS, BASE_TOP_LEVEL_FIELDS | {"fixture_review"})
    ):
        return ["fixture bundle has unexpected top-level shape"]
    if value["schema"] != "aster-sa3-development-fixtures.v1":
        errors.append("fixture bundle schema must be v1")
    if value["classification"] != "public synthetic development; review required; never a held-out benchmark":
        errors.append("fixture classification must remain public synthetic development")
    if value["model_calls_authorized"] is not False or value["tool_calls_authorized"] is not False:
        errors.append("fixture bundle must not authorize model or tool calls")
    if value["source_corpus_sha256"] != hashlib.sha256(source_corpus.read_bytes()).hexdigest():
        errors.append("fixture source corpus digest mismatch")
    if value["source_plan_sha256"] != hashlib.sha256(source_plan.read_bytes()).hexdigest():
        errors.append("fixture source plan digest mismatch")

    source = json.loads(source_corpus.read_text())
    source_cases = source.get("cases", [])
    source_ids = [case.get("id") for case in source_cases if isinstance(case, dict)]
    bindings = value["source_case_sha256"]
    expected_bindings = {case["id"]: _canonical_sha256(case) for case in source_cases}
    if not isinstance(bindings, dict) or bindings != expected_bindings:
        errors.append("fixture source case bindings mismatch")
    cases = value["cases"]
    if not isinstance(cases, list):
        return errors + ["fixture cases must be a list"]
    if [case.get("id") for case in cases if isinstance(case, dict)] != source_ids:
        errors.append("fixture cases must exactly match source case order")
    for case in cases:
        try:
            _validated_case(case)
        except (TypeError, ValueError):
            errors.append(f"{case.get('id', '<missing id>') if isinstance(case, dict) else '<invalid case>'}: invalid investigation fixture")
    return errors


def validate_for_qualification(value, source_corpus, source_plan):
    errors = validate_bundle(value, source_corpus, source_plan)
    if not isinstance(value, dict):
        return errors
    if value.get("status") != "development_fixtures_reviewed":
        errors.append("fixture qualification requires reviewed status")
    review = value.get("fixture_review")
    if (
        not isinstance(review, dict)
        or set(review) != REVIEW_FIELDS
        or review.get("reviewed_by") != "Jason"
        or not isinstance(review.get("reviewed_at"), str)
        or not review["reviewed_at"]
        or not isinstance(review.get("fixture_source_sha256"), str)
        or SHA256.fullmatch(review["fixture_source_sha256"]) is None
        or review["fixture_source_sha256"] != review_source_sha256(value)
    ):
        errors.append("fixture qualification requires a bound Jason review")
    return errors


def main(argv=None):
    here = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--source-corpus", type=Path, default=here / "sysadmin-incident-development-extension-draft-v1.json")
    parser.add_argument("--source-plan", type=Path, default=here / "sysadmin-incident-development-plan-v1.json")
    parser.add_argument("--qualification", action="store_true")
    args = parser.parse_args(argv)
    value = json.loads(args.path.read_text())
    validator = validate_for_qualification if args.qualification else validate_bundle
    errors = validator(value, args.source_corpus, args.source_plan)
    if errors:
        raise SystemExit("\n".join(errors))
    print("SA3 fixture bundle: " + ("qualification eligible" if args.qualification else "structurally valid"))


if __name__ == "__main__":
    main()
