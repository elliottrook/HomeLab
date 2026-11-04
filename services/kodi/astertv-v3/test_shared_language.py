#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
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
TV_PAGE = OVERLAY / "1080i/custom_1196_tv_rework.xml"
AI_PAGE = OVERLAY / "1080i/custom_1197_aster_ai.xml"
AI_KEYWORD_PAGE = OVERLAY / "1080i/custom_1202_aster_ai_keyword.xml"
NEWS_PAGE = OVERLAY / "1080i/custom_1198_news_rework.xml"
PODCAST_PAGE = OVERLAY / "1080i/custom_1199_podcast_requests.xml"
HOME_PAGE = OVERLAY / "1080i/custom_1200_home_rework.xml"
CAMERAS_PAGE = OVERLAY / "1080i/custom_1201_cameras_rework.xml"
ACTOR_PLUGIN = V3 / "overlay/plugin.video.astersearch"
ACTOR_SEARCH = ACTOR_PLUGIN / "actor_search.py"
INCLUDES = OVERLAY / "1080i/IncludesV3.xml"
COLORS = OVERLAY / "colors/defaults.xml"
PATCH = V3 / "patches/001-load-v3-includes.patch"
ACTOR_HEADING_PATCH = V3 / "patches/002-actor-search-heading.patch"
ACTOR_VISUALS_PATCH = V3 / "patches/003-actor-search-visuals.patch"
ARCHIVE = ROOT / "services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
ART_TITLE_TRANSFORM = V3 / "apply_art_title_focus.py"
BUTTON_TRANSFORM = V3 / "apply_button_focus.py"
BUTTON_FOCUS = OVERLAY / "media/ui-button-focus-gold-rim.svg"
BUTTON_CURRENT = OVERLAY / "media/ui-button-current-gold-rim.svg"
BUTTON_FOCUS_PNG = OVERLAY / "media/ui-button-focus-gold-rim.png"
BUTTON_CURRENT_PNG = OVERLAY / "media/ui-button-current-gold-rim.png"
TRAILER_ROUTE = V3 / "jellyfin_trailer_route.py"


