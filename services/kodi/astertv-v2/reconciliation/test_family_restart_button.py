import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name("apply_family_restart_button.py").read_text()


class FamilyRestartButtonTests(unittest.TestCase):
    def test_source_is_syntactically_valid(self):
        ast.parse(SOURCE)

    def test_restart_is_kodi_only_and_confirmed(self):
        self.assertIn('xbmc.executebuiltin("RestartApp")', SOURCE)
        self.assertNotIn('xbmc.executebuiltin("Reboot")', SOURCE)
        self.assertIn("Dialog().yesno", SOURCE)
        self.assertIn("Player().isPlaying()", SOURCE)
        self.assertIn("Stop playback before restarting.", SOURCE)

    def test_button_and_physical_select_routes_match(self):
        route = "RunScript(special://skin/tools/restart_astertv.py)"
        self.assertGreaterEqual(SOURCE.count(route), 2)
        self.assertIn('<control type="button" id="208">', SOURCE)
        self.assertIn("<ondown>208</ondown>", SOURCE)

    def test_deployment_is_family_only_idle_and_checkpointed(self):
        self.assertIn('socket.gethostname() != "AsterTV-Family"', SOURCE)
        self.assertIn("require_idle()", SOURCE)
        self.assertIn("astertv-family-restart-button-20261031", SOURCE)
        self.assertIn('systemctl", "stop", "kodi', SOURCE)
        self.assertIn('systemctl", "start", "kodi', SOURCE)


if __name__ == "__main__":
    unittest.main()
