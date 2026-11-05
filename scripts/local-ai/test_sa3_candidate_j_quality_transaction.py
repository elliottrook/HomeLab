import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import sa3_candidate_j_quality_transaction as transaction


def valid_result():
    rows = []
    for index in range(20):
        requested = index < 14
        rows.append({"id": f"quality-{index}",
            "outcome": "plan" if requested else "clarify",
            "checks": ["dependency_state"],
            "summary": "Current bounded evidence; no action has been performed.",
            "effects": [], "authority": "none",
            "prose_source": "deterministic-evidence-matrix",
            "model": "accepted-local-model", "model_requested": requested,
            "finish_reason": "stop" if requested else "deterministic",
            "latency_seconds": 0.1, "error_class": None})
    return {"schema": "aster-sa3-evidence-matrix-quality-result.v1",
        "candidate_alias": "candidate-j", "model": "accepted-local-model",
        "packet_id": transaction.WORKLOAD_ID,
        "packet_sha256": transaction.PACKET_SHA256,
        "case_count": 20, "model_request_count": 14, "retry_count": 0,
        "predictions": rows, "errors": [], "authority": "none",
        "automatic_routing": "off"}


class Controller:
    def __init__(self): self.restored = 0
    def begin(self, _preflight, lab_seconds):
        if lab_seconds != 2700: raise AssertionError()
        return "plan"
    def restore(self, _plan, now_epoch, owner_present): self.restored += 1


class CandidateJQualityTransactionTests(unittest.TestCase):
    def test_exact_result_passes(self):
        metadata = transaction.validate_result(valid_result())
        self.assertEqual(20, metadata["case_count"])
        self.assertEqual(14, metadata["model_request_count"])

    def test_identity_error_and_request_drift_fail(self):
        value = valid_result(); value["packet_sha256"] = "0" * 64
        with self.assertRaisesRegex(transaction.TransactionError, "IDENTITY"):
            transaction.validate_result(value)
        value = valid_result(); value["predictions"][14]["model_requested"] = True
        value["predictions"][14]["finish_reason"] = "stop"
        with self.assertRaisesRegex(transaction.TransactionError, "REQUEST_COUNT"):
            transaction.validate_result(value)
        value = valid_result(); value["errors"] = [{"id": "x", "class": "TimeoutError"}]
        with self.assertRaisesRegex(transaction.TransactionError, "COUNT_OR_ERROR"):
            transaction.validate_result(value)

    def test_success_retains_then_restores(self):
        controller = Controller(); cleanup = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); os.chmod(root, 0o700)
            receipt = transaction.execute(
                preflight=SimpleNamespace(lab_end_epoch=9999999999),
                controller=controller, workload_runner=lambda **_kw: valid_result(),
                retain_root=root, cleanup=lambda: cleanup.append(True),
                expected_uid=os.geteuid())
            self.assertTrue((root / transaction.RESULT_FILENAME).is_file())
        self.assertEqual(1, controller.restored); self.assertEqual([True], cleanup)
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
                    workload_runner=lambda **_kw: (_ for _ in ()).throw(RuntimeError("failed")),
                    retain_root=root, cleanup=lambda: cleanup.append(True),
                    expected_uid=os.geteuid())
        self.assertEqual(1, controller.restored); self.assertEqual([True], cleanup)


if __name__ == "__main__": unittest.main()
