import copy
import json
import unittest

from sa3_evidence_matrix_candidate_j_quality import run_quality, score_result
from sa3_evidence_matrix_candidate_j_quality_freeze import build


class CandidateJQualityTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.keys = build(); tick = [0.0]
        keyed = {row["id"]: row for row in self.keys["case_answer_keys"]}
        prompt_ids = {case["prompt"]: case["id"] for case in self.packet["cases"]}
        def monotonic(): tick[0] += 0.01; return tick[0]
        def transport(payload):
            request = json.loads(payload["messages"][1]["content"])
            selected = keyed[prompt_ids[request["prompt"]]]["expected_hypothesis_ids"]
            return {"choices": [{"message": {"role": "assistant", "content": json.dumps({"hypothesis_ids": selected})}, "finish_reason": "stop"}]}
        self.result = run_quality(self.packet, self.keys, transport,
                                  model="hidden-model", monotonic=monotonic)

    def test_exact_frozen_transaction_shape_scores(self):
        score = score_result(self.packet, self.keys, self.result)
        self.assertEqual(20, score["passed"])
        self.assertEqual(6, score["abstentions_passed"])
        self.assertTrue(score["deterministic_gate_met"])

    def test_request_error_and_retry_drift_fail_closed(self):
        for field, value in (("model_request_count", 13), ("retry_count", 1),
                             ("errors", [{"id": "x", "class": "ValueError"}])):
            changed = copy.deepcopy(self.result); changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                score_result(self.packet, self.keys, changed)

    def test_prediction_identity_and_false_completion_fail(self):
        changed = copy.deepcopy(self.result); changed["predictions"][0]["id"] = "foreign"
        with self.assertRaises(ValueError): score_result(self.packet, self.keys, changed)
        changed = copy.deepcopy(self.result); changed["predictions"][0]["summary"] = "Possible cause."
        score = score_result(self.packet, self.keys, changed)
        self.assertFalse(score["deterministic_gate_met"])
        self.assertEqual(1, score["false_completion_failures"])


if __name__ == "__main__": unittest.main()
