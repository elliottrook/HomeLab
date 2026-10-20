"""Build a content-free evaluation plan only from a qualification-eligible corpus.

This module deliberately has no model, tool, network, or execution adapter.  It
is the fail-closed boundary between human-reviewed incident intake and any
future evaluation runner.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from validate_sysadmin_incident_intake import validate_for_qualification


class QualificationError(ValueError):
    """The corpus is structurally or procedurally ineligible for evaluation."""


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_evaluation_plan(value):
    """Return bounded metadata after enforcing the human-review boundary.

    The returned plan contains no prompt text, symptoms, source descriptions,
    case identifiers, permitted outcomes, or expected answers.  A later runner
    can bind to the digest, but it must receive its own authorization and must
    not treat this plan as model or tool promotion evidence.
    """
    errors = validate_for_qualification(value)
    if errors:
        raise QualificationError("corpus is not qualification eligible")

    cases = value["cases"]
    return {
        "schema": "aster-sysadmin-evaluation-plan.v1",
        "qualification_eligible": True,
        "corpus_schema_version": value["schema_version"],
        "corpus_sha256": hashlib.sha256(_canonical_bytes(value)).hexdigest(),
        "case_count": len(cases),
        "split_counts": dict(sorted(Counter(case["split"] for case in cases).items())),
        "family_counts": dict(sorted(Counter(case["family"] for case in cases).items())),
        "execution_authorized": False,
        "model_calls_authorized": False,
        "tool_calls_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    value = json.loads(args.path.read_text())
    try:
        plan = build_evaluation_plan(value)
    except QualificationError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(plan, sort_keys=True))


if __name__ == "__main__":
    main()
