import copy
import json
import unittest

from sa3_evidence_matrix_candidate_j_batch import run_public
from sa3_evidence_matrix_candidate_j_public import FIXTURE, score_result


class CandidateJBatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text())

    @staticmethod
    def transport(payload):
        request = json.loads(payload["messages"][1]["content"])
        value = {"hypothesis_ids": [request["eligible_hypothesis_ids"][0]]}
        return {"choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant",
                                         "content": json.dumps(value)}}]}

    def test_exact_batch_uses_two_calls_and_passes_public_gate(self):
        result = run_public(self.fixture, self.transport, model="fixed-model",
                            monotonic=lambda: 1.0)
        self.assertEqual(2, result["model_request_count"])
        self.assertEqual([], result["errors"])
        score = score_result(self.fixture, result)
        self.assertEqual(6, score["passed"])
        self.assertTrue(score["public_gate_met"])

    def test_transport_error_is_retained_once_and_rejected(self):
        calls = []
        def broken(payload):
            calls.append(payload); raise RuntimeError("synthetic")
        result = run_public(self.fixture, broken, model="fixed-model",
                            monotonic=lambda: 2.0)
        self.assertEqual(2, len(calls))
        self.assertEqual(2, result["model_request_count"])
        self.assertEqual(2, len(result["errors"]))
        with self.assertRaisesRegex(ValueError, "ineligible"):
            score_result(self.fixture, result)

    def test_result_identity_count_and_prediction_drift_fail(self):
        baseline = run_public(self.fixture, self.transport, model="fixed-model",
                              monotonic=lambda: 3.0)
        variants = []
        identity = copy.deepcopy(baseline); identity["candidate_alias"] = "candidate-i"
        variants.append(identity)
        requests = copy.deepcopy(baseline); requests["model_request_count"] = 3
        variants.append(requests)
        duplicate = copy.deepcopy(baseline)
        duplicate["predictions"][1]["id"] = duplicate["predictions"][0]["id"]
        variants.append(duplicate)
        for result in variants:
            with self.subTest(result=result), self.assertRaises(ValueError):
                score_result(self.fixture, result)


if __name__ == "__main__":
    unittest.main()
