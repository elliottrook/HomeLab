import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_full_aster_first_screen_absolute_window.sh")


class AbsoluteWindowInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text()

    def test_exact_predecessor_and_candidate_are_pinned(self):
        self.assertIn("live_sha=328b41538451a47cf8ae3355c4a3f978c2cdc47cff848b856c1671178f0bca47", self.source)
        self.assertIn("candidate_sha=11568103c134b98821aad4154e79645375f15f3021fdaf9ce232340d8ef24d66", self.source)

    def test_only_launcher_is_installed_and_rollback_restores_it(self):
        self.assertIn("full_aster_first_screen_launch.py", self.source)
        self.assertEqual(2, self.source.count('install -o root -g root -m 0644'))
        self.assertNotIn("systemctl restart", self.source)
        self.assertNotIn("systemctl stop", self.source)
        self.assertNotIn("systemctl disable", self.source)

    def test_prestate_timer_and_poststate_are_checked(self):
        self.assertGreaterEqual(self.source.count("full-aster-first-screen-20261027.timer"), 2)
        for path in (
            "/var/lib/local-ai-lab/full-aster-first-screen.json",
            "/var/lib/local-ai-lab/full-aster-first-screen-guardian.json",
            "/var/lib/local-ai-lab/full-inference-drain.json",
        ):
            self.assertGreaterEqual(self.source.count(path), 2)


if __name__ == "__main__":
    unittest.main()
