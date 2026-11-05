#!/usr/bin/env python3
"""Static and presentation tests for the bounded Jen AsterTV client."""

import ast
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "addon/script.astertv.voice"
SOURCE = (ROOT / "default.py").read_text(encoding="utf-8")


class ClientTests(unittest.TestCase):
    def test_python_and_xml_parse(self):
        ast.parse(SOURCE)
        ET.parse(ROOT / "addon.xml")
        for name in ("direct.xml", "search.xml"):
            ET.parse(ROOT / "resources/skins/default/1080i" / name)

    def test_guest_fails_before_broker(self):
        tree = ast.parse(SOURCE)
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "broker_intent")
        rendered = ast.unparse(function)
        self.assertLess(rendered.index("profile != 'jason'"), rendered.index("urllib.request.Request"))

    def test_private_pages_mirror_local_profile_authority(self):
        for value in ('"cameras": ("cameras", "home_assistant")',
                      '"home": ("home_control", "home_assistant")',
                      '"youtube": ("personal_youtube", "youtube")'):
            self.assertIn(value, SOURCE)
        self.assertIn("That page is not enabled for this AsterTV profile.", SOURCE)

    def test_no_general_remote_authority(self):
        denied = ("Player.Open", "Application.Quit", "System.Exec",
                  "subprocess", "os.system", "Home Assistant", "service.call")
        for value in denied:
            self.assertNotIn(value, SOURCE)
        self.assertIn('BROKER = "http://192.168.70.10:9120/v1/astertv/intent"', SOURCE)
        self.assertIn("xbmc.executeJSONRPC", SOURCE)
        self.assertNotIn("VideoLibrary.Remove", SOURCE)

    def test_credential_is_private_file_only(self):
        self.assertIn('/storage/.aster-private/astertv-broker.key', SOURCE)
        self.assertIn('special://home/addons/script.astertv.voice', SOURCE)
        self.assertIn('details.st_mode & 0o077', SOURCE)
        self.assertNotIn("ASTER_TV_API_KEY", SOURCE)

    def test_search_reuses_accepted_details_routes(self):
        self.assertIn("aster-series-preview24,default", SOURCE)
        self.assertIn('AsterSearch.VoiceQuery', SOURCE)
        self.assertIn('AsterSearch.Command', SOURCE)
        self.assertIn("weakening the controller's boundary", SOURCE)
        self.assertIn('window.setProperty("Series.Command", "select")', SOURCE)

    def test_direct_card_auto_closes_before_action_continues(self):
        self.assertIn("dialog.show()", SOURCE)
        self.assertIn("xbmc.sleep(1400)", SOURCE)
        self.assertIn("dialog.close()", SOURCE)

    def test_search_dialog_is_destroyed_before_handoff(self):
        start = SOURCE.index("def show_search")
        end = SOURCE.index("def open_global_search")
        body = SOURCE[start:end]
        self.assertLess(body.index("del dialog"), body.index("open_global_search"))

    def test_news_reuses_guarded_digest_player(self):
        self.assertIn("from aster_v2_digest import main as digest_main", SOURCE)
        self.assertIn('digest_main("play")', SOURCE)

    def test_dialogs_use_accepted_aster_assets(self):
        combined = "".join(
            (ROOT / "resources/skins/default/1080i" / name).read_text(encoding="utf-8")
            for name in ("direct.xml", "search.xml")
        )
        for asset in ("aster-compass-128.png", "aster-ai-listening-png",
                      "ui-button-focus-gold-rim.png", "ui-dialog-result-focus.png"):
            self.assertIn(asset, combined)


if __name__ == "__main__":
    unittest.main()
