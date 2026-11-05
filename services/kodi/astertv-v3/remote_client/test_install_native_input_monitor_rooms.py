import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_native_input_monitor_rooms.py").read_text()


class NativeInputRoomInstallerTests(unittest.TestCase):
    def test_scope_hash_idle_checkpoint_and_rollback(self):
        ast.parse(SOURCE)
        for value in ('"AsterTV-Jen"', '"AsterTV-Family"',
                      "native-input-predecessor-drift", 'rpc("Player.GetActivePlayers")',
                      '"live.py": LIVE', '"stable.py": stable_service'):
            self.assertIn(value, SOURCE)
        self.assertNotIn("AsterTV-Bedroom", SOURCE)
        self.assertIn("except Exception:", SOURCE)

    def test_reload_is_addon_only(self):
        self.assertIn("enable(False)", SOURCE)
        self.assertIn("enable(True)", SOURCE)
        self.assertNotIn("systemctl", SOURCE)


if __name__ == "__main__": unittest.main()
