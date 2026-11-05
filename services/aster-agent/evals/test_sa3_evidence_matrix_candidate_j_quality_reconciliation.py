import copy
import json
import unittest

from sa3_evidence_matrix_candidate_j_quality_freeze import build, canonical
from sa3_evidence_matrix_candidate_j_quality_reconciliation import reconcile
from sa3_evidence_matrix_candidate_j_quality_runtime import run_quality


BOOKING = "aster-stream-a-sa3-candidate-j-quality-test"


def terminal():
    return {
        "schema": "aster-lab-hours-booked-result.v1", "state": "complete",
        "booking_id": BOOKING, "started_epoch": 100, "finished_epoch": 200,
        "request_count": 20,
        "workload": "sa3-evidence-matrix-candidate-j-quality-v1",
        "production_restored": True,
    }


class CandidateJQualityReconciliationTests(unittest.TestCase):
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
                                  model="hidden-model", monotonic=monotonic)

    def test_complete_gate_is_only_blind_review_eligible(self):
        summary = reconcile(BOOKING, canonical(terminal()), self.packet,
                            self.keys, canonical(self.result))
        self.assertEqual(20, summary["case_count"])
        self.assertEqual(14, summary["model_request_count"])
        self.assertEqual(6, summary["deterministic_abstentions"])
        self.assertEqual("eligible-for-three-reviewer-model-blind-review",
                         summary["quality_decision"])
        self.assertEqual("not-authorized", summary["promotion"])
        self.assertNotIn("hidden-model", json.dumps(summary))

    def test_terminal_drift_fails_closed(self):
        for field, changed in (("state", "no_go"),
                               ("production_restored", False),
                               ("request_count", 14),
                               ("booking_id", "other"),
                               ("workload", "other")):
            value = copy.deepcopy(terminal()); value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                reconcile(BOOKING, canonical(value), self.packet, self.keys,
                          canonical(self.result))

    def test_quality_regression_fails_closed(self):
        value = copy.deepcopy(self.result)
        value["predictions"][0]["summary"] = "Possible cause."
        with self.assertRaisesRegex(ValueError, "quality gate"):
            reconcile(BOOKING, canonical(terminal()), self.packet, self.keys,
                      canonical(value))

    def test_strict_prediction_and_duplicate_json_fail_closed(self):
        value = copy.deepcopy(self.result)
        value["predictions"][0]["prose_source"] = "changed"
        with self.assertRaisesRegex(ValueError, "prediction"):
            reconcile(BOOKING, canonical(terminal()), self.packet, self.keys,
                      canonical(value))
        duplicate = canonical(terminal()).replace(
            b'"state":"complete"', b'"state":"complete","state":"complete"')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reconcile(BOOKING, duplicate, self.packet, self.keys,
                      canonical(self.result))


if __name__ == "__main__":
    unittest.main()
