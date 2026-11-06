import sys
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import b60_musetalk_xpu_adapter as adapter
import b60_musetalk_xpu_transaction as transaction


class B60MuseTalkXPUTests(unittest.TestCase):
    def test_manifest_matches_session_v2_attempt_contract(self):
        manifest = json.loads((HERE / "b60_musetalk_xpu_manifest.json").read_text())
        controls = manifest["controls"]
        self.assertEqual(manifest["status"], "scheduled-session-v2")
        self.assertIs(controls["retryable_session"], True)
        self.assertEqual(controls["maximum_attempts"], 3)
        self.assertEqual(controls["attempt_deadline_seconds"], 1200)
        self.assertEqual(transaction.DEADLINE_SECONDS, 1200)

    def test_transient_unit_enforces_isolation_and_memory_controls(self):
        command = adapter.guest_command("lease-1", 1)
        self.assertIn("--property=PrivateNetwork=yes", command)
        self.assertIn("--property=MemoryMax=12G", command)
        self.assertIn("--property=MemorySwapMax=0", command)

    def test_intel_compiler_library_path_is_present(self):
        self.assertIn("/runtime/root/usr/local/lib", adapter.LIBRARY_PATH)

    def test_fixed_result_contract(self):
        value = {
            "schema": "aster-news-video-musetalk-xpu-result.v1",
            "workload_id": transaction.WORKLOAD_ID,
            "lease_id": "lease-1",
            "generation": 1,
            "source_commit": transaction.SOURCE_COMMIT,
            "source_tree": transaction.SOURCE_TREE,
            "torch_version": "2.14.1+xpu",
            "device": "xpu:0",
            "device_name": "Intel BMG G21",
            "fps": 25,
            "batch_size": 4,
            "frame_count": 42,
            "render_seconds": 12.5,
            "xpu_max_memory_allocated": 1024,
            "output_path": "/opt/aster-news-video-xpu/outputs/test.mp4",
            "output_bytes": 4096,
            "output_sha256": "a" * 64,
            "network_used_during_render": False,
            "production_route_changed": False,
        }
        result = transaction.validate_result(value)
        self.assertEqual(result["frame_count"], 42)


if __name__ == "__main__":
    unittest.main()
