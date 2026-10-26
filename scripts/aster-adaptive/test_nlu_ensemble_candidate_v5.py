import unittest

import nlu_ensemble_candidate_v5 as candidate


class NluEnsembleCandidateV5Tests(unittest.TestCase):
    def test_vague_change_and_household_referents_clarify(self):
        self.assertEqual({
            "request_family": "change-request", "sensitivity": "internal",
            "capability_needs": [], "ambiguity": "ambiguous",
            "disposition": "clarify", "reason": "ambiguous",
        }, candidate.classify_deterministically("Fix it"))
        self.assertEqual(
            "household-command",
            candidate.classify_deterministically("Turn it off")["request_family"],
        )

    def test_clear_and_long_requests_continue_to_semantic_candidate(self):
        self.assertIsNone(candidate.classify_deterministically("Restart the named Aster service"))
        self.assertIsNone(candidate.classify_deterministically(
            "Please explain why this scientific effect changes over several years"
        ))

    def test_empty_request_fails(self):
        with self.assertRaises(ValueError):
            candidate.classify_deterministically("  ")


if __name__ == "__main__":
    unittest.main()
