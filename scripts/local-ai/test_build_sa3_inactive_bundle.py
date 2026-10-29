import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest

import build_sa3_inactive_bundle as builder


class BundleTests(unittest.TestCase):
    def test_bundle_is_deterministic_selected_and_custodied(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundles"
            result = builder.build(output, expected_uid=os.geteuid())
            self.assertIsNone(result["stage"])
            archive = Path(result["archive"])
            sidecar = Path(result["sidecar"])
            self.assertTrue(archive.exists())
            self.assertTrue(sidecar.exists())
            self.assertEqual(output.stat().st_uid, os.geteuid())
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            self.assertEqual(archive.stat().st_mode & 0o777, 0o600)
            self.assertEqual(sidecar.stat().st_mode & 0o777, 0o600)
            with tarfile.open(archive, "r:gz") as tar:
                names = sorted(tar.getnames())
                self.assertEqual(names, sorted([
                    "bundle-manifest.json",
                    "services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json",
                    "scripts/local-ai/sa3_expanded_quality_transaction.py",
                    "scripts/local-ai/sa3_inactive_install.py",
                    "scripts/local-ai/sa3_listener_adapter.py",
                    "services/aster-agent/evals/sa3-expanded-source-quality-v1.json",
                    "services/aster-agent/evals/sa3_expanded_quality_packet.py",
                    "services/aster-agent/evals/sa3_expanded_quality_runner.py",
                    "services/aster-agent/evals/sa3_fair_scorer.py",
                    "scripts/local-ai/aster_llama_sa3_guest_wrapper.py",
                ]))

    def test_bundle_retention_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "bundles"
            result = builder.build(output, expected_uid=os.geteuid(), retain_stage=True)
            stage = Path(result["stage"])
            self.assertTrue(stage.is_dir())
            manifest = json.loads((stage / "bundle-manifest.json").read_text())
            self.assertEqual(manifest["packet_sha256"], builder.PACKET_SHA256)
            self.assertEqual(manifest["source_commits"]["stream_a"], builder.STREAM_COMMIT)
            paths = {item["path"] for item in manifest["files"]}
            self.assertEqual(len(paths), result["source_files"])
            self.assertFalse(any("keys-v1" in path or "review" in path for path in paths))
            packet = stage / "services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json"
            self.assertEqual(packet.stat().st_mode & 0o777, 0o600)
            for item in manifest["files"]:
                path = stage / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(path.stat().st_mode & 0o777, int(item["mode"], 8))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])


if __name__ == "__main__":
    unittest.main()
