import unittest

import nlu_ensemble_candidate_v3 as candidate


def label(disposition="route"):
    return {
        "request_family": "general-answer", "sensitivity": "public",
        "capability_needs": ["facts.answer"], "ambiguity": "clear",
        "disposition": disposition,
        "reason": "understood" if disposition == "route" else "policy-denied",
    }


class NluEnsembleCandidateV3Tests(unittest.TestCase):
    def test_one_missing_vote_caps_confidence_at_two_thirds(self):
        result = candidate.aggregate_available([label(), label()])
        self.assertEqual(2 / 3, result["decision_score"])
        self.assertEqual(2 / 3, result["route_score"])
        self.assertEqual("not-granted", result["authority"])

    def test_two_or_zero_valid_votes_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            candidate.aggregate_available([label()])
        with self.assertRaisesRegex(ValueError, "at least two"):
            candidate.aggregate_available([])

    def test_disagreement_with_two_votes_has_one_third_confidence(self):
        result = candidate.aggregate_available([label(), label("deny")])
        self.assertEqual(1 / 3, result["decision_score"])
        self.assertEqual(1 / 3, result["route_score"])


if __name__ == "__main__":
    unittest.main()
