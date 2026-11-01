#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import shutil
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
TILE_GALLERY = OVERLAY / "1080i/custom_1192_tile_gallery.xml"
BUTTON_GALLERY = OVERLAY / "1080i/custom_1193_button_gallery.xml"
MOVIE_PAGE = OVERLAY / "1080i/custom_1194_movie_rework.xml"
PERSON_PAGE = OVERLAY / "1080i/custom_1195_person_library.xml"
INCLUDES = OVERLAY / "1080i/IncludesV3.xml"
COLORS = OVERLAY / "colors/defaults.xml"
PATCH = V3 / "patches/001-load-v3-includes.patch"
ARCHIVE = ROOT / "services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
ART_TITLE_TRANSFORM = V3 / "apply_art_title_focus.py"
BUTTON_TRANSFORM = V3 / "apply_button_focus.py"
BUTTON_FOCUS = OVERLAY / "media/ui-button-focus-gold-rim.svg"
BUTTON_CURRENT = OVERLAY / "media/ui-button-current-gold-rim.svg"
BUTTON_FOCUS_PNG = OVERLAY / "media/ui-button-focus-gold-rim.png"
BUTTON_CURRENT_PNG = OVERLAY / "media/ui-button-current-gold-rim.png"


class SharedLanguageTests(unittest.TestCase):
    def test_xml_is_well_formed(self) -> None:
        for path in (
            PAGE,
            YOUTUBE_PAGE,
            TILE_GALLERY,
            BUTTON_GALLERY,
            MOVIE_PAGE,
            PERSON_PAGE,
            BUTTON_FOCUS,
            BUTTON_CURRENT,
            INCLUDES,
            COLORS,
            OVERLAY / "addon.xml",
        ):
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
        self.assertIn('<include content="AsterClockPill" />', text)
        self.assertIn('colordiffuse="asterCharcoalGlass"', text)
        self.assertIn('colordiffuse="asterPaperGlass"', text)
        self.assertNotIn('colordiffuse="66000000"', text)
        self.assertNotIn('colordiffuse="33000000"', text)
        self.assertNotIn("<include>AsterV3PageBackdrop</include>", text)

        includes = ET.parse(INCLUDES).getroot()
        art_title_tile = includes.find("include[@name='AsterV3ArtTitleTile']")
        self.assertIsNotNone(art_title_tile)
        self.assertGreaterEqual(int(art_title_tile.findtext("height", "0")), 294)
        self.assertEqual(art_title_tile.find("texturefocus").attrib["colordiffuse"], "asterSageGlass")
        self.assertEqual(
            art_title_tile.findtext("texturenofocus"),
            "special://skin/media/ui-transparent.svg",
        )
        self.assertEqual(text.count("<include>AsterV3ArtTitleTile</include>"), 4)
        self.assertNotIn("AsterV3YouTubeCard", text)

        for title in ("Aurora Station", "Rails Through Autumn", "Velvet Hour", "Living Light"):
            self.assertIn(f"<label>{title}</label>", text)

        buttons = {node.attrib["id"]: node for node in page.findall(".//control[@type='button']")}
        self.assertEqual(len(buttons), 11)
        for button_id, art_left in (
            ("11940", 117),
            ("11941", 532),
            ("11942", 947),
            ("11943", 1362),
        ):
            button = buttons[button_id]
            self.assertEqual(int(button.findtext("left")) + 4, art_left)
            self.assertEqual(int(button.findtext("top")) + 4, 597)
            self.assertEqual(int(button.findtext("width")), 366 + 8)
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
            self.assertEqual(
                node.find("texture").attrib.get("diffuse"),
                "special://skin/media/ui-compact-card-mask.png",
            )
            self.assertIn("special://skin/media/fixtures/youtube/", node.findtext("texture"))

        hero_art = [
            node
            for node in page.findall(".//control[@type='image']")
            if node.findtext("left") == "36" and node.findtext("width") == "390"
        ]
        self.assertEqual(len(hero_art), 1)
        self.assertNotIn("AsterYouTubeHeroArt", text)

    def test_tile_gallery_covers_shared_art_shapes_and_focus_graph(self) -> None:
        page = ET.parse(TILE_GALLERY).getroot()
        text = TILE_GALLERY.read_text()
        for mask in ("ui-compact-card-mask.png", "ui-album-mask.png", "ui-poster-mask.png"):
            self.assertIn(mask, text)
        buttons = {node.attrib["id"]: node for node in page.findall(".//control[@type='button']")}
        self.assertEqual(len(buttons), 5)
        expected_focus_geometry = {
            "11950": (82, 237, 396, 318),
            "11951": (537, 240, 296, 375),
            "11952": (899, 225, 246, 430),
            "11953": (1222, 239, 286, 326),
        }
        for button_id in ("11950", "11951", "11952", "11953"):
            button = buttons[button_id]
            self.assertEqual(
                button.findtext("texturenofocus"),
                "special://skin/media/ui-transparent.svg",
            )
            self.assertEqual(
                tuple(int(button.findtext(name)) for name in ("left", "top", "width", "height")),
                expected_focus_geometry[button_id],
            )
        for button in buttons.values():
            for direction in ("onleft", "onright", "onup", "ondown"):
                self.assertIn(button.findtext(direction), buttons)
        self.assertEqual(text.count('colordiffuse="asterSageGlass"'), 5)

    def test_art_title_transform_is_pinned_to_expected_layout_inventory(self) -> None:
        prefix = "aster-v2-package/lab-addon-snapshot/skin.asterhome/"
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            with tarfile.open(ARCHIVE, "r:gz") as archive:
                members = [member for member in archive.getmembers() if member.name.startswith(prefix)]
                archive.extractall(tmp, members=members)
            source = tmp / prefix
            skin = tmp / "skin.asterhome.v3pilot"
            shutil.move(source, skin)
            completed = subprocess.run(
                ["python3", str(ART_TITLE_TRANSFORM), str(skin)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("14 focused layouts", completed.stdout)
            surfaces = 0
            tight_surfaces = 0
            for path in (skin / "1080i").glob("*.xml"):
                root = ET.parse(path).getroot()
                for layout in root.iter("focusedlayout"):
                    for surface in layout.findall("control"):
                        texture = surface.find("texture")
                        if texture is None:
                            continue
                        if texture.attrib.get("colordiffuse") == "asterSageGlass":
                            surfaces += 1
                            if int(surface.findtext("left", "0")) > 0 or int(surface.findtext("top", "0")) > 0:
                                tight_surfaces += 1
            self.assertEqual(surfaces, 14)
            self.assertGreaterEqual(tight_surfaces, 8)

    def test_button_gallery_covers_definitive_gold_rim_states(self) -> None:
        page = ET.parse(BUTTON_GALLERY).getroot()
        text = BUTTON_GALLERY.read_text()
        buttons = {node.attrib["id"]: node for node in page.findall(".//control[@type='button']")}
        self.assertEqual(len(buttons), 15)
        self.assertEqual(page.findtext("defaultcontrol"), "11962")
        for button in buttons.values():
            for direction in ("onleft", "onright", "onup", "ondown"):
                self.assertIn(button.findtext(direction), buttons)
        self.assertIn("ui-button-current-gold-rim.png", text)
        self.assertIn("#AD8A4D", text)
        self.assertNotIn("#D7B45F", text.upper())

        for path in (BUTTON_FOCUS, BUTTON_CURRENT):
            svg = path.read_text().lower()
            self.assertIn("#ad8a4d", svg)
            self.assertNotIn("#d7b45f", svg)
        self.assertIn("#1f513b", BUTTON_FOCUS.read_text().lower())
        self.assertTrue(BUTTON_FOCUS_PNG.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(BUTTON_CURRENT_PNG.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(
            hashlib.sha256(BUTTON_FOCUS_PNG.read_bytes()).hexdigest(),
            "c1de42c5d178eeb0c2136781f891c9543fea78a9a41c4a084a78d8fbc86f214f",
        )
        self.assertEqual(
            hashlib.sha256(BUTTON_CURRENT_PNG.read_bytes()).hexdigest(),
            "cbaf368d835e864e68ba816c9184350d59a9c0a861e1de9b6e8e03b6bb955925",
        )

    def test_button_transform_is_guarded_and_preserves_art_contract(self) -> None:
        prefix = "aster-v2-package/lab-addon-snapshot/skin.asterhome/"
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            with tarfile.open(ARCHIVE, "r:gz") as archive:
                members = [member for member in archive.getmembers() if member.name.startswith(prefix)]
                archive.extractall(tmp, members=members)
            source = tmp / prefix
            skin = tmp / "skin.asterhome.v3pilot"
            shutil.move(source, skin)
            shutil.copytree(OVERLAY, skin, dirs_exist_ok=True)
            patched = subprocess.run(
                ["patch", "-d", str(skin), "-p1", "-i", str(PATCH)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(patched.returncode, 0, patched.stdout + patched.stderr)
            art = subprocess.run(
                ["python3", str(ART_TITLE_TRANSFORM), str(skin)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(art.returncode, 0, art.stdout + art.stderr)
            completed = subprocess.run(
                ["python3", str(BUTTON_TRANSFORM), str(skin)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("231 visible buttons", completed.stdout)
            self.assertIn("anchor:1, art:8, catcher:2, hidden:4", completed.stdout)
            self.assertIn("12 shared button definitions", completed.stdout)

            focus_refs = 0
            for path in (skin / "1080i").glob("*.xml"):
                root = ET.parse(path).getroot()
                for node in root.iter("texturefocus"):
                    if (node.text or "").strip() != (
                        "special://skin/media/ui-button-focus-gold-rim.png"
                    ):
                        continue
                    self.assertEqual(node.attrib.get("border"), "20")
                    focus_refs += 1
            self.assertEqual(focus_refs, 205)

            tile = ET.parse(skin / "1080i/custom_1192_tile_gallery.xml").getroot()
            art_buttons = {
                node.attrib["id"]: node
                for node in tile.findall(".//control[@type='button']")
            }
            for button_id in ("11950", "11951", "11952", "11953"):
                focus = art_buttons[button_id].find("texturefocus")
                self.assertEqual(focus.attrib.get("colordiffuse"), "asterSageGlass")
                self.assertEqual(focus.text, "special://skin/media/ui-panel.png")

            for fixture in (
                "custom_1190_v3language.xml",
                "custom_1191_youtube_rework.xml",
                "custom_1193_button_gallery.xml",
            ):
                root = ET.parse(skin / "1080i" / fixture).getroot()
                for button in root.findall(".//control[@type='button']"):
                    if button.findtext("description") == "AsterV3ArtTitleTile":
                        continue
                    if "AsterV3ArtTitleTile" in {
                        node.text for node in button.findall("include")
                    }:
                        continue
                    self.assertEqual(button.findtext("focusedcolor"), "asterIvory")

    def test_movie_rework_uses_the_locked_layout_and_person_flow(self) -> None:
        movie = ET.parse(MOVIE_PAGE).getroot()
        person = ET.parse(PERSON_PAGE).getroot()
        movie_text = MOVIE_PAGE.read_text()
        person_text = PERSON_PAGE.read_text()

        self.assertNotIn("AsterClockPill", movie_text)
        self.assertNotIn("<label>Clock</label>", movie_text)
        logo = next(
            node
            for node in movie.findall(".//control[@type='image']")
            if node.findtext("texture") == "special://skin/media/27-aster-media-logo.png"
        )
        self.assertGreaterEqual(int(logo.findtext("height")), 190)
        self.assertGreaterEqual(int(logo.findtext("width")), 280)

        buttons = {
            node.attrib["id"]: node
            for node in movie.findall(".//control[@type='button']")
        }
        self.assertEqual(set(buttons), {"200", "201", "202"})
        self.assertEqual(buttons["200"].findtext("label"), "")
        self.assertEqual(buttons["201"].findtext("label"), "")
        self.assertIn("player-controls/play.png", movie_text)
        self.assertIn("player-controls/forward.png", movie_text)
        self.assertNotIn("<font>font14</font>", movie_text)

        cast = movie.find(".//control[@type='list'][@id='500']")
        related = movie.find(".//control[@type='list'][@id='501']")
        self.assertIsNotNone(cast)
        self.assertIsNotNone(related)
        cast_art = cast.find("itemlayout/control[@type='image']")
        related_art = related.find("itemlayout/control[@type='image']")
        self.assertLess(
            int(cast_art.findtext("width")) / int(cast_art.findtext("height")),
            1,
        )
        self.assertGreater(
            int(related_art.findtext("width")) / int(related_art.findtext("height")),
            1.8,
        )
        self.assertEqual(cast.findtext("onclick"), "ActivateWindow(1195)")

        self.assertIn("current Jellyfin user", person_text)
        self.assertIn("<label>Films</label>", person_text)
        self.assertIn("<label>Television</label>", person_text)
        self.assertEqual(person.findtext("defaultcontrol"), "600")
        person_lists = {
            node.attrib["id"]: node
            for node in person.findall(".//control[@type='list']")
        }
        self.assertEqual(set(person_lists), {"600", "601"})
        for control in person_lists.values():
            for direction in ("onleft", "onright", "onup", "ondown"):
                self.assertIn(control.findtext(direction), {"600", "601", "602"})


if __name__ == "__main__":
    unittest.main()
