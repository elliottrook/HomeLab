import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_native_input_monitor.py").read_text()


class NativeInputInstallerTests(unittest.TestCase):
    def test_bedroom_hash_checkpoint_idle_and_rollback_gates(self):
        ast.parse(SOURCE)
        for value in ('HOST = "AsterTV-Bedroom"', "native-input-predecessor-drift",
                      'rpc("Player.GetActivePlayers")', '"live.py": LIVE',
                      '"stable.py": STABLE_SERVICE', '"manifest.json": MANIFEST'):
            self.assertIn(value, SOURCE)
        self.assertIn("except Exception:", SOURCE)

    def test_reload_is_addon_only_and_preserves_kodi(self):
        self.assertIn("enable(False)", SOURCE)
        self.assertIn("enable(True)", SOURCE)
        self.assertNotIn("systemctl", SOURCE)
        self.assertNotIn("Application.Quit", SOURCE)


if __name__ == "__main__": unittest.main()
