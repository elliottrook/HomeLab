"""Regression checks for the HP owner-review follow-up."""

from pathlib import Path
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET

import build_owner_review_followup as builder
import owner_review_followup as subject


FIXTURE = Path("/private/tmp/aster-owner-review2")


def root(name, transform):
    return ET.fromstring(transform((FIXTURE / name).read_bytes()))


@unittest.skipUnless(FIXTURE.is_dir(), "HP owner-review fixture unavailable")
class OwnerReviewFollowupTests(unittest.TestCase):
    def test_home_and_side_rail(self):
        home = root("Home.xml", subject.home)
        hero = home.find(".//control[@id='21']")
        synopsis = next(node for node in hero.findall("control")
                        if node.get("type") == "textbox")
        self.assertEqual(synopsis.findtext("font"), "font18")
        self.assertIn("9009", ET.tostring(home, encoding="unicode"))
        rail = root("IncludesHub.xml", subject.side_rail)
        request = [node.findtext("texture") for node in rail.findall(".//control[@type='image']")
                   if node.findtext("top") in ("349", "345")]
        self.assertEqual(request.count("special://skin/media/aster-icon-128.png"), 2)

    def test_media_books_and_music_heroes(self):
        media = root("MyVideoNav.xml", subject.media_browser)
        generic = media.find(".//control[@id='9893']")
        self.assertEqual(generic.find("control[@id='9100']/width").text, "180")
        self.assertEqual(generic.find("control[@id='9101']/height").text, "44")
        plot = next(node for node in generic.findall("control")
                    if node.findtext("label") == "$VAR[AsterBrowsePlot]")
        self.assertEqual((plot.findtext("font"), plot.findtext("height")), ("font18", "68"))
        books = root("IncludesBooks.xml", subject.books)
        self.assertEqual(books.find(".//control[@id='300']/height").text, "44")
        self.assertIn("<height>620</height>", ET.tostring(books, encoding="unicode"))
        music = root("IncludesMusic.xml", subject.music)
        rendered = ET.tostring(music, encoding="unicode")
        self.assertIn("special://skin/media/13-music.png", rendered)
        self.assertNotIn("special://skin/media/20-music-app.png", rendered)
        self.assertIn("<height>620</height>", rendered)

    def test_settings_and_acquisition_navigation(self):
        settings = root("Settings.xml", subject.settings)
        self.assertEqual(settings.find(".//control[@id='200']/onleft").text, "8999")
        acquisition = root("custom_1133_acquisition.xml", subject.acquisition)
        self.assertIsNotNone(acquisition.find(".//include[@content='AsterNavigationRail']"))
        group = acquisition.find(".//control[@id='600']")
        self.assertIn("9009", group.findtext("visible"))
        for identity in (10, 11, 12):
            button = group.find("control[@id='%s']" % identity)
            self.assertEqual((button.findtext("width"), button.findtext("height"),
                              button.findtext("align"), button.findtext("aligny")),
                             ("120", "44", "center", "center"))
        self.assertEqual(group.find("control[@id='50']/width").text, "180")
        self.assertEqual(group.find("control[@id='30']/onleft").text, "8999")

    def test_family_manifest_and_immutable_build(self):
        changed = {
            "Home.xml": subject.home((FIXTURE / "Home.xml").read_bytes()),
            "Settings.xml": subject.settings((FIXTURE / "Settings.xml").read_bytes()),
        }
        family = json.loads(subject.family(
            (FIXTURE / "family-manifest.json").read_bytes(), changed))
        self.assertEqual(family["skin"]["1080i/Home.xml"], subject.sha(changed["Home.xml"]))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "candidate"
            pin = builder.build(FIXTURE, target)
            manifest = json.loads((target / "manifest.json").read_bytes())
            self.assertEqual(manifest["kind"], "hp-owner-review-followup.v1")
            self.assertEqual(len(manifest["files"]), 8)
            self.assertEqual(subject.sha((target / "manifest.json").read_bytes()), pin)


if __name__ == "__main__":
    unittest.main()
