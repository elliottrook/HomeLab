import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
V3 = HERE.parent
PLAYER = HERE / "resources/skins/Default/1080i/DigestPlayer.xml"
PILOT = V3 / "overlay/skin.asterhome.v3pilot/1080i/custom_1204_news_player.xml"
BASE = V3 / "low-spec/recovered/host-gates/script.asterruntime/aster-digest-player8/default.py"
SPEC = importlib.util.spec_from_file_location("news_player_transform", HERE / "transform.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NewsPlayerTests(unittest.TestCase):
    def test_runtime_xml_parses_and_uses_existing_digest_contract(self):
        root = ET.parse(PLAYER).getroot()
        self.assertEqual(root.findtext("defaultcontrol"), "203")
        text = PLAYER.read_text()
        for value in (
            "Digest.Image", "Digest.Title", "Digest.Summary", "Digest.Source",
            "Digest.Counter", "Digest.Playing", "Digest.Paused",
            "Player.Progress", "Player.Time(mm:ss)", "Player.Duration(mm:ss)",
            "ListItem.Art(thumb)", "ListItem.Property(Active)",
        ):
            self.assertIn(value, text)

    def test_runtime_focus_graph_matches_existing_controller_ids(self):
        root = ET.parse(PLAYER).getroot()
        controls = {node.get("id"): node for node in root.findall(".//control[@id]")}
        self.assertEqual(set(("200", "201", "202", "203", "204", "300")) - set(controls), set())
        self.assertEqual(controls["203"].findtext("onleft"), "201")
        self.assertEqual(controls["203"].findtext("onright"), "202")
        self.assertEqual(controls["300"].findtext("onleft"), "203")
        self.assertEqual(controls["300"].findtext("onright"), "200")

    def test_active_story_is_gold_and_focus_is_jade(self):
        text = PLAYER.read_text()
        self.assertIn("String.IsEqual(ListItem.Property(Active),true)", text)
        self.assertIn('colordiffuse="ffd8b778"', text)
        self.assertIn('colordiffuse="ff235640"', text)

    def test_controller_transform_exposes_only_existing_story_metadata(self):
        patched = MODULE.add_story_art(BASE.read_text())
        self.assertIn("item.setProperty('Source', row.source)", patched)
        self.assertIn("item.setArt({'thumb': row.image or", patched)
        self.assertIn("self.getControl(300).selectItem(row)", patched)
        self.assertIn("self.publish(row)", patched)
        with self.assertRaisesRegex(ValueError, "baseline-drift"):
            MODULE.add_story_art(patched)

    def test_pilot_flow_opens_the_player_candidate(self):
        ET.parse(PILOT)
        news = V3 / "overlay/skin.asterhome.v3pilot/1080i/custom_1198_news_rework.xml"
        self.assertIn("<onclick>ActivateWindow(1204)</onclick>", news.read_text())
        text = PILOT.read_text()
        self.assertIn("SYNTHETIC PLAYER · NO AUDIO", text)
        self.assertIn("Back to News", text)
        self.assertIn("ActivateWindow(1198)", text)

    def test_pilot_player_uses_semantic_icon_controls(self):
        text = PILOT.read_text()
        for icon in ("previous.svg", "pause.svg", "next.svg", "stop.svg"):
            self.assertIn(f"player-controls/{icon}", text)
        for old_label in ("<label>Previous</label>", "<label>Pause</label>",
                          "<label>Next</label>", "<label>Stop</label>"):
            self.assertNotIn(old_label, text)
        self.assertEqual(text.count("ui-button-focus-gold-rim.png"), 4)


if __name__ == "__main__":
    unittest.main()