class SharedLanguageTests(unittest.TestCase):
    def test_xml_is_well_formed(self) -> None:
        for path in (
            PAGE,
            YOUTUBE_PAGE,
            TILE_GALLERY,
            BUTTON_GALLERY,
            MOVIE_PAGE,
            PERSON_PAGE,
            TV_PAGE,
            AI_PAGE,
            AI_KEYWORD_PAGE,
            NEWS_PAGE,
            PODCAST_PAGE,
            HOME_PAGE,
            CAMERAS_PAGE,
            BUTTON_FOCUS,
            BUTTON_CURRENT,
            INCLUDES,
            COLORS,
            OVERLAY / "addon.xml",
            ACTOR_PLUGIN / "addon.xml",
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

    def test_actor_result_patches_apply_in_order_to_immutable_v2_baseline(self) -> None:
        prefix = "aster-v2-package/lab-addon-snapshot/skin.asterhome/"
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            with tarfile.open(ARCHIVE, "r:gz") as archive:
                members = [member for member in archive.getmembers() if member.name.startswith(prefix)]
                archive.extractall(tmp, members=members)
            skin = tmp / prefix
            for patch_path in (ACTOR_HEADING_PATCH, ACTOR_VISUALS_PATCH):
                completed = subprocess.run(
                    ["patch", "-d", str(skin), "-p1", "-i", str(patch_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    f"{patch_path.name}: {completed.stdout}{completed.stderr}",
                )

            nav = ET.parse(skin / "1080i/MyVideoNav.xml").getroot()
            nav_text = (skin / "1080i/MyVideoNav.xml").read_text()
            self.assertGreaterEqual(nav_text.count("<height>1080</height>"), 3)
            self.assertIn("plugin.video.astersearch", nav_text)
            self.assertIn("colordiffuse=\"99000000\"", nav_text)
            self.assertIn("ui-hero-bottom-fade.png", nav_text)
            self.assertEqual(nav.tag, "window")
            plot = next(
                node
                for node in nav.findall(".//control[@type='label']")
                if node.findtext("label") == "$VAR[AsterBrowsePlot]"
            )
            score = next(
                node
                for node in nav.findall(".//control[@type='label']")
                if "Score:" in node.findtext("label", "")
            )
            action = nav.find(".//control[@type='button'][@id='9100']")
            self.assertIsNotNone(action)
            self.assertLessEqual(
                int(plot.findtext("top")) + int(plot.findtext("height")),
                int(score.findtext("top")),
            )
            self.assertLessEqual(
                int(score.findtext("top")) + int(score.findtext("height")),
                int(action.findtext("top")),
            )
            self.assertLess(
                int(action.findtext("top")) + int(action.findtext("height")),
                492,
            )

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
            self.assertIn("293 visible buttons", completed.stdout)
            self.assertIn("anchor:1, art:11, catcher:2, hidden:4", completed.stdout)
            self.assertIn("14 shared button definitions", completed.stdout)

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
            self.assertEqual(focus_refs, 212)

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
                    if {node.text for node in button.findall("include")} & {
                        "AsterV3MediaPill",
                        "AsterV3MediaSearchPill",
                    }:
                        self.assertNotEqual(button.findtext("focusedcolor"), "asterIvory")
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
        self.assertEqual(set(buttons), {"200", "201", "202", "203"})
        self.assertEqual(buttons["200"].findtext("label"), "")
        self.assertEqual(buttons["201"].findtext("label"), "")
        self.assertEqual(buttons["200"].findtext("onleft"), "500")
        self.assertIn("player-controls/play.png", movie_text)
        self.assertIn("player-controls/forward.png", movie_text)
        self.assertIn("player-controls/trailer.png", movie_text)
        self.assertIn("<label>Trailer</label>", movie_text)
        self.assertNotIn("<font>font14</font>", movie_text)

        cast = movie.find(".//control[@type='list'][@id='500']")
        related = movie.find(".//control[@type='list'][@id='501']")
        self.assertIsNotNone(cast)
        self.assertIsNotNone(related)
        self.assertEqual(cast.findtext("onright"), "200")
        cast_art = cast.find("itemlayout/control[@type='image']")
        related_art = related.find("itemlayout/control[@type='image']")
        self.assertLess(
            int(cast_art.findtext("width")) / int(cast_art.findtext("height")),
            1,
        )
        self.assertGreaterEqual(int(cast_art.findtext("height")), 160)
        self.assertAlmostEqual(
            int(related_art.findtext("width")) / int(related_art.findtext("height")),
            16 / 9,
            delta=0.08,
        )
        self.assertGreaterEqual(int(related_art.findtext("width")), 250)
        poster = next(
            node
            for node in movie.findall(".//control[@type='image']")
            if "ui-poster-mask.png"
            in ((node.find("texture").attrib.get("diffuse", "")) if node.find("texture") is not None else "")
            and node.findtext("left") == "1450"
        )
        self.assertEqual(
            int(poster.findtext("width")) / int(poster.findtext("height")),
            2 / 3,
        )
        poster_left = int(poster.findtext("left"))
        poster_right = poster_left + int(poster.findtext("width"))
        for control_id in ("200", "201", "203"):
            control = buttons[control_id]
            self.assertGreaterEqual(int(control.findtext("left")), poster_left)
            self.assertLessEqual(
                int(control.findtext("left")) + int(control.findtext("width")),
                poster_right,
            )
            self.assertGreaterEqual(int(control.findtext("top")), 665)
        synopsis = next(
            node
            for node in movie.findall(".//control[@type='textbox']")
            if "lone researcher" in node.findtext("label", "")
        )
        self.assertGreaterEqual(int(synopsis.findtext("top")), 370)
        self.assertLess(int(cast.findtext("top")), 655)
        self.assertLess(int(related.findtext("top")), 895)
        self.assertGreaterEqual(
            int(related.findtext("top"))
            - (int(cast.findtext("top")) + int(cast.findtext("height"))),
            50,
        )
        for icon in ("play.png", "forward.png", "trailer.png"):
            control = next(
                node
                for node in movie.findall(".//control[@type='image']")
                if node.findtext("texture", "").endswith(icon)
            )
            self.assertEqual(control.find("texture").attrib.get("colordiffuse"), "asterInk")
        self.assertIsNone(cast.find("onclick"))
        cast_items = cast.findall("content/item")
        self.assertGreaterEqual(len(cast_items), 4)
        for item in cast_items:
            action = item.findtext("onclick", "")
            self.assertIn("plugin://plugin.video.astersearch/", action)
            self.assertIn("actor=", action)
        item_name = cast.find("itemlayout/control[@type='label']")
        focused_name = cast.find("focusedlayout/control[@type='label']")
        self.assertEqual(int(item_name.findtext("width")), int(cast_art.findtext("width")))
        self.assertEqual(int(focused_name.findtext("width")), int(cast_art.findtext("width")))
        self.assertEqual(item_name.findtext("truncate"), "true")
        self.assertEqual(focused_name.findtext("scroll"), "true")
        self.assertEqual(focused_name.findtext("scrollout"), "false")
        for rail in (cast, related):
            self.assertLessEqual(
                int(rail.findtext("top")) + int(rail.findtext("height")), 1080
            )
            for layout_name in ("itemlayout", "focusedlayout"):
                layout = rail.find(layout_name)
                layout_height = int(layout.attrib["height"])
                for label in layout.findall("control[@type='label']"):
                    self.assertLessEqual(
                        int(label.findtext("top")) + int(label.findtext("height")),
                        layout_height,
                    )

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

    def test_actor_search_is_read_only_bounded_and_validated(self) -> None:
        spec = importlib.util.spec_from_file_location("aster_actor_search", ACTOR_SEARCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.clean_actor("  Keegan-Michael   Key  "), "Keegan-Michael Key")
        for value in ("", "   ", "bad\nname", "x" * 129):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.clean_actor(value)

        source = (ACTOR_PLUGIN / "default.py").read_text()
        compile(source, str(ACTOR_PLUGIN / "default.py"), "exec")
        self.assertIn('"field": "actor"', source)
        self.assertIn('"operator": "is"', source)
        self.assertIn('"VideoLibrary.GetMovies"', source)
        self.assertIn('"VideoLibrary.GetTVShows"', source)
        self.assertIn('"end": 500', source)
        self.assertIn("Movie and TV credits available on AsterTV", source)
        self.assertIn("TVSHOW_PROPERTIES = BASE_PROPERTIES", source)
        self.assertNotIn('TVSHOW_PROPERTIES = BASE_PROPERTIES + ["resume"]', source)
        for mutation in ("SetMovieDetails", "SetTVShowDetails", "RemoveMovie", "RemoveTVShow"):
            self.assertNotIn(mutation, source)
        skin_requires = {
            node.attrib["addon"]
            for node in ET.parse(OVERLAY / "addon.xml").getroot().findall("requires/import")
        }
        self.assertIn("plugin.video.astersearch", skin_requires)
        heading_patch = ACTOR_HEADING_PATCH.read_text()
        self.assertIn("plugin.video.astersearch", heading_patch)
        self.assertIn("Container.PluginCategory", heading_patch)
        self.assertIn("<font>font30</font>", heading_patch)
        visuals_patch = ACTOR_VISUALS_PATCH.read_text()
        self.assertIn("<height>1080</height>", visuals_patch)
        self.assertIn("ui-hero-left-fade.png", visuals_patch)
        self.assertIn("ui-hero-bottom-fade.png", visuals_patch)
        self.assertIn("colordiffuse=\"99000000\"", visuals_patch)
        self.assertIn("!String.Contains(Container.FolderPath,plugin.video.astersearch)", visuals_patch)

    def test_movie_and_tv_trailer_lookup_is_bounded_and_strict(self) -> None:
        spec = importlib.util.spec_from_file_location("aster_trailer_route", TRAILER_ROUTE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        movie_method, movie_params, movie_key = module.kodi_trailer_lookup_request(
            "movie", "  Buddy  "
        )
        tv_method, tv_params, tv_key = module.kodi_trailer_lookup_request(
            "tvshow", "Aurora Station"
        )
        self.assertEqual((movie_method, movie_key), ("VideoLibrary.GetMovies", "movies"))
        self.assertEqual((tv_method, tv_key), ("VideoLibrary.GetTVShows", "tvshows"))
        self.assertEqual(movie_params["filter"]["value"], "Buddy")
        self.assertEqual(tv_params["filter"]["value"], "Aurora Station")
        self.assertEqual(movie_params["limits"], {"start": 0, "end": 2})
        for bad_type, bad_title in (
            ("episode", "Pilot"),
            ("movie", ""),
            ("tvshow", "bad\nname"),
            ("tvshow", "x" * 257),
        ):
            with self.subTest(bad_type=bad_type, bad_title=bad_title), self.assertRaises(ValueError):
                module.kodi_trailer_lookup_request(bad_type, bad_title)

        safe = "plugin://plugin.video.youtube/play/?video_id=dQw4w9WgXcQ"
        self.assertEqual(
            module.trailer_from_kodi_result(
                {"tvshows": [{"title": "Aurora Station", "trailer": safe}]},
                "tvshows",
            ),
            safe,
        )
        for result in (
            {},
            {"tvshows": []},
            {"tvshows": [{"trailer": safe}, {"trailer": safe}]},
            {"tvshows": [{"trailer": "https://example.invalid/trailer"}]},
        ):
            self.assertIsNone(module.trailer_from_kodi_result(result, "tvshows"))

    def test_tv_rework_has_remote_safe_seasons_episodes_and_watch_markers(self) -> None:
        page = ET.parse(TV_PAGE).getroot()
        text = TV_PAGE.read_text()
        self.assertEqual(page.findtext("defaultcontrol"), "600")
        self.assertNotIn("<label>Seasons</label>", text)
        for season in range(1, 11):
            self.assertIn(f"<item><label>$NUMBER[{season}]</label>", text)
            self.assertNotIn(
                f"<item><label>{season}</label>",
                text,
                "bare numeric labels resolve to Kodi localization strings, not numbers",
            )
        self.assertIn("Play next", text)
        self.assertIn("Resume", text)
        self.assertIn("ui-button-focus-gold-rim.png", text)
        self.assertIn("asterSageGlass", text)
        self.assertIn("ListItem.Property(Watched)", text)
        self.assertIn("✓", text)
        self.assertIn("ui-timer-dot.png", text)
        self.assertIn("ui-compact-card-mask.png", text)

        controls = {
            node.attrib["id"]: node
            for node in page.findall(".//control[@id]")
            if node.attrib.get("id") in {"600", "602", "603", "604", "605", "610", "611", "612"}
        }
        self.assertEqual(set(controls), {"600", "602", "603", "604", "605", "610", "611", "612"})
        for control in controls.values():
            for direction in ("onleft", "onright", "onup", "ondown"):
                self.assertIn(control.findtext(direction), controls)

        episodes = controls["600"]
        self.assertEqual(episodes.findtext("orientation"), "vertical")
        self.assertEqual(episodes.findtext("width"), "740")
        self.assertGreaterEqual(len(episodes.findall("content/item")), 5)
        focused = episodes.find("focusedlayout")
        self.assertIsNotNone(focused)
        focus_panel = focused.find("control[@type='image']/texture")
        self.assertEqual(focus_panel.attrib.get("colordiffuse"), "asterSageGlass")
        seasons = controls["612"]
        self.assertEqual(seasons.findtext("orientation"), "vertical")
        self.assertEqual(seasons.findtext("left"), "954")
        self.assertEqual(seasons.findtext("top"), "288")
        self.assertEqual(seasons.findtext("width"), "50")
        self.assertEqual(seasons.findtext("height"), "704")
        self.assertEqual(
            int(seasons.findtext("height"))
            // int(seasons.find("itemlayout").attrib["height"]),
            8,
        )
        self.assertEqual(len(seasons.findall("content/item")), 10)
        self.assertEqual(seasons.findtext("scrolltime"), "180")
        self.assertEqual(seasons.findtext("onleft"), "610")
        self.assertEqual(seasons.findtext("onright"), "600")
        self.assertNotIn("Now highlighted", text)
        self.assertNotIn("Container(600).ListItem.Property(Plot)", text)
        self.assertIn("Cast &amp; Crew", text)
        self.assertIn("More Like This", text)
        self.assertIn("!Control.HasFocus(612)", text)
        self.assertIn("Control.HasFocus(612)", text)
        self.assertIn("Control.HasFocus(610)", text)
        self.assertIn("Control.HasFocus(611)", text)
        self.assertIn("player-controls/trailer.png", text)
        self.assertIn("<label>Trailer</label>", text)
        trailer_action = controls["605"].findtext("onclick", "")
        self.assertIn("pilot_jellyfin_trailer_smoke.py", trailer_action)
        self.assertIn("tvshow", trailer_action)

    def test_pa3_fixtures_are_synthetic_local_and_remote_safe(self) -> None:
        include_root = ET.parse(INCLUDES).getroot()
        include_heights = {
            node.attrib["name"]: int(node.findtext("height", "0"))
            for node in include_root.findall("include")
        }
        for path in (AI_PAGE, AI_KEYWORD_PAGE, NEWS_PAGE, PODCAST_PAGE, HOME_PAGE, CAMERAS_PAGE):
            with self.subTest(path=path):
                text = path.read_text()
                self.assertIn("Synthetic", text)
                for forbidden in ("http://", "https://", "plugin://", "RunScript("):
                    self.assertNotIn(forbidden, text)
                page = ET.parse(path).getroot()
                buttons = {
                    node.attrib["id"]: node
                    for node in page.findall(".//control[@type='button']")
                }
                self.assertTrue(buttons)
                for button in buttons.values():
                    include_name = button.findtext("include")
                    height = int(button.findtext("height", "0"))
                    if not height and include_name:
                        height = include_heights[include_name]
                    self.assertGreaterEqual(height, 44)
                    for direction in ("onleft", "onright", "onup", "ondown"):
                        self.assertIn(button.findtext(direction), buttons)

    def test_pa3_aster_ai_is_a_global_media_search_dialog(self) -> None:
        page = ET.parse(AI_PAGE).getroot()
        text = AI_PAGE.read_text()
        self.assertEqual(page.attrib.get("type"), "dialog")
        self.assertEqual(page.findtext("backgroundcolor"), "00000000")
        self.assertNotIn("AsterV3PageBackdrop", text)
        for label in (
            "●  Listening…",
            "YOU SAID",
            "“Find me a light comedy film.”",
            "I found three matches on AsterTV",
            "Search again",
            "Keyword view",
            "View all results",
            "Close",
        ):
            self.assertIn(f"<label>{label}</label>", text)
        self.assertEqual(text.count("<include>AsterV3ArtTitleTile</include>"), 3)
        self.assertIn("<onclick>ActivateWindow(1127)</onclick>", text)
        self.assertEqual(text.count("<onclick>Dialog.Close(1197)</onclick>"), 6)
        for control_id in ("11970", "11971", "11972", "11974", "11977"):
            action = page.find(f".//control[@id='{control_id}']")
            self.assertEqual(
                [node.text for node in action.findall("onclick")],
                [
                    "Dialog.Close(1197)",
                    "ActivateWindow(1127)" if control_id == "11974" else
                    "ActivateWindow(1202)" if control_id == "11977" else
                    "ActivateWindow(1194)",
                ],
            )
        self.assertEqual(text.count("<include>AsterV3DialogPill</include>"), 5)
        self.assertIn('colordiffuse="d0292721"', text)
        self.assertIn("returns to the page underneath", text)
        self.assertIn("no microphone or search service connected", text)

    def test_pa3_aster_ai_keyword_view_groups_art_results_by_media_type(self) -> None:
        page = ET.parse(AI_KEYWORD_PAGE).getroot()
        text = AI_KEYWORD_PAGE.read_text()
        self.assertEqual(page.attrib.get("type"), "dialog")
        self.assertEqual(page.findtext("backgroundcolor"), "00000000")
        for label in ("TV SHOWS", "MOVIES", "BOOKS &amp; LISTENING", "MUSIC"):
            self.assertIn(f"<label>{label}</label>", text)
        self.assertIn("“Show me anything about space.”", text)
        self.assertEqual(text.count("<include>AsterV3DialogResult</include>"), 12)
        self.assertGreaterEqual(text.count("ui-compact-card-mask.png"), 12)
        self.assertGreaterEqual(text.count("<include>AsterV3DialogPill</include>"), 8)
        self.assertIn('colordiffuse="d0292721"', text)
        self.assertIn("<label>More TV shows</label>", text)
        self.assertIn("<label>More movies</label>", text)
        self.assertNotIn("More TV &amp; movie results", text)
        for window in (1194, 1196, 1197, 1127):
            self.assertIn(f"<onclick>ActivateWindow({window})</onclick>", text)

    def test_pa3_news_preserves_digest_article_and_narration_contracts(self) -> None:
        text = NEWS_PAGE.read_text()
        for label in ("Search", "Daily Digest", "Breaking", "Sections", "Back", "Read", "Play from beginning"):
            self.assertIn(f"<label>{label}</label>", text)
        self.assertGreaterEqual(text.count("aster-compass-128.png"), 4)
        self.assertIn("30-aster-news-logo.png", text)
        self.assertIn("04-news-digest.png", text)
        self.assertIn("$INFO[System.Time(HH:mm)]", text)
        self.assertIn("existing digest and article runtime routes remain untouched", text)

    def test_pa3_podcast_request_flow_is_explicit_and_inert(self) -> None:
        page = ET.parse(PODCAST_PAGE).getroot()
        text = PODCAST_PAGE.read_text()
        for status in ("Available now", "Already followed", "Request needed", "Not in your library"):
            self.assertIn(status, text)
        for label in ("Search", "Discover", "Following", "Requests", "Back"):
            self.assertIn(f"<label>{label}</label>", text)
        self.assertGreaterEqual(text.count("aster-compass-128.png"), 5)
        request = page.find(".//control[@type='button'][label='Request podcast']")
        self.assertIsNotNone(request)
        self.assertIsNone(request.find("onclick"))
        self.assertIn("no request sent", text)

    def test_pa3_home_and_cameras_cover_freshness_and_failure_states(self) -> None:
        home = HOME_PAGE.read_text()
        cameras = CAMERAS_PAGE.read_text()
        self.assertIn("ActivateWindow(1201)", home)
        for state in ("Fresh", "Stale", "Unavailable", "Door event"):
            self.assertIn(state, cameras)
        self.assertIn("no live Home Assistant data", home)
        self.assertIn("no live imagery", cameras)
        self.assertNotIn("background=\"true\"", cameras)
        camera_page = ET.parse(CAMERAS_PAGE).getroot()
        self.assertEqual(camera_page.findtext("defaultcontrol"), "12102")
        self.assertEqual(
            camera_page.find(".//control[@id='12100']").findtext("ondown"),
            "12102",
        )
        self.assertEqual(
            camera_page.find(".//control[@id='12101']").findtext("ondown"),
            "12103",
        )

    def test_pa3_primary_actions_use_the_locked_gold_rim_rest_contract(self) -> None:
        includes = ET.parse(INCLUDES).getroot()
        action = includes.find("include[@name='AsterV3PrimaryAction']")
        self.assertIsNotNone(action)
        self.assertEqual(action.findtext("textcolor"), "asterV3Text")
        self.assertEqual(action.findtext("focusedcolor"), "asterV3Text")
        self.assertEqual(
            action.find("texturenofocus").attrib.get("colordiffuse"),
            "asterV3Panel",
        )
        self.assertEqual(
            action.find("texturefocus").attrib.get("colordiffuse"),
            "asterV3Focus",
        )

    def test_pa3_keymap_is_bounded_to_the_five_fixture_pages(self) -> None:
        keymap = ET.parse(V3 / "pilot/keymaps/astertv-v3-pilot.xml").getroot()
        keyboard = keymap.find("global/keyboard")
        self.assertIsNotNone(keyboard)
        self.assertEqual(
            {keyboard.findtext(f"f{index}") for index in range(1, 6)},
            {f"ActivateWindow({window})" for window in range(1197, 1202)},
        )


if __name__ == "__main__":
    unittest.main()
