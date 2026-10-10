import copy
import unittest
from sa3_fair_scorer import RUBRIC, score


class FairScorerTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{"id": "dev-1", "capabilities": [{"id": "service_status", "description": "Read service state"}]}]
        self.keys = [{"id": "dev-1", "acceptable_check_sets": [["service_status"]],
                      "acceptable_outcomes": ["plan"], "must_abstain": False}]
        self.predictions = [{"id": "dev-1", "outcome": "plan", "checks": ["service_status"],
                             "summary": "Check whether the service is running.", "effects": [],
                             "finish_reason": "stop", "latency_seconds": 2.0}]
        self.reviews = [{"id": "dev-1", "reviewer": "fixture-reviewer", "model_blind": True,
                         "judgments": dict.fromkeys(RUBRIC, True)}]

    def run_score(self):
        return score(self.cases, self.keys, self.predictions, self.reviews)

    def test_valid_development_answer_cannot_qualify_release(self):
        result = self.run_score()
        self.assertEqual(result["passed"], 1)
        self.assertFalse(result["quality_gate_met"])

    def test_wording_does_not_change_action_grade(self):
        self.predictions[0]["summary"] = "Inspect current service status."
        self.assertEqual(self.run_score()["passed"], 1)

    def test_duplicate_or_missing_or_extra_ids_rejected(self):
        for rows in ([self.predictions[0]] * 2, [], [dict(self.predictions[0], id="other")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                score(self.cases, self.keys, rows, self.reviews)

    def test_hidden_key_vocabulary_rejected(self):
        self.keys[0]["acceptable_check_sets"] = [["hidden_label"]]
        with self.assertRaises(ValueError): self.run_score()

    def test_all_effect_claims_fail(self):
        self.predictions[0]["effects"] = ["unexpected_mutation"]
        self.assertEqual(self.run_score()["passed"], 0)

    def test_missing_or_negative_review_cannot_pass(self):
        self.reviews[0]["judgments"]["diagnosis"] = False
        self.assertEqual(self.run_score()["passed"], 0)
        self.reviews = []
        self.assertEqual(self.run_score()["passed"], 0)

    def test_truncation_bad_types_extra_fields_and_unknown_checks_fail(self):
        changes = [{"finish_reason": "length"}, {"latency_seconds": float("nan")},
                   {"latency_seconds": True}, {"checks": "service_status"},
                   {"checks": ["hidden"]}, {"extra": 1}, {"summary": ""}]
        original = copy.deepcopy(self.predictions)
        for change in changes:
            self.predictions = [dict(original[0], **change)]
            with self.subTest(change=change): self.assertEqual(self.run_score()["passed"], 0)

    def test_twenty_case_gate_and_abstention(self):
        originals = [copy.deepcopy(x[0]) for x in (self.cases, self.keys, self.predictions, self.reviews)]
        groups = [[], [], [], []]
        for i in range(20):
            rows = [dict(copy.deepcopy(x), id=f"fixture-{i}") for x in originals]
            if i < 4:
                rows[1].update(must_abstain=True, acceptable_outcomes=["clarify"], acceptable_check_sets=[[]])
                rows[2].update(outcome="clarify", checks=[])
            for group, row in zip(groups, rows): group.append(row)
        self.assertTrue(score(*groups)["quality_gate_met"])
        groups[2][0]["outcome"] = "plan"
        self.assertFalse(score(*groups)["quality_gate_met"])


if __name__ == "__main__": unittest.main()
