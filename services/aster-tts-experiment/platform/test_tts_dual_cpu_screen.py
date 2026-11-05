from __future__ import annotations

import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).parent))

import tts_dual_cpu_screen_adapter as adapter
import tts_dual_cpu_screen_transaction as transaction


def valid_result() -> dict[str, object]:
    value = {
        "schema": "aster-tts-dual-cpu-screen-result.v1",
        "workload_id": transaction.WORKLOAD_ID,
        "lease_id": "test-lease",
        "generation": 1,
        "binary_sha256": "a" * 64,
        "codec_sha256": "b" * 64,
        "reference_wav_sha256": "c" * 64,
        "input_sha256": "d" * 64,
        "candidate_count": 2,
        "gpu_used": False,
        "network_used": False,
        "production_route_changed": False,
        "results": [],
    }
    for index, (identifier, model_hash) in enumerate(transaction.CANDIDATES.items()):
        value["results"].append({
            "candidate_id": identifier, "model_sha256": model_hash, "backend": "CPU",
            "seed": 20261104, "input_sha256": "d" * 64, "render_seconds": 100.0,
            "real_time_factor": 1.0, "audio_seconds": 100.0, "words_per_minute": 120.0,
            "wav_bytes": 1000, "wav_sha256": str(index) * 64,
        })
    return value


class DualCpuScreenTests(unittest.TestCase):
    def test_exact_two_candidate_result_is_accepted(self):
        self.assertEqual(transaction.validate_result(valid_result())["passed_count"], 2)

    def test_gpu_or_candidate_drift_is_rejected(self):
        value = valid_result()
        value["gpu_used"] = True
        with self.assertRaises(transaction.TransactionError):
            transaction.validate_result(value)

    def test_adapter_is_fixed_to_cpu_guest_and_bounded_unit(self):
        command = adapter.guest_command("test-lease", 1)
        self.assertEqual(command[:4], ("pct", "exec", "110", "--"))
        self.assertIn(adapter.GUEST_SCRIPT, command)
        self.assertIn(f"--property=RuntimeMaxSec={transaction.DEADLINE_SECONDS}", command)
        self.assertEqual(transaction.DEADLINE_SECONDS, 4500)


if __name__ == "__main__":
    unittest.main()
