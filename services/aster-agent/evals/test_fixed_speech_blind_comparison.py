from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from prepare_fixed_speech_blind_comparison import build_packet
from score_fixed_speech_blind_comparison import score


ROOT = Path(__file__).parent


class FixedSpeechBlindComparisonTests(unittest.TestCase):
    def setUp(self):
        raw = (ROOT / "fixed-speech-blind-comparison-v1.json").read_bytes()
        self.packet, artifacts = build_packet(raw)
        self.template, self.key = artifacts["template"], artifacts["key"]

    def completed_review(self):
        review = json.loads(json.dumps(self.template))
        review["reviewer"] = "independent-reviewer"
        slots = {row["id"]: row["fixed_slot"] for row in self.key["rows"]}
        for row in review["cases"]:
            fixed = slots[row["id"]]
            row["preferred"] = fixed
            for dimension in row["dimensions"].values():
                dimension[fixed] = True
        return review

    def test_packet_hides_candidate_identity_and_balances_slots(self):
        encoded = json.dumps(self.packet, sort_keys=True).lower()
        self.assertNotIn("fixed speech", encoded)
        self.assertNotIn("aggregate-health", encoded)
        slots = [row["fixed_slot"] for row in self.key["rows"]]
        self.assertGreaterEqual(slots.count("A"), 2)
        self.assertGreaterEqual(slots.count("B"), 2)

    def test_complete_favorable_review_passes(self):
        result = score(self.packet, self.key, self.completed_review())
        self.assertTrue(result["passed"])
        self.assertEqual(result["fixed_preferred"], 8)
        self.assertEqual(result["fixed_unsafe_claims"], 0)

    def test_incomplete_and_nonblind_reviews_fail_closed(self):
        review = self.completed_review()
        review["implementation_blind"] = False
        with self.assertRaises(ValueError):
            score(self.packet, self.key, review)
        review = self.completed_review()
        review["cases"][0]["preferred"] = ""
        with self.assertRaises(ValueError):
            score(self.packet, self.key, review)

    def test_unsafe_or_insufficient_preference_rejects(self):
        review = self.completed_review()
        slots = {row["id"]: row["fixed_slot"] for row in self.key["rows"]}
        for row in review["cases"][:3]:
            row["preferred"] = "B" if slots[row["id"]] == "A" else "A"
        review["cases"][3]["unsafe_claims"][slots[review["cases"][3]["id"]]] = ["broader_health"]
        result = score(self.packet, self.key, review)
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
