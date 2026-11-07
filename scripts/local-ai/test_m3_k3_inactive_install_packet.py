import hashlib
import tarfile
from pathlib import Path
import tempfile
import unittest

import build_m3_k3_development_inactive_bundle as builder
import m3_k3_development_inactive_install as installer


class K3InactiveInstallPacketTests(unittest.TestCase):
    def test_fixed_baseline_and_absent_targets(self):
        self.assertEqual(
            "b7d5157b21366898e434fd2fc7840bed3f1643d96b4316df360a5dcecaf27045",
            installer.HOST_REPLACE["lab_hours_workloads.py"][0])
        self.assertEqual(4, len(installer.HOST_REPLACE))
        self.assertEqual(3, len(installer.HOST_ADD))
        self.assertEqual(6, len(installer.GUEST_ADD))
        self.assertEqual(11, len(installer.GUEST_EXISTING))
        self.assertEqual(
            0o600,
            installer.GUEST_EXISTING_MODES["nlu-k2-development-corpus-v1.json"])

    def test_bundle_is_deterministic_and_contains_only_fixed_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = builder.build(root / "one")
            second = builder.build(root / "two")
            raw_first = Path(first["archive"]).read_bytes()
            raw_second = Path(second["archive"]).read_bytes()
            self.assertEqual(raw_first, raw_second)
            self.assertEqual(first["sha256"], hashlib.sha256(raw_first).hexdigest())
            with tarfile.open(first["archive"], "r:gz") as archive:
                names = set(archive.getnames())
            self.assertIn("bundle-manifest.json", names)
            self.assertIn(
                "scripts/aster-adaptive/nlu_k3_development_runner_v1.py", names)
            self.assertNotIn("artifacts/nlu-k2-development-corpus-v1.json", names)


if __name__ == "__main__":
    unittest.main()
