import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_youtube_landing import build, TARGETS
from youtube_landing import (extend_includes, extend_navigation, NAV_SHA, ROOT,
                             SEARCH, NOT_ROOT_OR_SEARCH, SEARCH_ROUTE)
from youtube_landing_install import run


HERE = Path(__file__).resolve().parent
SKIN = HERE.parent / "skin.asterhome/1080i"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class YouTubeLandingCompositionTests(unittest.TestCase):
    def test_root_has_hero_top_rail_and_three_official_rows(self):
        result = extend_navigation((SKIN / "MyVideoNav.xml").read_bytes())
        root = ET.fromstring(result)
        self.assertEqual(sha(SKIN / "MyVideoNav.xml"), NAV_SHA)
        generic = root.find(".//control[@id='9890']")
        landing = root.find(".//control[@id='9891']")
        search = root.find(".//control[@id='9892']")
        self.assertEqual(generic.findtext("visible"), "!" + ROOT)
        self.assertEqual(landing.findtext("visible"), ROOT)
        self.assertEqual(search.findtext("visible"), SEARCH)
        self.assertEqual(len(root.findall(".//control[@id='50']")), 1)
        self.assertIsNotNone(root.find(".//control[@id='9530']"))
        self.assertIsNotNone(root.find(".//control[@id='9531']"))
        self.assertIsNotNone(root.find(".//control[@id='9532']"))
        groups = root.find("controls").findall("control")
        self.assertEqual(groups[0].get("id"), "9890")
        self.assertEqual(groups[1].get("id"), "9891")
        self.assertEqual(search.get("id"), "9892")
        self.assertEqual(
            root.findtext("onload"),
            "AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:01,silent)")
        self.assertEqual(root.findtext('defaultcontrol'), '50')
        self.assertEqual(root.find(".//control[@id='9300']/ondown").text,
                         "9530")
        hero = landing.find("control[@type='image'][2]")
        self.assertTrue(any(node.findtext('height') == '620'
                            for node in landing.findall("control[@type='image']")))
        panels = [landing.find(f".//control[@id='{identity}']")
                  for identity in (9530, 9531, 9532)]
        self.assertEqual([panel.findtext('top') for panel in panels],
                         ['425', '625', '825'])
        self.assertTrue(all(panel.findtext('height') == '160' for panel in panels))
        self.assertTrue(all(panel.find('itemlayout').get('height') == '160'
                            for panel in panels))
        titles = [panel.find("itemlayout/control[@type='label']")
                  for panel in panels]
        self.assertTrue(all(title.findtext('top') == '126'
                            and title.findtext('height') == '30'
                            for title in titles))
        for identity in range(9300, 9306):
            self.assertIsNotNone(root.find(f".//control[@id='{identity}']"))
        for identity in range(9400, 9405):
            self.assertIsNotNone(root.find(f".//control[@id='{identity}']"))
        self.assertEqual(root.findall(".//control[@id='50']/onback"), [])
        raw = result.decode()
        self.assertIn("AsterYouTubeHeroTitle", raw)
        self.assertIn("special/my_subscriptions", raw)
        self.assertIn("hide_folders=true", raw)
        self.assertIn("special/recommendations", raw)
        self.assertIn("special/playlist/WL", raw)
        self.assertTrue(any(SEARCH_ROUTE in (node.text or "")
                            for node in root.findall(".//onclick")))
        self.assertIn("Search again", raw)
        self.assertNotIn("youtube.com", raw)
        includes = extend_includes((SKIN / "Includes.xml").read_bytes())
        self.assertIn(b"Choose a video", includes)

    def test_predecessor_drift_is_refused(self):
        with self.assertRaisesRegex(ValueError, "youtube-landing-nav-predecessor"):
            extend_navigation(b"<window />")


class YouTubeLandingBuildInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir="/private/tmp")
        self.root = Path(self.temporary.name)
        self.stage = self.root / "stage"
        self.pin = build(self.stage)
        self.storage = self.root / "storage"
        self.storage.mkdir()
        sources = {
            ".kodi/addons/skin.asterhome/1080i/Includes.xml":
                extend_includes((SKIN / "Includes.xml").read_bytes(),
                                include_search=False),
            ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml":
                extend_navigation((SKIN / "MyVideoNav.xml").read_bytes(),
                                  include_search=False),
        }
        for target, raw in sources.items():
            path = self.storage / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.secret = self.storage / ".kodi/userdata/addon_data/plugin.video.youtube/api_keys.json"
        self.secret.parent.mkdir(parents=True)
        self.secret.write_bytes(b"private-test-fixture")

    def tearDown(self):
        self.temporary.cleanup()

    def test_manifest_is_bounded_to_official_skin_presentation(self):
        manifest = json.loads((self.stage / "manifest.json").read_text())
        self.assertEqual(manifest["kind"], "hp-aster-youtube-landing.v2")
        self.assertEqual(manifest["official_addon"], "plugin.video.youtube")
        self.assertEqual(manifest["credential_files"], 0)
        self.assertFalse(manifest["production_changed"])
        self.assertEqual({row["path"] for row in manifest["files"]},
                         set(TARGETS.values()))
        self.assertEqual(manifest["rows"],
                         ["subscriptions", "recommendations", "watch-later"])
        self.assertEqual(manifest["search_view"],
                         ["aster-keyboard", "focused-result-hero",
                          "multi-row-result-grid"])

    def test_install_verify_and_rollback_preserve_account_state(self):
        before_secret = sha(self.secret)
        result = run("install", self.stage, self.storage, self.pin,
                     idle=lambda: True)
        self.assertTrue(result["installed"])
        self.assertTrue(run("verify", self.stage, self.storage, self.pin,
                            idle=lambda: True)["active"])
        self.assertEqual(sha(self.secret), before_secret)
        self.assertTrue(run("rollback", self.stage, self.storage, self.pin,
                            idle=lambda: True)["rolled_back"])
        self.assertFalse(run("verify", self.stage, self.storage, self.pin,
                             idle=lambda: True)["active"])
        self.assertEqual(sha(self.secret), before_secret)

    def test_requires_home_idle_and_exact_predecessor(self):
        with self.assertRaisesRegex(ValueError, "youtube-landing-home-idle-required"):
            run("install", self.stage, self.storage, self.pin,
                idle=lambda: False)
        target = self.storage / ".kodi/addons/skin.asterhome/1080i/MyVideoNav.xml"
        target.write_bytes(b"drift")
        with self.assertRaisesRegex(ValueError, "youtube-landing-exact-predecessor"):
            run("install", self.stage, self.storage, self.pin,
                idle=lambda: True)


if __name__ == "__main__":
    unittest.main()
