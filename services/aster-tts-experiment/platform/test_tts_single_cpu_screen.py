from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).parent))

import tts_single_cpu_screen_adapter as adapter
import tts_single_cpu_screen_transaction as transaction


def valid_result(workload_id: str) -> dict[str, object]:
    candidate_id, model_hash = transaction.PROFILES[workload_id]
    return {
        "schema": "aster-tts-single-cpu-screen-result.v1", "workload_id": workload_id,
        "lease_id": "test-lease", "generation": 1, "candidate_id": candidate_id,
        "model_sha256": model_hash, **transaction.EXACT_PINS,
        "backend": "CPU", "seed": 20261104, "gpu_used": False, "network_used": False,
        "production_route_changed": False, "render_seconds": 100.0,
        "real_time_factor": 1.0, "audio_seconds": 100.0, "words_per_minute": 120.0,
        "wav_bytes": 1000, "wav_sha256": "e" * 64,
    }


class RejectingController:
    def begin(self, _preflight, *, lab_seconds):
        raise RuntimeError(f"rejected:{lab_seconds}")


class SingleCpuScreenTests(unittest.TestCase):
    def test_both_exact_profiles_are_accepted(self):
        for workload_id in transaction.PROFILES:
            with self.subTest(workload_id=workload_id):
                metadata = transaction.validate_result(valid_result(workload_id),
                                                       workload_id=workload_id)
                self.assertEqual(metadata["candidate_count"], 1)
                self.assertEqual(metadata["candidate_id"], transaction.PROFILES[workload_id][0])

    def test_wrong_profile_pin_and_gpu_are_rejected(self):
        first, second = transaction.PROFILES
        value = valid_result(first)
        value["candidate_id"] = transaction.PROFILES[second][0]
        with self.assertRaises(transaction.TransactionError):
            transaction.validate_result(value, workload_id=first)
        value = valid_result(first); value["binary_sha256"] = "f" * 64
        with self.assertRaises(transaction.TransactionError):
            transaction.validate_result(value, workload_id=first)
        value = valid_result(first); value["gpu_used"] = True
        with self.assertRaises(transaction.TransactionError):
            transaction.validate_result(value, workload_id=first)

    def test_begin_rejection_does_not_call_cleanup_or_runner(self):
        calls = []
        with tempfile.TemporaryDirectory() as root:
            Path(root).chmod(0o700)
            with self.assertRaisesRegex(RuntimeError, "rejected:2400"):
                transaction.execute(
                    workload_id=next(iter(transaction.PROFILES)), preflight=object(),
                    controller=RejectingController(),
                    workload_runner=lambda **_kwargs: calls.append("runner"),
                    retain_root=Path(root), cleanup=lambda: calls.append("cleanup"),
                    expected_uid=Path(root).stat().st_uid,
                )
        self.assertEqual(calls, [])

    def test_adapter_fixes_profile_and_uses_safe_budget(self):
        for workload_id in transaction.PROFILES:
            command = adapter.guest_command(workload_id, "test-lease", 1)
            self.assertEqual(command[:4], ("pct", "exec", "110", "--"))
            self.assertEqual(command[command.index("--workload-id") + 1], workload_id)
            self.assertIn(f"--property=RuntimeMaxSec={transaction.DEADLINE_SECONDS}", command)
        self.assertEqual(transaction.DEADLINE_SECONDS, 2400)

    def test_boolean_generation_and_bad_lease_are_rejected(self):
        workload_id = next(iter(transaction.PROFILES))
        with self.assertRaises(adapter.AdapterError):
            adapter.unit_name(workload_id, "test-lease", True)
        value = valid_result(workload_id); value["lease_id"] = "bad lease"
        with self.assertRaises(transaction.TransactionError):
            transaction.validate_result(value, workload_id=workload_id)


if __name__ == "__main__":
    unittest.main()
