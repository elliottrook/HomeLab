import os
import tempfile
import unittest
from pathlib import Path

from sa3_expanded_quality_transaction import (PACKET_SHA256, REQUEST_COUNT,
    TransactionError, content_free_receipt, execute, inactive_workload_runner,
    retain_result, validate_result)


def result():
    return {"schema_version": 1,
            "packet_id": "sa3-expanded-source-quality-v1",
            "packet_sha256": PACKET_SHA256, "model": "aster-qwen3.5-9b",
            "request_count": REQUEST_COUNT, "retry_count": 0,
            "predictions": [{"id": f"case-{i}", "outcome": "clarify",
                             "checks": [], "summary": "bounded",
                             "effects": [], "finish_reason": "stop",
                             "latency_seconds": 0.1} for i in range(REQUEST_COUNT)],
            "errors": []}


class Controller:
    def __init__(self): self.events = []
    def begin(self, preflight, *, lab_seconds):
        self.events.append(("begin", lab_seconds)); return "plan"
    def restore(self, plan, *, now_epoch, owner_present):
        self.events.append(("restore", plan, owner_present))


class TransactionTests(unittest.TestCase):
    def test_result_validation_and_content_free_receipt(self):
        metadata = validate_result(result())
        receipt = content_free_receipt(metadata)
        self.assertEqual(receipt["receipt"]["request_count"], 20)
        self.assertNotIn("predictions", receipt)
        self.assertNotIn("summary", receipt)

    def test_count_and_retry_drift_fail_closed(self):
        value = result(); value["request_count"] = 19
        with self.assertRaisesRegex(TransactionError, "COUNT"):
            validate_result(value)
        value = result(); value["retry_count"] = 1
        with self.assertRaisesRegex(TransactionError, "COUNT_OR_RETRY"):
            validate_result(value)

    def test_invalid_prediction_requires_matching_error(self):
        value = result(); value["predictions"][0]["outcome"] = "invalid"
        with self.assertRaisesRegex(TransactionError, "ERROR_PROJECTION"):
            validate_result(value)

    def test_retention_is_root_only_and_digest_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); os.chmod(root, 0o700)
            retained = retain_result(root, result(), expected_uid=os.geteuid())
            self.assertEqual((root / "sa3-expanded-source-quality-v1-result.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(retained["result_bytes"], (root / "sa3-expanded-source-quality-v1-result.json").stat().st_size)

    def test_success_restores_after_retention(self):
        controller = Controller(); events = []
        preflight = type("Preflight", (), {"lab_end_epoch": 5000})()
        with tempfile.TemporaryDirectory() as tmp:
            receipt = execute(preflight=preflight, controller=controller,
                              workload_runner=lambda **kwargs: (events.append("workload") or result()),
                              retain_root=Path(tmp), expected_uid=os.geteuid())
        self.assertEqual(events, ["workload"])
        self.assertEqual(controller.events, [("begin", 2700), ("restore", "plan", True)])
        self.assertEqual(receipt["receipt"]["profile"], "sa3-expanded-source-quality-v1")

    def test_failure_cleans_up_and_restores(self):
        controller = Controller(); events = []
        preflight = type("Preflight", (), {"lab_end_epoch": 5000})()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "workload failed"):
                execute(preflight=preflight, controller=controller,
                        workload_runner=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("workload failed")),
                        retain_root=Path(tmp), cleanup=lambda: events.append("cleanup"),
                        expected_uid=os.geteuid())
        self.assertEqual(events, ["cleanup"])
        self.assertEqual(controller.events, [("begin", 2700), ("restore", "plan", True)])

    def test_inactive_runner_never_returns_a_result(self):
        with self.assertRaisesRegex(TransactionError, "LISTENER_TARGET_INACTIVE"):
            inactive_workload_runner()


if __name__ == "__main__":
    unittest.main()
