#!/usr/bin/env python3
"""Static regression gates for the Stream M TV-details package."""
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "deploy/tv-details"
XML = PACKAGE / "aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml"


class TvDetailsPackageTests(unittest.TestCase):
    def test_deployable_page_has_no_synthetic_content(self):
        data = XML.read_text()
        ET.fromstring(data)
        self.assertNotIn("<content>", data)
        for fixture in ("Aurora Station", "The Signal Above", "Mara Vale"):
            self.assertNotIn(fixture, data)

    def test_dynamic_controls_are_present_once(self):
        root = ET.parse(XML).getroot()
        ids = [node.attrib.get("id") for node in root.iter("control")]
        for identity in ("200", "202", "203", "204", "300", "610", "611", "612"):
            self.assertEqual(ids.count(identity), 1, identity)

    def test_episode_art_uses_controller_property_and_season_strip_is_bounded(self):
        data = XML.read_text()
        self.assertEqual(data.count("ListItem.Property(Still)"), 2)
        self.assertEqual(data.count("ListItem.Property(Synopsis)"), 2)
        self.assertEqual(data.count("ListItem.Property(Metadata)"), 2)
        self.assertNotIn("<height>720</height>", data)
        self.assertIn("player-controls/trailer.png", data)
        self.assertTrue((PACKAGE / "skin.asterhome/media/player-controls/trailer.png").is_file())

    def test_seasons_and_cast_use_the_connected_dynamic_routes(self):
        source = (PACKAGE / "aster-series-preview24/v3_series_extension.py").read_text()
        self.assertIn("group.number not in (None, 0)", source)
        self.assertIn("control.setHeight(min(len(seasons), 8) * 88)", source)
        self.assertIn("self._v3_season_indices", source)
        self.assertIn("AlarmClock(AsterActor,", source)
        self.assertIn("self.close()", source)
        for installer in ("deploy.py", "hotfix_tv_connections.py"):
            installer_source = (PACKAGE / installer).read_text()
            self.assertIn('"method": "Addons.SetAddonEnabled"', installer_source)
            self.assertIn('"addonid": "plugin.video.astersearch"', installer_source)

    def test_ok_dispatch_covers_every_dynamic_control(self):
        source = (PACKAGE / "aster-series-preview24/v3_series_extension.py").read_text()
        self.assertIn("(200, 202, 203, 204, 300, 610, 611, 612)", source)
        self.assertIn("def consume_command(self):", source)

    def test_news_repair_restores_entry_and_pin(self):
        source = (PACKAGE / "repair_digest_entry.py").read_text()
        self.assertIn("main(sys.argv[1])", source)
        self.assertIn("9e3644b7d012bc7610f7366608456ce06ffe1d8b6eee315574bb762d5a186e9c", source)


if __name__ == "__main__":
    unittest.main()
