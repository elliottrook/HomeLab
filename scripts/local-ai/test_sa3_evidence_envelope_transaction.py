import copy
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import sa3_evidence_envelope_transaction as transaction


def valid_result():
    rows = []
    for index in range(20):
        deterministic = index >= 14
        rows.append({
            "id": f"case-{index}", "outcome": "clarify" if deterministic else "plan",
            "checks": [] if deterministic else ["doctor_status"],
            "summary": "Bounded synthetic evidence only.", "effects": [],
            "authority": "none",
            "prose_source": "deterministic-fallback" if deterministic else "bounded-model-draft",
            "model": "accepted-local-model",
            "finish_reason": "deterministic" if deterministic else "stop",
            "latency_seconds": 0.1, "error_class": None,
        })
    return {
        "schema": "aster-sa3-evidence-envelope-result.v1",
        "packet_id": transaction.WORKLOAD_ID,
        "packet_sha256": transaction.PACKET_SHA256,
        "candidate_alias": "candidate-g", "model": "accepted-local-model",
        "case_count": 20, "model_request_count": 14, "retry_count": 0,
        "predictions": rows, "errors": [], "authority": "none",
        "automatic_routing": "off",
    }


class Controller:
    def __init__(self): self.restored = 0
    def begin(self, preflight, lab_seconds):
        if lab_seconds != 2700: raise AssertionError()
        return "plan"
    def restore(self, plan, now_epoch, owner_present):
        self.restored += 1


class EvidenceEnvelopeTransactionTests(unittest.TestCase):
    def test_valid_result_binds_fourteen_requests_and_no_errors(self):
        metadata = transaction.validate_result(valid_result())
        self.assertEqual(14, metadata["model_request_count"])
        self.assertEqual(0, metadata["error_count"])

    def test_any_error_fails_closed(self):
        value = valid_result()
        value["errors"] = [{"id": "case-0", "error_class": "TimeoutError"}]
        with self.assertRaisesRegex(transaction.TransactionError, "COUNT_OR_ERROR"):
            transaction.validate_result(value)

    def test_control_or_count_drift_fails_closed(self):
        value = valid_result(); value["automatic_routing"] = "on"
        with self.assertRaisesRegex(transaction.TransactionError, "IDENTITY"):
            transaction.validate_result(value)
        value = valid_result(); value["predictions"][0]["effects"] = ["restart"]
        with self.assertRaisesRegex(transaction.TransactionError, "PREDICTION"):
            transaction.validate_result(value)

    def test_success_retains_result_then_restores(self):
        controller = Controller(); cleanup = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); os.chmod(root, 0o700)
            receipt = transaction.execute(
                preflight=SimpleNamespace(lab_end_epoch=9999999999),
                controller=controller, workload_runner=lambda **_kwargs: valid_result(),
                retain_root=root, cleanup=lambda: cleanup.append(True),
                expected_uid=os.geteuid())
            self.assertTrue((root / transaction.RESULT_FILENAME).is_file())
        self.assertEqual(1, controller.restored)
        self.assertEqual([True], cleanup)
        self.assertEqual(20, receipt["receipt"]["request_count"])
        self.assertEqual(14, receipt["receipt"]["model_request_count"])
        self.assertTrue(receipt["production_restored"])

    def test_failure_cleans_and_restores(self):
        controller = Controller(); cleanup = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); os.chmod(root, 0o700)
            with self.assertRaisesRegex(RuntimeError, "failed"):
                transaction.execute(
                    preflight=SimpleNamespace(lab_end_epoch=9999999999),
                    controller=controller,
                    workload_runner=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("failed")),
                    retain_root=root, cleanup=lambda: cleanup.append(True),
                    expected_uid=os.geteuid())
        self.assertEqual(1, controller.restored)
        self.assertEqual([True], cleanup)


if __name__ == "__main__":
    unittest.main()
