import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
UNIT = ROOT / "services/local-ai-lease/aster-a1-test.service"
MANIFEST = ROOT / "services/local-ai-lease/A1-HOST-INSTALL-MANIFEST.md"


class A1HostManifestTests(unittest.TestCase):
    def test_unit_is_disabled_by_default_and_controller_startable(self):
        text = UNIT.read_text()
        self.assertIn("User=aster-a1-test", text)
        self.assertIn("Group=aster-a1-test", text)
        self.assertIn("--port 19104", text)
        self.assertIn("--workers 1", text)
        self.assertNotIn("RefuseManualStart", text)
        self.assertNotIn("RefuseManualStop", text)
        self.assertIn("IPAddressAllow=127.0.0.0/8 192.168.70.12/32", text)
        self.assertIn("IPAddressDeny=any", text)
        self.assertIn("CapabilityBoundingSet=", text)

    def test_manifest_rejects_container_wide_network_policy_and_requires_probe_split(self):
        text = MANIFEST.read_text()
        self.assertIn("container-wide nftables allowlist", text)
        self.assertIn("separate disposable probe", text)
        self.assertIn("final A1 request body", text)
        self.assertIn("source-bound application backup checkpoint", text)
        self.assertIn("not a lease receipt", text)

    def test_runner_hash_is_pinned_in_local_manifest(self):
        digest = hashlib.sha256((ROOT / "services/local-ai-lease/a1_service_runner.py").read_bytes()).hexdigest()
        self.assertIn("a1_service_runner.py", MANIFEST.read_text())
        self.assertIn(digest, MANIFEST.read_text())


if __name__ == "__main__":
    unittest.main()
