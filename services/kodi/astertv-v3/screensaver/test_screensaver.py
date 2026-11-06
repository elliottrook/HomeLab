import importlib.util
import json
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("aster_screensaver_policy", HERE / "policy.py")
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)
BUILD_SPEC = importlib.util.spec_from_file_location(
    "aster_screensaver_build", HERE / "build_candidate.py")
BUILDER = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(BUILDER)


class ScreensaverPolicyTests(unittest.TestCase):
    def test_music_pages_select_music_and_media_pages_select_media(self):
        for window in (11113, 11114, 11115, 11116, 11117):
            self.assertEqual(POLICY.context_for_window(window), POLICY.MUSIC)
        for window in (10000, 11121, 11125, 11130):
            self.assertEqual(POLICY.context_for_window(window), POLICY.MEDIA)

    def test_section_pages_select_their_approved_brand_context(self):
        for window in (11110, 11118, 11119, 11120):
            self.assertEqual(POLICY.context_for_window(window), POLICY.BOOKS)
        for window in (11111, 1122):
            self.assertEqual(POLICY.context_for_window(window), POLICY.NEWS)
        for window in (11112, 11134):
            self.assertEqual(POLICY.context_for_window(window), POLICY.HOME)
        source = (HERE / "default.py").read_text()
        for asset in ("27-aster-media-logo.png", "28-aster-books-logo.png",
                      "29-aster-music-logo.png", "30-aster-news-logo.png",
                      "aster-home-logo-512.png", "aster-compass-128.png"):
            self.assertIn(asset, source)

    def test_private_or_unknown_pages_fail_closed_to_neutral(self):
        for window in (None, "", "bad", 1201, 10016, 11133):
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

    def test_missing_art_keeps_black_surface_and_section_logo(self):
        source = (HERE / "default.py").read_text()
        self.assertIn("self.getControl(10).setVisible(False)", source)
        self.assertIn("self.getControl(12).setVisible(False)", source)
        self.assertIn("self.getControl(11).setVisible(True)", source)
        self.assertIn("if art:", source)
        self.assertIn("mark.setImage(LOGOS[context], True)", source)
        xml = (HERE / "resources/skins/Default/1080i/AsterIdle.xml").read_text()
        self.assertIn("<backgroundcolor>ff000000</backgroundcolor>", xml)

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

    def test_candidate_archive_is_deterministic_and_non_release(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.tar.gz"
            second = Path(directory) / "second.tar.gz"
            one = BUILDER.build(first)
            two = BUILDER.build(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(one["sha256"], two["sha256"])
            with tarfile.open(first, "r:gz") as archive:
                names = archive.getnames()
                self.assertEqual(names[-1], "manifest.json")
                record = json.load(archive.extractfile("manifest.json"))
            self.assertFalse(record["release"])
            self.assertEqual(record["status"], "non-production-test-candidate")
            self.assertEqual(
                [row["path"] for row in record["files"]], list(BUILDER.PAYLOAD))
            self.assertEqual(record["skin_dependencies"], list(BUILDER.SKIN_DEPENDENCIES))

    def test_jen_installer_is_host_bound_checkpointed_and_rollback_first(self):
        source = (HERE / "install_jen_canary.py").read_text()
        self.assertIn('HOST = "AsterTV-Jen"', source)
        self.assertIn('OLD_ID = "screensaver.asterhome.v2lab"', source)
        self.assertIn('NEW_ID = "screensaver.asterhome.v3"', source)
        self.assertIn("EXPECTED_OLD", source)
        self.assertIn("candidate-manifest-boundary", source)
        self.assertIn("v2-baseline-drift", source)
        self.assertIn("unexpected-current-screensaver", source)
        self.assertIn("shutil.copy2(settings, checkpoint", source)
        self.assertIn("shutil.copy2(database, checkpoint", source)
        self.assertIn("shutil.rmtree(new)", source)
        self.assertNotIn("release-guard", source.casefold())

    def test_branding_upgrade_is_exact_hash_and_atomic_rollback(self):
        source = (HERE / "upgrade_jen_branding.py").read_text()
        self.assertIn("EXPECTED_CURRENT", source)
        self.assertIn("current-canary-drift", source)
        self.assertIn("shutil.copytree(target, checkpoint", source)
        self.assertIn("os.rename(target, displaced)", source)
        self.assertIn("os.rename(temporary, target)", source)
        self.assertIn("os.rename(displaced, target)", source)
        self.assertIn("v3-selection-not-retained", source)


if __name__ == "__main__":
    unittest.main()
