import sys
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import b60_musetalk_xpu_adapter as adapter
import b60_musetalk_xpu_transaction as transaction
import b60_musetalk_openvino_adapter as ov_adapter
import b60_musetalk_openvino_transaction as ov_transaction


class B60MuseTalkXPUTests(unittest.TestCase):
    def test_manifest_matches_session_v2_attempt_contract(self):
        manifest = json.loads((HERE / "b60_musetalk_xpu_manifest.json").read_text())
        controls = manifest["controls"]
        self.assertEqual(manifest["status"], "scheduled-session-v2")
        self.assertIs(controls["retryable_session"], True)
        self.assertEqual(controls["retry_policy"], "remaining-time-and-restoration")
        self.assertIsNone(controls["maximum_attempts"])
        self.assertEqual(controls["attempt_deadline_seconds"], 1200)
        self.assertEqual(transaction.DEADLINE_SECONDS, 1200)

    def test_transient_unit_enforces_isolation_and_memory_controls(self):
        command = adapter.guest_command("lease-1", 1)
        self.assertIn("--property=PrivateNetwork=yes", command)
        self.assertIn("--property=MemoryMax=12G", command)
        self.assertIn("--property=MemorySwapMax=0", command)

    def test_intel_compiler_library_path_is_present(self):
        self.assertIn("/runtime/root/usr/local/lib", adapter.LIBRARY_PATH)

    def test_native_failure_reports_last_stage(self):
        raw = b'{"stage":"MOVE_MODELS_TO_XPU"}\nFatal Python error: Segmentation fault\n'
        self.assertEqual(adapter.guest_failure_detail(raw),
                         "NATIVE_CRASH_AFTER_MOVE_MODELS_TO_XPU")

    def test_fixed_b60_identity_avoids_crashing_torch_name_query(self):
        source = (HERE / "b60_musetalk_xpu_guest.py").read_text()
        self.assertNotIn("get_device_name", source)
        self.assertIn('EXPECTED_PCI_ID = ("0x8086", "0xe211")', source)

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

    def test_openvino_command_keeps_torch_on_cpu_and_gpu_private(self):
        command = ov_adapter.guest_command("lease-1", 1)
        self.assertIn("MUSETALK_DEVICE=cpu", command)
        self.assertIn("--property=PrivateNetwork=yes", command)
        self.assertIn("--property=MemoryMax=12G", command)
        self.assertIn("--property=MemorySwapMax=0", command)
        self.assertIn(f"LD_LIBRARY_PATH={ov_adapter.LD_LIBRARY_PATH}", command)
        self.assertIn(f"OCL_ICD_FILENAMES={ov_adapter.OCL_ICD_FILENAMES}", command)

    def test_openvino_result_contract(self):
        value = {
            "schema": "aster-news-video-musetalk-openvino-result.v1",
            "workload_id": ov_transaction.WORKLOAD_ID,
            "lease_id": "lease-1", "generation": 1,
            "source_commit": ov_transaction.SOURCE_COMMIT,
            "source_tree": ov_transaction.SOURCE_TREE,
            "openvino_version": ov_transaction.OPENVINO_VERSION, "backend": "openvino:GPU",
            "device_name": "Intel Arc Pro B60", "ir_xml_sha256": "a" * 64,
            "ir_bin_sha256": "b" * 64, "fps": 25, "batch_size": 4,
            "frame_count": 42, "render_seconds": 12.5,
            "output_path": "/opt/aster-news-video-xpu/outputs/test.mp4",
            "output_bytes": 4096, "output_sha256": "c" * 64,
            "network_used_during_render": False, "production_route_changed": False,
        }
        self.assertEqual(ov_transaction.validate_result(value)["frame_count"], 42)


if __name__ == "__main__":
    unittest.main()
