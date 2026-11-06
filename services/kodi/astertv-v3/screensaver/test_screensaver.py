import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("aster_screensaver_policy", HERE / "policy.py")
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


class ScreensaverPolicyTests(unittest.TestCase):
    def test_music_pages_select_music_and_media_pages_select_media(self):
        for window in (11113, 11114, 11115, 11116, 11117):
            self.assertEqual(POLICY.context_for_window(window), POLICY.MUSIC)
        for window in (10000, 11110, 11121, 11125, 11130):
            self.assertEqual(POLICY.context_for_window(window), POLICY.MEDIA)

    def test_private_or_unknown_pages_fail_closed_to_neutral(self):
        for window in (None, "", "bad", 11111, 11112, 11118, 11120, 11134, 1201):
            self.assertEqual(POLICY.context_for_window(window), POLICY.NEUTRAL)
        self.assertEqual(POLICY.context_for_launch("cameras", 11113), POLICY.NEUTRAL)

    def test_reviewed_explicit_context_wins(self):
        self.assertEqual(POLICY.context_for_launch("neutral", 11113), POLICY.NEUTRAL)
        self.assertEqual(POLICY.context_for_launch("music", 11110), POLICY.MUSIC)
        self.assertEqual(POLICY.context_for_launch("media", 11113), POLICY.MEDIA)

    def test_mark_moves_between_four_safe_corners(self):
        expected = ((1630, 878), (50, 878), (1630, 48), (50, 48))
        self.assertEqual(tuple(POLICY.mark_position(i) for i in range(4)), expected)
        self.assertEqual(POLICY.mark_position(4), expected[0])

    def test_candidate_has_separate_fullscreen_and_album_surfaces(self):
        root = ET.parse(HERE / "resources/skins/Default/1080i/AsterIdle.xml").getroot()
        controls = {node.attrib.get("id"): node for node in root.findall(".//control")}
        self.assertEqual(controls["10"].findtext("width"), "1920")
        self.assertEqual(controls["12"].findtext("width"), "760")
        self.assertEqual(controls["12"].findtext("height"), "760")

    def test_candidate_excludes_sensitive_sources_and_sound(self):
        source = (HERE / "default.py").read_text().casefold()
        for forbidden in ("camera", "frigate", "password", "credential", "playsfx"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)
        self.assertIn("player.hasmedia", source)
        self.assertIn("hometimeractive", source)
        self.assertIn("hometimerexpired", source)

    def test_tracker_publishes_only_coarse_context(self):
        source = (HERE / "service.py").read_text()
        self.assertIn('PROPERTY = "AsterIdle.Context"', source)
        self.assertIn("context_for_window", source)
        self.assertIn('getCondVisibility("System.ScreenSaverActive")', source)
        for forbidden in ("label", "title", "account", "profile", "camera", "entity"):
            self.assertNotIn(forbidden, source.casefold())
        addon = ET.parse(HERE / "addon.xml").getroot()
        extensions = {(node.attrib.get("point"), node.attrib.get("library"))
                      for node in addon.findall("extension")}
        self.assertIn(("xbmc.service", "service.py"), extensions)


if __name__ == "__main__":
    unittest.main()
