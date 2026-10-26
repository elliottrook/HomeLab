import unittest

import nlu_ensemble_candidate_v4 as candidate


LABEL = {
    "request_family": "general-answer", "sensitivity": "public",
    "capability_needs": ["facts.answer"], "ambiguity": "clear",
    "disposition": "route", "reason": "understood",
}


class NluEnsembleCandidateV4Tests(unittest.TestCase):
    def test_one_valid_vote_is_retained_at_one_third_confidence(self):
        result = candidate.aggregate_available([LABEL])
        self.assertEqual(1 / 3, result["decision_score"])
        self.assertEqual(1 / 3, result["route_score"])
        self.assertEqual("not-granted", result["authority"])

    def test_zero_valid_votes_fail_closed(self):
        with self.assertRaises(ValueError):
            candidate.aggregate_available([])


if __name__ == "__main__":
    unittest.main()
