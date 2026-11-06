import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "repair_jen_home_identity.py"
SPEC = importlib.util.spec_from_file_location("repair_jen_home_identity", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class JenHomeIdentityRepairTests(unittest.TestCase):
    def test_repair_is_exact_host_hash_and_idle_bound(self):
        source = SOURCE.read_text()
        self.assertEqual(MODULE.HOST, "AsterTV-Jen")
        self.assertEqual(len(MODULE.PREDECESSOR), 64)
        self.assertEqual(len(MODULE.TARGET), 64)
        for token in ("active-playback", "predecessor-drift", "candidate-drift",
                      "home-authority-registry-drift", "profile-state:",
                      "profile-state-timeout:", "systemctl", "restart", "kodi",
                      "checkpoint.json"):
            self.assertIn(token, source)

    def test_repair_preserves_rollback_custody_and_never_changes_registry(self):
        source = SOURCE.read_text()
        self.assertIn('CHECKPOINT / "live.py"', source)
        self.assertIn('CHECKPOINT / "stable.py"', source)
        self.assertNotIn("REGISTRY.write", source)
        self.assertNotIn("profiles.json.tmp", source)


if __name__ == "__main__":
    unittest.main()
