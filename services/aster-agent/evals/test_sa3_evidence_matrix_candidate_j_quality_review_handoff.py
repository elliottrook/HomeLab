import copy
import json
import unittest

from sa3_evidence_matrix_candidate_j_quality_freeze import build
from sa3_evidence_matrix_candidate_j_quality_review_handoff import build_handoff
from sa3_evidence_matrix_candidate_j_quality_runtime import run_quality


class CandidateJQualityReviewHandoffTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.keys = build(); tick = [0.0]
        keyed = {row["id"]: row for row in self.keys["case_answer_keys"]}
        prompt_ids = {case["prompt"]: case["id"] for case in self.packet["cases"]}
        def monotonic(): tick[0] += 0.01; return tick[0]
        def transport(payload):
            request = json.loads(payload["messages"][1]["content"])
            selected = keyed[prompt_ids[request["prompt"]]]["expected_hypothesis_ids"]
            return {"choices": [{"message": {"role": "assistant", "content":
                json.dumps({"hypothesis_ids": selected})}, "finish_reason": "stop"}]}
        self.result = run_quality(self.packet, transport,
                                  model="secret-backend-identity", monotonic=monotonic)

    def test_handoff_is_bound_complete_and_model_blind(self):
        handoff = build_handoff(self.packet, self.result)
        self.assertEqual(20, len(handoff["review_packet"]["cases"]))
        self.assertEqual(3, handoff["required_distinct_reviewers"])
        self.assertFalse(handoff["model_identity_disclosed"])
        self.assertEqual("not-authorized", handoff["promotion"])
        self.assertNotIn("secret-backend-identity", json.dumps(handoff))
        self.assertEqual(handoff["review_packet_sha256"],
                         handoff["review_template"]["review_packet_sha256"])

    def test_incomplete_result_fails_closed(self):
        changed = copy.deepcopy(self.result)
        changed["predictions"].pop()
        with self.assertRaises(ValueError):
            build_handoff(self.packet, changed)


if __name__ == "__main__":
    unittest.main()
