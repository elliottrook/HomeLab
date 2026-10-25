import copy
import json
from pathlib import Path
import unittest

from evaluate_sa3_development_gate import evaluate
from prepare_sa3_development_review import RUBRIC


class DevelopmentGateTests(unittest.TestCase):
    def setUp(self):
        self.rule_path = Path(__file__).with_name("sa3-development-decision-rule-v3.json")
        self.rule_raw = self.rule_path.read_bytes()
        self.rule = json.loads(self.rule_raw)
        self.summary = {
            "schema": "aster-d4-model-blind-review-summary.v1",
            "packet_sha256": "a" * 64,
            "reviewer": "fresh-model-blind-reviewer",
            "model_blind": True,
            "cases": 12,
            "all_dimensions_passed": 12,
            "dimension_pass_counts": {field: 12 for field in RUBRIC},
            "rows": [
                {"review_id": f"D4R-{index:02d}", "all_dimensions_pass": True}
                for index in range(1, 13)
            ],
            "quality_gate": "not_defined_for_development_set",
            "limit": "development review only; no role, route, tool or deployment promotion",
            "run_digest": self.rule["expected_run_digest"],
            "candidate_alias": self.rule["candidate_alias"],
        }

    def test_exact_all_dimension_pass_is_eligible_only_to_design(self):
        result = evaluate(self.rule, self.summary, self.rule_raw)
        self.assertEqual("pass", result["decision"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual([], result["failed_dimensions"])
        self.assertIn("design", result["outcome"])

    def test_one_failed_dimension_is_no_go(self):
        summary = copy.deepcopy(self.summary)
        summary["dimension_pass_counts"]["verification"] = 11
        summary["all_dimensions_passed"] = 11
        summary["rows"][-1]["all_dimensions_pass"] = False
        result = evaluate(self.rule, summary, self.rule_raw)
        self.assertEqual("no-go", result["decision"])
        self.assertEqual(["verification"], result["failed_dimensions"])

    def test_run_candidate_or_row_drift_fails_closed(self):
        for field, value in (
            ("run_digest", "b" * 64),
            ("candidate_alias", "candidate-C"),
        ):
            with self.subTest(field=field):
                summary = dict(self.summary, **{field: value})
                with self.assertRaises(ValueError):
                    evaluate(self.rule, summary, self.rule_raw)
        summary = copy.deepcopy(self.summary)
        summary["rows"][-1]["review_id"] = summary["rows"][0]["review_id"]
        with self.assertRaisesRegex(ValueError, "identity"):
            evaluate(self.rule, summary, self.rule_raw)

    def test_post_result_rule_changes_are_not_accepted_as_the_frozen_rule(self):
        changed = copy.deepcopy(self.rule)
        changed["minimum_dimension_pass_counts"]["verification"] = 0
        result = evaluate(changed, self.summary)
        self.assertNotEqual(result["rule_sha256"], evaluate(
            self.rule, self.summary, self.rule_raw
        )["rule_sha256"])


if __name__ == "__main__":
    unittest.main()
