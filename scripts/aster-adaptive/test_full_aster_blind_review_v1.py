import copy
import unittest

import full_aster_blind_review_v1 as review
from test_full_aster_capture_v1 import fixtures


class FullAsterBlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.contract, self.baseline = fixtures()
        self.challenger = copy.deepcopy(self.baseline)
        self.challenger.update(role="challenger", model_sha256="c" * 64,
                               runtime_sha256="d" * 64,
                               mode="reasoning-on-27b-plus")
        for row in self.challenger["rows"]:
            row["answer"] = "Different fictional answer"

    def test_packet_is_backend_blind_and_key_is_separate(self):
        packet, template, key = review.prepare(
            self.contract, self.packet, self.baseline, self.challenger, 1, "e" * 64)
        visible = review.canonical(packet).decode()
        self.assertNotIn("baseline", visible)
        self.assertNotIn("challenger", visible)
        self.assertNotIn("a" * 64, visible)
        self.assertIsNone(template["reviewer_id"])
        self.assertEqual(24, len(key["cases"]))
        self.assertEqual(review._digest(packet), template["packet_sha256"])

    def test_two_reviewers_receive_independent_alias_orders(self):
        first, _, _ = review.prepare(self.contract, self.packet, self.baseline,
                                     self.challenger, 1, "f" * 64)
        second, _, _ = review.prepare(self.contract, self.packet, self.baseline,
                                      self.challenger, 2, "f" * 64)
        orders = lambda packet: [row["answers"][0]["answer"] for row in packet["cases"]]
        self.assertNotEqual(orders(first), orders(second))

    def test_invalid_capture_or_blinding_input_fails_closed(self):
        changed = copy.deepcopy(self.challenger)
        changed["retry_count"] = 1
        with self.assertRaises(ValueError):
            review.prepare(self.contract, self.packet, self.baseline, changed, 1, "a" * 64)
        with self.assertRaises(ValueError):
            review.prepare(self.contract, self.packet, self.baseline,
                           self.challenger, 3, "a" * 64)

    def test_review_template_has_explicit_quality_and_safety_fields(self):
        _, template, _ = review.prepare(self.contract, self.packet, self.baseline,
                                        self.challenger, 1, "b" * 64)
        answer = template["cases"][0]["answers"][0]
        self.assertEqual({"fabricated_effect_claim", "unsafe_action_advice",
                          "privacy_underclassification", "out_of_allowlist_capability"},
                         set(answer["safety_failures"]))
        self.assertIsNone(answer["outcome_ok"])


if __name__ == "__main__":
    unittest.main()
