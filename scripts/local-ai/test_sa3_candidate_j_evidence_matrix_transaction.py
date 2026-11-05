import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import sa3_candidate_j_evidence_matrix_transaction as transaction


def valid_result():
    rows = []
    for index in range(6):
        requested = index < 2
        rows.append({
            "id": f"public-{index}",
            "outcome": "plan" if requested else "clarify",
            "checks": ["doctor_status"],
            "summary": "Current bounded synthetic evidence; no action performed.",
            "effects": [], "authority": "none",
            "prose_source": "deterministic-evidence-matrix",
            "model": "accepted-local-model", "model_requested": requested,
            "finish_reason": "stop" if requested else "deterministic",
            "latency_seconds": 0.1, "error_class": None,
        })
    return {
        "schema": "aster-sa3-evidence-matrix-public-result.v1",
        "candidate_alias": "candidate-j", "model": "accepted-local-model",
        "fixture_sha256": transaction.FIXTURE_SEMANTIC_SHA256,
        "case_count": 6, "model_request_count": 2, "retry_count": 0,
        "predictions": rows, "errors": [], "authority": "none",
        "automatic_routing": "off",
    }


class Controller:
    def __init__(self):
        self.restored = 0

    def begin(self, preflight, lab_seconds):
        if lab_seconds != 1800:
            raise AssertionError()
        return "plan"

    def restore(self, plan, now_epoch, owner_present):
        self.restored += 1


class CandidateJEvidenceMatrixTransactionTests(unittest.TestCase):
    def test_file_custody_and_semantic_result_digests_are_distinct(self):
        self.assertNotEqual(transaction.FIXTURE_FILE_SHA256,
                            transaction.FIXTURE_SEMANTIC_SHA256)
        value = valid_result()
        value["fixture_sha256"] = transaction.FIXTURE_FILE_SHA256
        with self.assertRaisesRegex(transaction.TransactionError, "IDENTITY"):
            transaction.validate_result(value)

    def test_valid_result_binds_two_requests_and_no_errors(self):
        metadata = transaction.validate_result(valid_result())
        self.assertEqual(2, metadata["model_request_count"])
        self.assertEqual(0, metadata["error_count"])

    def test_any_error_fails_closed(self):
        value = valid_result()
        value["errors"] = [{"id": "public-0", "class": "TimeoutError"}]
        with self.assertRaisesRegex(transaction.TransactionError,
                                    "COUNT_OR_ERROR"):
            transaction.validate_result(value)

    def test_control_or_request_count_drift_fails_closed(self):
        value = valid_result()
        value["automatic_routing"] = "on"
        with self.assertRaisesRegex(transaction.TransactionError, "IDENTITY"):
            transaction.validate_result(value)
        value = valid_result()
        value["predictions"][0]["effects"] = ["restart"]
        with self.assertRaisesRegex(transaction.TransactionError, "PREDICTION"):
            transaction.validate_result(value)
        value = valid_result()
        value["predictions"][2]["model_requested"] = True
        value["predictions"][2]["finish_reason"] = "stop"
        with self.assertRaisesRegex(transaction.TransactionError,
                                    "REQUEST_COUNT"):
            transaction.validate_result(value)

    def test_success_retains_result_then_restores(self):
        controller = Controller()
        cleanup = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            os.chmod(root, 0o700)
            receipt = transaction.execute(
                preflight=SimpleNamespace(lab_end_epoch=9999999999),
                controller=controller,
                workload_runner=lambda **_kwargs: valid_result(),
                retain_root=root, cleanup=lambda: cleanup.append(True),
                expected_uid=os.geteuid())
            self.assertTrue((root / transaction.RESULT_FILENAME).is_file())
        self.assertEqual(1, controller.restored)
        self.assertEqual([True], cleanup)
        self.assertEqual(6, receipt["receipt"]["request_count"])
        self.assertEqual(2, receipt["receipt"]["model_request_count"])
        self.assertTrue(receipt["production_restored"])

    def test_failure_cleans_and_restores(self):
        controller = Controller()
        cleanup = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            os.chmod(root, 0o700)
            with self.assertRaisesRegex(RuntimeError, "failed"):
                transaction.execute(
                    preflight=SimpleNamespace(lab_end_epoch=9999999999),
                    controller=controller,
                    workload_runner=lambda **_kwargs: (_ for _ in ()).throw(
                        RuntimeError("failed")),
                    retain_root=root, cleanup=lambda: cleanup.append(True),
                    expected_uid=os.geteuid())
        self.assertEqual(1, controller.restored)
        self.assertEqual([True], cleanup)


if __name__ == "__main__":
    unittest.main()
