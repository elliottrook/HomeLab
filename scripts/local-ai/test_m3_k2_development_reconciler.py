import copy
import unittest

import m3_k2_development_reconciler as reconcile
from test_m3_k2_development_transaction import valid_result


def evidence(passed=True):
    result = valid_result(passed)
    metadata = reconcile.validate_result(result)
    booking = {
        "schema": "aster-lab-hours-reservation.v1",
        "booking_id": reconcile.BOOKING_ID,
        "owner": "aster-stream-a",
        "workload": reconcile.WORKLOAD_ID,
        "start_epoch": 1,
        "end_epoch": 2,
        "state": "complete",
        "created_epoch": 0,
        "restore_buffer_seconds": 900,
        "promotable": False,
        "claimant": "lh-example",
        "claimed_epoch": 1,
        "finished_epoch": 2,
        "result_code": "COMPLETE",
    }
    terminal = {
        "schema": "aster-lab-hours-booked-result.v1",
        "state": "complete",
        "booking_id": reconcile.BOOKING_ID,
        "started_epoch": 1,
        "finished_epoch": 2,
        "request_count": 192,
        "workload": reconcile.WORKLOAD_ID,
        "production_restored": True,
    }
    receipt = {
        "effects": "m3-k2-development-complete",
        "production_restored": True,
        "receipt": {
            "exit_status": 0,
            "profile": reconcile.WORKLOAD_ID,
            "request_count": 192,
            "model_request_count": 192,
            "case_count": 192,
            "prediction_sha256": metadata["result_sha256"],
            "development_gate_passed": passed,
            "status": "pass" if passed else "reject",
            "error_count": 0,
        },
    }
    return booking, terminal, receipt, result


class K2ReconciliationTests(unittest.TestCase):
    def test_accepts_pass_and_reject_as_complete_development_outcomes(self):
        for passed in (True, False):
            value = reconcile.reconcile(*(), **dict(zip(
                ("booking", "terminal", "receipt", "result"), evidence(passed))))
            self.assertEqual("complete", value["state"])
            self.assertEqual(passed, value["development_gate_passed"])
            self.assertTrue(value["production_restored"])

    def test_rejects_receipt_result_digest_drift(self):
        booking, terminal, receipt, result = evidence()
        receipt = copy.deepcopy(receipt)
        receipt["receipt"]["prediction_sha256"] = "0" * 64
        with self.assertRaisesRegex(reconcile.ReconciliationError, "MISMATCH"):
            reconcile.reconcile(booking=booking, terminal=terminal,
                                receipt=receipt, result=result)

    def test_rejects_failed_restoration_or_nonterminal_booking(self):
        booking, terminal, receipt, result = evidence()
        terminal = copy.deepcopy(terminal)
        terminal["production_restored"] = False
        with self.assertRaises(reconcile.ReconciliationError):
            reconcile.reconcile(booking=booking, terminal=terminal,
                                receipt=receipt, result=result)
        booking["state"] = "claimed"
        with self.assertRaises(reconcile.ReconciliationError):
            reconcile.reconcile(booking=booking, terminal=evidence()[1],
                                receipt=receipt, result=result)

    def test_duplicate_json_keys_fail_closed(self):
        with self.assertRaisesRegex(reconcile.ReconciliationError, "DUPLICATE"):
            reconcile.decode(b'{"state":"complete","state":"failed"}',
                             maximum=1024)


if __name__ == "__main__":
    unittest.main()
