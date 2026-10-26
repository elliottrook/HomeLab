import unittest

import nlu_ensemble_candidate_v6 as candidate


class NluEnsembleCandidateV6Tests(unittest.TestCase):
    def test_all_invalid_fallback_has_zero_confidence_and_no_authority(self):
        result = candidate.fallback_rejected("Inspect the named service")
        self.assertEqual(0.0, result["decision_score"])
        self.assertEqual(0.0, result["route_score"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])


if __name__ == "__main__":
    unittest.main()
