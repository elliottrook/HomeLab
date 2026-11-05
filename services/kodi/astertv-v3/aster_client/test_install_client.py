#!/usr/bin/env python3
"""Static safety tests for the Jen client installer."""

import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_client.py").read_text()


class InstallerTests(unittest.TestCase):
    def test_installer_parses_and_is_jen_bound(self):
        ast.parse(SOURCE)
        self.assertIn('EXPECTED_HOST = "AsterTV-Jen"', SOURCE)

    def test_installer_requires_idle_guard_and_private_key(self):
        for value in ("Player.GetActivePlayers", "release-guard-not-clean",
                      "details.st_mode & 0o077", "credential-boundary"):
            self.assertIn(value, SOURCE)

    def test_checkpoint_precedes_kodi_stop(self):
        self.assertLess(SOURCE.index("destination = checkpoint(identifier)"),
                        SOURCE.index('run("systemctl", "stop", "kodi")'))

    def test_installer_enables_new_addon(self):
        self.assertIn('Addons.SetAddonEnabled', SOURCE)
        self.assertIn('candidate-addon-not-enabled', SOURCE)

    def test_profile_identity_modules_and_state_are_checkpointed(self):
        for value in ("registry.py", "access_policy.py", "authority.py",
                      "identity_resolver.py", "PROFILE_STATE", "build_registry"):
            self.assertIn(value, SOURCE)


if __name__ == "__main__":
    unittest.main()
