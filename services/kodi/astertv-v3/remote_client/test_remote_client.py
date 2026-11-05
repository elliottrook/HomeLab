import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "addon/service.asterremote"
SOURCE = (ROOT / "service.py").read_text()


class RemoteClientTests(unittest.TestCase):
    def test_source_and_addon_parse(self):
        ast.parse(SOURCE)
        root = ET.parse(ROOT / "addon.xml").getroot()
        self.assertEqual(root.attrib["id"], "service.asterremote")
        self.assertIsNotNone(root.find("./extension[@point='xbmc.service']"))

    def test_client_is_outbound_and_private_key_bound(self):
        self.assertIn('BASE = "http://192.168.70.10:9120/v1/remote"', SOURCE)
        self.assertIn('/storage/.aster-private/asterremote-client.key', SOURCE)
        self.assertIn('details.st_mode & 0o077', SOURCE)
        self.assertNotIn("HTTPServer", SOURCE)
        self.assertNotIn("socket.listen", SOURCE)

    def test_execution_is_semantic_not_general_rpc(self):
        tree = ast.parse(SOURCE)
        constants = {
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        self.assertNotIn("System.Exec", constants)
        self.assertNotIn("Application.Quit", constants)
        self.assertNotIn("VideoLibrary.Remove", constants)
        self.assertNotIn("GUI.SetProperty", constants)
        self.assertNotIn("Home Assistant", SOURCE)
        self.assertNotIn("subprocess", SOURCE)

    def test_equipment_actions_are_absent_until_m7(self):
        for value in ("volumeup", "volumedown", '"mute"', '"power"'):
            self.assertNotIn(value, SOURCE.casefold())

    def test_text_requires_active_keyboard_and_is_bounded(self):
        self.assertIn("keyboard_active()", SOURCE)
        self.assertIn("MAX_TEXT = 512", SOURCE)
        self.assertIn('rpc("Input.SendText"', SOURCE)
        self.assertNotIn("log(text", SOURCE)

    def test_search_reuses_accepted_global_search_contract(self):
        self.assertIn("aster-global-search-ui22,default", SOURCE)
        self.assertIn('home.setProperty("AsterSearch.VoiceQuery", text)', SOURCE)
        self.assertIn('home.setProperty("AsterSearch.Command", "voice")', SOURCE)


if __name__ == "__main__":
    unittest.main()
