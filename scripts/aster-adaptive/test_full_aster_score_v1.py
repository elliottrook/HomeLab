import copy
import unittest

import full_aster_blind_review_v1 as blind
import full_aster_score_v1 as scoring
from test_full_aster_capture_v1 import fixtures


def complete_review(template, reviewer):
    value = copy.deepcopy(template); value["reviewer_id"] = reviewer
    for case in value["cases"]:
        for answer in case["answers"]:
            answer["outcome_ok"] = True
            answer["required_facts"] = [True] * len(answer["required_facts"])
            answer["completion_criteria"] = [True] * len(answer["completion_criteria"])
            answer["prohibited_claims_present"] = [False] * len(answer["prohibited_claims_present"])
            answer["citation_ok"] = True
            answer["safety_failures"] = {key: False for key in answer["safety_failures"]}
    return value


class FullAsterScoreTests(unittest.TestCase):
    def setUp(self):
        self.owner, self.contract, self.baseline = fixtures()
        self.challenger = copy.deepcopy(self.baseline)
        self.challenger.update(role="challenger", model_sha256="c" * 64,
                               runtime_sha256="d" * 64,
                               mode="reasoning-on-27b-plus")
        self.reviews = []
        for slot, nonce in ((1, "e" * 64), (2, "f" * 64)):
            packet, template, key = blind.prepare(self.contract, self.owner,
                self.baseline, self.challenger, slot, nonce)
            self.reviews.append((packet, complete_review(template, f"reviewer-{slot}"), key))
        self.recovery = {"f6_admitted": True, "exact_baseline_restored": True,
                         "independent_observer_passed": True,
                         "uncertain_recovery": False}

    def test_complete_passing_comparison_is_accepted_without_authority(self):
        result = scoring.score(self.contract, self.owner, self.baseline,
                               self.challenger, self.reviews, self.recovery)
        self.assertTrue(result["accepted"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_one_reviewer_failure_fails_quality(self):
        for case in self.reviews[0][1]["cases"][:2]:
            for answer in case["answers"]:
                answer["outcome_ok"] = False
        result = scoring.score(self.contract, self.owner, self.baseline,
                               self.challenger, self.reviews, self.recovery)
        self.assertFalse(result["accepted"])

    def test_safety_or_latency_or_recovery_failure_rejects(self):
        changed = copy.deepcopy(self.reviews)
        changed[0][1]["cases"][0]["answers"][0]["safety_failures"][
            "fabricated_effect_claim"] = True
        self.assertFalse(scoring.score(self.contract, self.owner, self.baseline,
                                       self.challenger, changed, self.recovery)["accepted"])
        slow = copy.deepcopy(self.challenger)
        for row in slow["rows"][:2]:
            row["end_to_end_ms"] = 20000
        self.assertFalse(scoring.score(self.contract, self.owner, self.baseline,
                                       slow, self.reviews, self.recovery)["accepted"])
        bad_recovery = {**self.recovery, "uncertain_recovery": True,
                        "exact_baseline_restored": False}
        with self.assertRaises(ValueError):
            scoring.score(self.contract, self.owner, self.baseline,
                          self.challenger, self.reviews, bad_recovery)

    def test_duplicate_reviewer_is_rejected(self):
        self.reviews[1][1]["reviewer_id"] = "reviewer-1"
        with self.assertRaises(ValueError):
            scoring.score(self.contract, self.owner, self.baseline,
                          self.challenger, self.reviews, self.recovery)


if __name__ == "__main__":
    unittest.main()
