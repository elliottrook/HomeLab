from __future__ import annotations

import json
import unittest

import run_fixed_speech_blind_review as review


class BlindReviewRunnerTests(unittest.TestCase):
    def test_payload_contains_only_case_and_blind_rubric(self):
        case = {"id": "fs-cmp-01", "question": "Question", "responses": {"A": "one", "B": "two"}}
        payload = json.loads(review.build_payload(case))
        self.assertEqual(json.loads(payload["messages"][1]["content"]), case)
        encoded = json.dumps(payload).lower()
        self.assertNotIn("fixed_slot", encoded)
        self.assertNotIn("minimum_fixed", encoded)

    def test_complete_judgment_validates(self):
        value = {
            "preferred": "A",
            "dimensions": {name: {"A": True, "B": False} for name in review.DIMENSIONS},
            "unsafe_claims": {"A": [], "B": ["broader_health"]},
            "note": "A is narrower.",
        }
        self.assertEqual(review.validate_judgment(value), value)

    def test_malformed_or_unknown_unsafe_claim_fails(self):
        value = {
            "preferred": "A",
            "dimensions": {name: {"A": True, "B": False} for name in review.DIMENSIONS},
            "unsafe_claims": {"A": [], "B": ["invented"]},
            "note": "",
        }
        with self.assertRaises(ValueError):
            review.validate_judgment(value)


if __name__ == "__main__":
    unittest.main()
