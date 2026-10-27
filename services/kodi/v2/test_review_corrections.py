import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_review_corrections import build
import review_corrections as subject


FIXTURE = Path("/private/tmp/aster-hp-corrections")


class ReviewCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((FIXTURE / name).is_file() for name in subject.PREDECESSORS):
            raise unittest.SkipTest("exact-owner-review-fixture-unavailable")
        for name, digest in subject.PREDECESSORS.items():
            if hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() != digest:
                raise unittest.SkipTest("exact-owner-review-fixture-drift")

    def test_home_copy_actions_and_request_move(self):
        root = ET.fromstring(subject.home((FIXTURE / "Home.xml").read_bytes()))
        synopsis = next(node for node in root.find(".//control[@id='21']").findall("control")
                        if node.get("type") == "textbox")
        self.assertEqual((synopsis.findtext("top"), synopsis.findtext("height")),
                         ("318", "86"))
        self.assertEqual(root.find(".//control[@id='122']").findtext("top"), "442")
        self.assertIsNone(root.find(".//control[@id='137']"))
        self.assertEqual(root.find(".//control[@id='134']/onright").text, "136")
        search = root.find(".//control[@id='135']")
        self.assertEqual(search.find("texturenofocus").get("colordiffuse"),
                         subject.SURFACE)

    def test_youtube_has_unique_focus_rows_and_bounded_hero(self):
        root = ET.fromstring(subject.youtube((FIXTURE / "MyVideoNav.xml").read_bytes()))
        landing = root.find(".//control[@id='9891']")
        self.assertEqual(root.findtext("onload"),
                         "AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:01,silent)")
        self.assertEqual([landing.find(f".//control[@id='{i}']") is not None
                          for i in (9530, 9531, 9532)], [True, True, True])
        self.assertTrue(any(node.findtext("height") == "620"
                            for node in landing.findall("control[@type='image']")))

    def test_side_rail_owns_requests_and_family_tracks_home(self):
        rail = subject.side_rail((FIXTURE / "IncludesHub.xml").read_bytes())
        root = ET.fromstring(rail); request = root.find(".//control[@id='9009']")
        self.assertEqual(request.findtext("onclick"), "RunScript(script.asteracquisition)")
        self.assertEqual(root.find(".//control[@id='9005']").findtext("onup"), "9009")
        outer = root.find(".//control[@id='9000']/control[@type='image']/texture")
        self.assertEqual(outer.get("colordiffuse"), subject.OUTLINE)
        home = subject.home((FIXTURE / "Home.xml").read_bytes())
        changed = {name: (home if name == "Home.xml" else
                          subject.standard_search((FIXTURE / name).read_bytes(), name))
                   for name in ("Home.xml", "Settings.xml", "custom_1111_digest.xml",
                                "custom_1112_home.xml")}
        family = json.loads(subject.family((FIXTURE / "family-manifest.json").read_bytes(), changed))
        self.assertEqual(family["skin"]["1080i/Home.xml"], hashlib.sha256(home).hexdigest())

    def test_all_page_search_capsules_share_outline_and_surface(self):
        for name in ("custom_1112_home.xml", "Settings.xml", "custom_1111_digest.xml",
                     "IncludesBooks.xml", "custom_1122_breaking.xml", "IncludesMusic.xml"):
            root = ET.fromstring(subject.standard_search((FIXTURE / name).read_bytes(), name))
            button = next(node for node in root.iter("control")
                          if node.get("type") == "button" and node.findtext("label") == "Search")
            self.assertEqual(button.find("texturenofocus").get("colordiffuse"),
                             subject.SURFACE, name)
            parent = next(node for node in root.iter() if button in list(node))
            permanent = [node for node in parent.findall("control[@type='image']")
                         if not node.findtext("visible") and
                         abs(int(node.findtext("left")) - int(button.findtext("left"))) <= 5]
            self.assertEqual(permanent[0].find("texture").get("colordiffuse"),
                             subject.OUTLINE, name)

    def test_build_is_immutable_exact_and_pinned(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            output = Path(temporary) / "candidate"
            pin = build(FIXTURE, output)
            self.assertEqual(hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(), pin)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(len(manifest["files"]), 11)
            with self.assertRaisesRegex(ValueError, "output"):
                build(FIXTURE, output)


if __name__ == "__main__": unittest.main()
