import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v1 import run
from sa3_evidence_envelope_reconciliation_v1 import reconcile


PACKET = json.loads(
    Path(__file__).with_name("sa3-evidence-envelope-quality-v1.json").read_text()
)
BOOKING = "aster-stream-a-sa3-envelope-20261104-test"


def response(_payload):
    return {"choices": [{
        "message": {"role": "assistant", "content": json.dumps({
            "diagnosis": "The visible evidence supports a bounded statement.",
            "verification": "Refresh the registered evidence before cause.",
        })},
        "finish_reason": "stop",
    }]}


def result():
    return run(PACKET, response, model="hidden-model")


def terminal():
    return {
        "schema": "aster-lab-hours-booked-result.v1",
        "state": "complete", "booking_id": BOOKING,
        "started_epoch": 100, "finished_epoch": 200,
        "request_count": 20,
        "workload": "sa3-evidence-envelope-quality-v1",
        "production_restored": True,
    }


class EvidenceEnvelopeReconciliationTests(unittest.TestCase):
    def test_complete_transaction_builds_blind_pending_packet(self):
        summary, packet = reconcile(BOOKING, terminal(), PACKET, result())
        self.assertEqual("pending-independent-review", summary["quality_decision"])
        self.assertTrue(summary["production_restored"])
        self.assertFalse(summary["model_identity_disclosed"])
        self.assertNotIn("hidden-model", json.dumps(packet))

    def test_no_go_restoration_or_booking_drift_fails_closed(self):
        variants = []
        for field, changed in (
                ("state", "no_go"),
                ("production_restored", False),
                ("request_count", 14),
                ("booking_id", "other-booking")):
            value = copy.deepcopy(terminal())
            value[field] = changed
            variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile(BOOKING, value, PACKET, result())

    def test_result_error_fails_before_review_packet(self):
        value = result()
        value["errors"] = [{"id": value["predictions"][0]["id"],
                            "error_class": "TimeoutError"}]
        with self.assertRaises(ValueError):
            reconcile(BOOKING, terminal(), PACKET, value)


if __name__ == "__main__":
    unittest.main()

