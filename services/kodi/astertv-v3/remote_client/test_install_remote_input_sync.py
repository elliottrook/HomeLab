import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).with_name("install_remote_input_sync.py")).read_text()


class RemoteInputSyncInstallerTests(unittest.TestCase):
    def test_source_parses_and_pins_each_predecessor(self):
        ast.parse(SOURCE)
        self.assertIn('"AsterTV-Jen": "6e033224', SOURCE)
        self.assertEqual(SOURCE.count('"22e06499'), 2)
        self.assertIn('NEW_SERVICE = "1a4d52f3', SOURCE)

    def test_rehearsal_is_bedroom_idle_and_checkpoint_bound(self):
        self.assertIn('host != "AsterTV-Bedroom"', SOURCE)
        self.assertIn('rpc("Player.GetActivePlayers")', SOURCE)
        self.assertIn('checkpoint / "live.py"', SOURCE)
        self.assertIn('checkpoint / "stable.py"', SOURCE)
        self.assertIn('checkpoint / "manifest.json"', SOURCE)
        self.assertIn('"predecessor_verified": predecessor_verified', SOURCE)

    def test_failure_restores_accepted_version_not_old_version(self):
        self.assertIn("accepted_manifest = manifest.read_bytes()", SOURCE)
        self.assertIn("shutil.copy2(source, LIVE)", SOURCE)
        self.assertIn("manifest.write_bytes(accepted_manifest)", SOURCE)
        self.assertIn('"credential_output": False', SOURCE)


if __name__ == "__main__": unittest.main()
