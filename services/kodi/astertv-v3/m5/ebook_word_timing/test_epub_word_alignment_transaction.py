import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "epub_word_alignment_transaction", HERE / "epub_word_alignment_transaction.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def result(passed=True):
    value = {
        "schema": "astertv-ebook-word-alignment-benchmark.v1",
        "workload_id": MODULE.WORKLOAD_ID,
        "input_manifest_sha256": "1" * 64,
        "input_audio_sha256": "2" * 64,
        "source_prefix_sha256": "3" * 64,
        "model_sha256": "4" * 64,
        "prefix_cues": 10,
        "network_used": False,
        "text_exported": False,
        "timestamps_inferred": False,
        "passed": passed,
        "failure_code": "NONE" if passed else "alignment-text-mismatch",
        "measured_word_count": 100,
        "elapsed_seconds": 12.5,
        "detected_language": "en",
    }
    if passed:
        value["word_count"] = 100
    return value


class Controller:
    def __init__(self):
        self.events = []

    def begin(self, preflight, *, lab_seconds):
        self.events.append(("begin", lab_seconds))
        return "plan"

    def restore(self, plan, *, now_epoch, owner_present):
        self.events.append(("restore", plan, owner_present))


class TransactionTests(unittest.TestCase):
    def test_accepts_negative_benchmark_without_invented_timing(self):
        metadata = MODULE.validate_result(result(False))
        self.assertFalse(metadata["passed"])
        self.assertEqual(metadata["failure_code"], "alignment-text-mismatch")

    def test_rejects_inferred_timing(self):
        value = result()
        value["timestamps_inferred"] = True
        with self.assertRaisesRegex(MODULE.TransactionError, "IDENTITY"):
            MODULE.validate_result(value)

    def test_transaction_restores_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            controller = Controller()
            receipt = MODULE.execute(
                preflight=types.SimpleNamespace(lab_end_epoch=1000),
                controller=controller,
                workload_runner=lambda **kwargs: result(),
                retain_root=root,
                now=lambda: 900,
                expected_uid=os.geteuid(),
            )
            self.assertEqual(receipt["effects"], "ebook-word-alignment-benchmark-complete")
            self.assertEqual(controller.events, [("begin", 900), ("restore", "plan", True)])
            retained = root / MODULE.RESULT_FILENAME
            self.assertEqual(retained.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(retained.read_text()), result())

    def test_transaction_restores_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o700)
            controller = Controller()
            with self.assertRaisesRegex(RuntimeError, "failed"):
                MODULE.execute(
                    preflight=types.SimpleNamespace(lab_end_epoch=1000),
                    controller=controller,
                    workload_runner=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("failed")),
                    retain_root=root,
                    now=lambda: 900,
                    expected_uid=os.geteuid(),
                )
            self.assertEqual(controller.events, [("begin", 900), ("restore", "plan", True)])


if __name__ == "__main__":
    unittest.main()
