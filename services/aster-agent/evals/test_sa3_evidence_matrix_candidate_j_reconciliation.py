import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_matrix_candidate_j_batch import run_public
from sa3_evidence_matrix_candidate_j_reconciliation import reconcile


ROOT = Path(__file__).parent
FIXTURE = json.loads((ROOT /
    "sa3-evidence-matrix-candidate-j-public-v1.json").read_text())
BOOKING = "aster-stream-a-sa3-candidate-j-test"


def response(payload):
    request = json.loads(payload["messages"][1]["content"])
    selected = request["eligible_hypothesis_ids"][0]
    return {"choices": [{"message": {"role": "assistant", "content":
        json.dumps({"hypothesis_ids": [selected]})},
        "finish_reason": "stop"}]}


def result():
    return run_public(FIXTURE, response, model="hidden-model",
                      monotonic=lambda: 1.0)


def terminal():
    return {
        "schema": "aster-lab-hours-booked-result.v1", "state": "complete",
        "booking_id": BOOKING, "started_epoch": 100, "finished_epoch": 200,
        "request_count": 6,
        "workload": "sa3-evidence-matrix-candidate-j-public-v1",
        "production_restored": True,
    }


class CandidateJReconciliationTests(unittest.TestCase):
    def test_complete_six_of_six_is_only_untouched_freeze_eligible(self):
        summary = reconcile(BOOKING, terminal(), FIXTURE, result())
        self.assertEqual(6, summary["case_count"])
        self.assertEqual(2, summary["model_request_count"])
        self.assertEqual(4, summary["deterministic_abstentions"])
        self.assertEqual("eligible-for-distinct-untouched-evaluation-freeze",
                         summary["quality_decision"])
        self.assertEqual("none", summary["authority"])
        self.assertNotIn("hidden-model", json.dumps(summary))

    def test_terminal_drift_fails_closed(self):
        for field, changed in (("state", "no_go"),
                               ("production_restored", False),
                               ("request_count", 2),
                               ("booking_id", "other"),
                               ("workload", "other")):
            value = copy.deepcopy(terminal()); value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                reconcile(BOOKING, value, FIXTURE, result())

    def test_less_than_six_public_passes_fails_closed(self):
        value = result()
        value["predictions"][0]["checks"] = ["different_check"]
        with self.assertRaisesRegex(ValueError, "public gate"):
            reconcile(BOOKING, terminal(), FIXTURE, value)


if __name__ == "__main__":
    unittest.main()
