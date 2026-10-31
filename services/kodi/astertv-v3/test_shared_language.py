#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
V3 = ROOT / "services/kodi/astertv-v3"
OVERLAY = V3 / "overlay/skin.asterhome.v3pilot"
PAGE = OVERLAY / "1080i/custom_1190_v3language.xml"
YOUTUBE_PAGE = OVERLAY / "1080i/custom_1191_youtube_rework.xml"
INCLUDES = OVERLAY / "1080i/IncludesV3.xml"
COLORS = OVERLAY / "colors/defaults.xml"
PATCH = V3 / "patches/001-load-v3-includes.patch"
ARCHIVE = ROOT / "services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz"


class SharedLanguageTests(unittest.TestCase):
    def test_xml_is_well_formed(self) -> None:
        for path in (PAGE, YOUTUBE_PAGE, INCLUDES, COLORS, OVERLAY / "addon.xml"):
            with self.subTest(path=path):
                ET.parse(path)

    def test_focus_graph_is_closed_and_targets_are_remote_sized(self) -> None:
        page = ET.parse(PAGE).getroot()
        buttons = {node.attrib["id"]: node for node in page.findall(".//control[@type='button']")}
        self.assertEqual(len(buttons), 9)

        include_root = ET.parse(INCLUDES).getroot()
        include_heights = {
            node.attrib["name"]: int(node.findtext("height", "0"))
            for node in include_root.findall("include")
        }
        for control_id, button in buttons.items():
            with self.subTest(control_id=control_id):
                include_name = button.findtext("include")
                height = int(button.findtext("height", "0")) or include_heights[include_name]
                self.assertGreaterEqual(height, 44)
                for direction in ("onleft", "onright", "onup", "ondown"):
                    self.assertIn(button.findtext(direction), buttons)

    def test_fixture_covers_explicit_states_and_safe_return(self) -> None:
        text = PAGE.read_text()
        for label in ("Ready", "Loading", "Nothing here yet", "Source unavailable"):
            self.assertIn(label, text)
        self.assertIn("Synthetic design fixture", text)
        self.assertIn("<label>Back</label>", text)
        self.assertGreaterEqual(text.count("<onclick>ActivateWindow(Home)</onclick>"), 2)

    def test_semantic_tokens_are_present(self) -> None:
        color_nodes = ET.parse(COLORS).getroot().findall("color")
        colors = {node.attrib["name"] for node in color_nodes}
        required = {
            "asterV3Bg",
            "asterV3Panel",
            "asterV3Text",
            "asterV3Muted",
            "asterV3Focus",
            "asterV3Success",
            "asterV3Danger",
        }
        self.assertTrue(required <= colors)

        values = {node.attrib["name"]: (node.text or "").lower() for node in color_nodes}
        self.assertEqual(values["asterV3Bg"], "ff191814")
        self.assertEqual(values["asterV3Panel"], "ff292721")
        self.assertEqual(values["asterV3Focus"], values["asterGold"])
        self.assertEqual(values["asterV3Success"], values["asterSage"])
        forbidden_blue_values = {"ff0b1020", "ff151d31", "ff1b2740", "ff111a2c", "ff2b3a58"}
        self.assertTrue(forbidden_blue_values.isdisjoint(values.values()))

    def test_overlay_patch_applies_to_immutable_v2_baseline(self) -> None:
        member = "aster-v2-package/lab-addon-snapshot/skin.asterhome/1080i/Includes.xml"
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            (tmp / "1080i").mkdir()
            with tarfile.open(ARCHIVE, "r:gz") as archive:
                source = archive.extractfile(member)
                self.assertIsNotNone(source)
                (tmp / "1080i/Includes.xml").write_bytes(source.read())
            completed = subprocess.run(
                ["patch", "-d", str(tmp), "-p1", "--dry-run", "-i", str(PATCH)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_youtube_rework_keeps_familiar_structure_and_adds_depth(self) -> None:
        page = ET.parse(YOUTUBE_PAGE).getroot()
        text = YOUTUBE_PAGE.read_text()
        for label in ("Search", "Subscriptions", "For You", "Watch Later", "My Channel", "Back"):
            self.assertIn(f"<label>{label}</label>", text)
        self.assertEqual(text.count("special://skin/media/aster-compass-128.png"), 5)
        self.assertIn("<include>AsterV3MediaSearchPill</include>", text)
        self.assertEqual(text.count("<include>AsterV3MediaPill</include>"), 5)
        self.assertIn("<backgroundcolor>asterStone</backgroundcolor>", text)
        self.assertIn("<colordiffuse>asterStone</colordiffuse>", text)
        self.assertIn("special://skin/media/ui-hero-left-fade.png", text)
        self.assertIn("special://skin/media/ui-hero-bottom-fade.png", text)
        self.assertLess(
            text.index("special://skin/media/ui-hero-left-fade.png"),
            text.index("special://skin/media/ui-hero-bottom-fade.png"),
        )
        self.assertIn("<label>YouTube</label><font>font36</font><textcolor>asterV3Text</textcolor>", text)
        self.assertIn('colordiffuse="asterCharcoalGlass"', text)
        self.assertIn('colordiffuse="asterPaperGlass"', text)
        self.assertNotIn('colordiffuse="66000000"', text)
        self.assertNotIn('colordiffuse="33000000"', text)
        self.assertNotIn("<include>AsterV3PageBackdrop</include>", text)

        includes = ET.parse(INCLUDES).getroot()
        youtube_card = includes.find("include[@name='AsterV3YouTubeCard']")
        self.assertIsNotNone(youtube_card)
        self.assertGreaterEqual(int(youtube_card.findtext("height", "0")), 294)
        self.assertEqual(youtube_card.find("texturefocus").attrib["colordiffuse"], "asterSageGlass")

        for title in ("A cinematic 16:9 card", "Titles sit on the card", "Focus lifts, never dims", "Rounded artwork and depth"):
            self.assertIn(f"<label>{title}</label>", text)

        buttons = {node.attrib["id"]: node for node in page.findall(".//control[@type='button']")}
        self.assertEqual(len(buttons), 11)
        for button in buttons.values():
            for direction in ("onleft", "onright", "onup", "ondown"):
                self.assertIn(button.findtext(direction), buttons)

        art = [
            node
            for node in page.findall(".//control[@type='image']")
            if node.findtext("width") == "366" and node.findtext("height") == "206"
        ]
        self.assertEqual(len(art), 4)
        for node in art:
            ratio = int(node.findtext("width")) / int(node.findtext("height"))
            self.assertAlmostEqual(ratio, 16 / 9, delta=0.02)
            self.assertEqual(node.find("texture").attrib.get("border"), "20")

        hero_art = [
            node
            for node in page.findall(".//control[@type='image']")
            if node.findtext("left") == "36" and node.findtext("width") == "390"
        ]
        self.assertEqual(len(hero_art), 1)
        self.assertNotIn("AsterYouTubeHeroArt", text)


if __name__ == "__main__":
    unittest.main()
