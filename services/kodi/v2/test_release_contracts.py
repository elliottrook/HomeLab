"""Regression contracts for the final AsterTV v2 landing routes."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent


class ReleaseContractTests(unittest.TestCase):
    def test_search_catalogue_uses_current_seerr_route(self):
        root = ET.parse(HERE / "search_native/overlay/custom_1127_search.xml").getroot()
        catalogue = root.find(".//control[@id='51']")
        self.assertIsNotNone(catalogue)
        self.assertEqual(catalogue.findtext("onclick"), "RunScript(script.asterseerr)")
        self.assertEqual(catalogue.findtext("label"), "Search catalogue")
        source = (HERE / "seerr_native/default.py").read_text()
        self.assertIn("xbmcgui.getCurrentWindowId() != 11132", source)

    def test_music_hero_uses_current_semantic_actions(self):
        source = (HERE / "music_hero_ui.py").read_text()
        for identity, action in ((116, "hero-play"), (117, "hero-open"),
                                 (118, "hero-next"), (115, "hero-shuffle")):
            self.assertIn("_button(%d" % identity, source)
            self.assertIn("'%s'" % action, source)


if __name__ == "__main__":
    unittest.main()
