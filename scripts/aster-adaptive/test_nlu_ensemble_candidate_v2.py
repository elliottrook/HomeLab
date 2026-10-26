import json
import unittest

import nlu_ensemble_candidate_v2 as candidate
import nlu_local_model_adapter_v10 as base


class NluEnsembleCandidateV2Tests(unittest.TestCase):
    def test_first_vote_is_exact_v10_payload(self):
        text = "Could you change that setting?"
        self.assertEqual(base.build_payload(text), candidate.build_payload(text, 0))

    def test_other_votes_are_distinct_and_tool_free(self):
        payloads = [candidate.build_payload("What is rain?", index) for index in range(3)]
        self.assertEqual(3, len(set(payloads)))
        for raw in payloads:
            self.assertNotIn("tools", json.loads(raw))

    def test_invalid_perspective_fails(self):
        with self.assertRaises(ValueError):
            candidate.build_payload("test", 3)


if __name__ == "__main__":
    unittest.main()
