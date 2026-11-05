import copy
import json
import unittest

from sa3_evidence_matrix_candidate_j_quality_freeze import build, canonical
from sa3_evidence_matrix_candidate_j_quality_reconciliation import (
    reconcile, reconcile_evidence,
)
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


def booking():
    return {
        "schema": "aster-lab-hours-reservation.v1", "booking_id": BOOKING,
        "owner": "aster-stream-a",
        "workload": "sa3-evidence-matrix-candidate-j-quality-v1",
        "start_epoch": 1793898960, "end_epoch": 1793902560,
        "state": "complete", "created_epoch": 1793891000,
        "restore_buffer_seconds": 900,
        "claimant": "lh-0123456789abcdef0123",
        "claimed_epoch": 1793898960, "finished_epoch": 1793899200,
        "result_code": "COMPLETE",
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

    def test_retained_byte_and_summary_bounds_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "canonical"):
            reconcile(BOOKING, canonical(terminal()), self.packet, self.keys,
                      canonical(self.result) + b"\n")
        value = copy.deepcopy(self.result)
        value["predictions"][0]["summary"] = "x" * 3001
        with self.assertRaisesRegex(ValueError, "prediction"):
            reconcile(BOOKING, canonical(terminal()), self.packet, self.keys,
                      canonical(value))
        with self.assertRaisesRegex(ValueError, "bounded size"):
            reconcile(BOOKING, canonical(terminal()), self.packet, self.keys,
                      b" " * 524289)

    def test_authoritative_booking_and_owner_receipt_are_cross_bound(self):
        value = terminal()
        value["started_epoch"] = 1793898959
        value["finished_epoch"] = 1793899199
        raw = canonical(self.result)
        receipt = {
            "effects": "sa3-evidence-matrix-candidate-j-quality-complete",
            "production_restored": True,
            "receipt": {"exit_status": 0,
                        "profile": "sa3-evidence-matrix-candidate-j-quality-v1",
                        "request_count": 20, "model_request_count": 14,
                        "case_count": 20,
                        "prediction_sha256": __import__("hashlib").sha256(raw).hexdigest(),
                        "error_count": 0},
        }
        summary = reconcile_evidence(
            BOOKING, canonical(booking()), canonical(value), canonical(receipt),
            self.packet, self.keys, raw)
        self.assertEqual(64, len(summary["booking_sha256"]))
        changed = booking(); changed["state"] = "failed"
        with self.assertRaisesRegex(ValueError, "booking"):
            reconcile_evidence(BOOKING, canonical(changed), canonical(value),
                               canonical(receipt), self.packet, self.keys, raw)
        changed_receipt = copy.deepcopy(receipt)
        changed_receipt["receipt"]["prediction_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "receipt"):
            reconcile_evidence(BOOKING, canonical(booking()), canonical(value),
                               canonical(changed_receipt), self.packet, self.keys, raw)


if __name__ == "__main__":
    unittest.main()
