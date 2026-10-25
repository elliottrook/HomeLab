import copy
import hashlib
import json
from pathlib import Path
import unittest

from validate_sa3_fixture_bundle import (
    _canonical_sha256,
    review_source_sha256,
    validate_bundle,
    validate_for_qualification,
)


class FixtureBundleTests(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).parent
        self.source = here / "sysadmin-incident-development-extension-draft-v1.json"
        self.plan = here / "sysadmin-incident-development-plan-v1.json"
        source = json.loads(self.source.read_text())
        cases = []
        for item in source["cases"]:
            cases.append({
                "id": item["id"],
                "prompt": f"Synthetic incident {item['id']}; investigate without effects.",
                "capabilities": [{"id": "status", "description": "Read synthetic status."}],
                "initial_observations": [{"id": "initial", "freshness": "stale", "text": "Synthetic symptom is unresolved."}],
                "responses": {"status": {"id": "status-result", "freshness": "current", "text": "Synthetic bounded status result."}},
            })
        self.value = {
            "schema": "aster-sa3-development-fixtures.v1",
            "classification": "public synthetic development; review required; never a held-out benchmark",
            "status": "draft_fixtures_require_jason_review",
            "source_corpus_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "source_plan_sha256": hashlib.sha256(self.plan.read_bytes()).hexdigest(),
            "source_case_sha256": {item["id"]: _canonical_sha256(item) for item in source["cases"]},
            "model_calls_authorized": False,
            "tool_calls_authorized": False,
            "cases": cases,
        }

    def test_structural_validation_accepts_bound_draft(self):
        self.assertEqual(validate_bundle(self.value, self.source, self.plan), [])

    def test_digests_order_and_authority_fail_closed(self):
        for mutation, expected in (
            (("source_corpus_sha256", "0" * 64), "fixture source corpus digest mismatch"),
            (("source_plan_sha256", "0" * 64), "fixture source plan digest mismatch"),
            (("model_calls_authorized", True), "fixture bundle must not authorize model or tool calls"),
        ):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.value)
                changed[mutation[0]] = mutation[1]
                self.assertIn(expected, validate_bundle(changed, self.source, self.plan))
        changed = copy.deepcopy(self.value)
        changed["cases"].reverse()
        self.assertIn("fixture cases must exactly match source case order", validate_bundle(changed, self.source, self.plan))

    def test_qualification_requires_exact_bound_review(self):
        self.assertIn("fixture qualification requires reviewed status", validate_for_qualification(self.value, self.source, self.plan))
        reviewed = copy.deepcopy(self.value)
        reviewed["status"] = "development_fixtures_reviewed"
        reviewed["fixture_review"] = {
            "reviewed_by": "Jason",
            "reviewed_at": "2026-10-24",
            "fixture_source_sha256": review_source_sha256(reviewed),
        }
        self.assertEqual(validate_for_qualification(reviewed, self.source, self.plan), [])

        reviewed["cases"][0]["prompt"] += " changed"
        self.assertIn(
            "fixture qualification requires a bound Jason review",
            validate_for_qualification(reviewed, self.source, self.plan),
        )

    def test_invalid_fixture_is_rejected_before_execution(self):
        changed = copy.deepcopy(self.value)
        changed["cases"][0]["responses"] = {}
        errors = validate_bundle(changed, self.source, self.plan)
        self.assertTrue(any("invalid investigation fixture" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
