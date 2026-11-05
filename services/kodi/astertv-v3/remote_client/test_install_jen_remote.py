import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INSTALLER = (ROOT / "install_jen_remote.py").read_text()
APPLY = (ROOT / "apply_remote_client.py").read_text()


class InstallJenRemoteTests(unittest.TestCase):
    def test_sources_parse_and_are_jen_only(self):
        ast.parse(INSTALLER); ast.parse(APPLY)
        self.assertIn('HOST = "AsterTV-Jen"', INSTALLER)
        self.assertIn('HOST = "AsterTV-Jen"', APPLY)
        self.assertNotIn("AsterTV-Family", INSTALLER + APPLY)
        self.assertNotIn("AsterTV-Bedroom", INSTALLER + APPLY)

    def test_checkpoint_includes_database_addon_key_and_overlay(self):
        for value in ('"addon": ADDON', '"database": DATABASE', '"key": KEY',
                      '"stable": STABLE', '"service": SERVICE'):
            self.assertIn(value, INSTALLER)
        self.assertIn("restore()", INSTALLER)
        self.assertIn("rollback-state-drift", INSTALLER)
        self.assertIn("new-target-already-present", INSTALLER)

    def test_key_stays_private_and_transient_input_is_removed(self):
        self.assertIn('/run/asterremote-client.key', INSTALLER)
        self.assertIn("private-input-key-required", INSTALLER)
        self.assertIn("os.chmod(KEY, 0o600)", INSTALLER)
        self.assertIn("mode=0o700, exist_ok=True", INSTALLER)
        self.assertIn("INPUT_KEY.unlink", INSTALLER)
        self.assertIn('"credential_output": False', INSTALLER + APPLY)

    def test_overlay_is_after_m6_before_kodi(self):
        self.assertIn("After=astertv-v3-m6-jen.service", INSTALLER)
        self.assertIn("Before=kodi.service", INSTALLER)
        self.assertIn("WantedBy=kodi.service", INSTALLER)

    def test_apply_is_manifest_bound_and_does_not_touch_guard(self):
        self.assertIn("remote-client-manifest-drift", APPLY)
        self.assertNotIn("release_guard", APPLY)
        self.assertNotIn("accepted-manifest", APPLY)


if __name__ == "__main__":
    unittest.main()
