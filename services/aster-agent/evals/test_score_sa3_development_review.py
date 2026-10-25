import copy
import unittest

from prepare_sa3_development_review import RUBRIC, blank_review, canonical_bytes
from score_sa3_development_review import score


class DevelopmentReviewScoreTests(unittest.TestCase):
    def setUp(self):
        self.packet = {
            "schema": "aster-d4-model-blind-review-packet.v1",
            "candidate_alias": "candidate-A",
            "model_identity_disclosed": False,
            "timing_disclosed": False,
            "ledger_sha256": "a" * 64,
            "rubric": list(RUBRIC),
            "cases": [{"review_id": "D4R-01"}],
        }
        import hashlib
        self.packet_raw = canonical_bytes(self.packet)
        self.review = blank_review(hashlib.sha256(self.packet_raw).hexdigest(), self.packet)
        self.review["reviewer"] = "independent-reviewer"
        self.review["cases"][0]["judgments"] = {field: True for field in RUBRIC}

    def test_complete_review_is_summarized_without_notes(self):
        result = score(self.packet, self.review, self.packet_raw, expected_cases=1)
        self.assertEqual(result["all_dimensions_passed"], 1)
        self.assertEqual(result["dimension_pass_counts"], {field: 1 for field in RUBRIC})
        self.assertNotIn("notes", str(result))
        self.assertEqual(result["quality_gate"], "not_defined_for_development_set")

    def test_blank_or_nonblind_review_is_rejected(self):
        for change in (
            {"reviewer": ""},
            {"model_blind": False},
        ):
            review = dict(self.review, **change)
            with self.assertRaises(ValueError):
                score(self.packet, review, self.packet_raw, expected_cases=1)

    def test_missing_judgment_and_packet_drift_are_rejected(self):
        review = copy.deepcopy(self.review)
        review["cases"][0]["judgments"]["diagnosis"] = None
        with self.assertRaises(ValueError):
            score(self.packet, review, self.packet_raw, expected_cases=1)
        review = copy.deepcopy(self.review)
        review["packet_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            score(self.packet, review, self.packet_raw, expected_cases=1)

    def test_v2_summary_carries_registered_candidate_identity(self):
        import hashlib
        packet = dict(
            self.packet,
            schema="aster-d4-model-blind-review-packet.v2",
            candidate_alias="candidate-B",
            run_digest="d" * 64,
        )
        raw = canonical_bytes(packet)
        review = blank_review(hashlib.sha256(raw).hexdigest(), packet)
        review["reviewer"] = "independent-reviewer"
        review["cases"][0]["judgments"] = {field: True for field in RUBRIC}
        result = score(packet, review, raw, expected_cases=1)
        self.assertEqual("candidate-B", result["candidate_alias"])
        self.assertEqual("d" * 64, result["run_digest"])


if __name__ == "__main__":
    unittest.main()
