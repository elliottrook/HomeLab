import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("install_select_dispatch_parity.py").read_text()


class SelectDispatchParityInstallerTests(unittest.TestCase):
    def test_installer_is_host_bounded_hash_pinned_and_idle_only(self):
        ast.parse(SOURCE)
        for host in ("AsterTV-Jen", "AsterTV-Family", "AsterTV-Bedroom"):
            self.assertIn(host, SOURCE)
        self.assertIn("PREDECESSOR =", SOURCE)
        self.assertIn("SUCCESSOR =", SOURCE)
        self.assertIn('rpc("Player.GetActivePlayers")', SOURCE)
        self.assertIn('raise RuntimeError("active-playback")', SOURCE)

    def test_installer_updates_live_and_stable_with_automatic_rollback(self):
        self.assertIn("shutil.copy2(source, LIVE)", SOURCE)
        self.assertIn("shutil.copy2(source, stable_service)", SOURCE)
        self.assertIn('enable(False)', SOURCE)
        self.assertIn('enable(True)', SOURCE)
        self.assertIn('checkpoint / "live.py"', SOURCE)
        self.assertIn('checkpoint / "stable.py"', SOURCE)
        self.assertIn('"kodi_restart": False', SOURCE)


if __name__ == "__main__":
    unittest.main()
