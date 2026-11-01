#!/usr/bin/env python3
"""Apply the definitive Gold Rim focus texture to visible AsterTV buttons."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


FOCUS_TEXTURE = "special://skin/media/ui-button-focus-gold-rim.png"
ART_TILE_INCLUDE = "AsterV3ArtTitleTile"
ART_TILE_DESCRIPTION = "AsterV3ArtTitleTile"
EXPECTED_BUTTONS = {
    "DialogAddonSettings.xml": 5,
    "DialogConfirm.xml": 3,
    "DialogContextMenu.xml": 1,
    "DialogKeyboard.xml": 45,
    "DialogSelect.xml": 1,
    "DialogSettings.xml": 4,
    "DialogVideoInfo.xml": 1,
    "Home.xml": 10,
    "IncludesBooks.xml": 6,
    "IncludesHub.xml": 8,
    "IncludesMusic.xml": 9,
    "MyMusicNav.xml": 6,
    "MyVideoNav.xml": 18,
    "Settings.xml": 9,
    "SettingsCategory.xml": 2,
    "SkinSettings.xml": 1,
    "VideoOSD.xml": 11,
    "custom_1111_digest.xml": 9,
    "custom_1112_home.xml": 11,
    "custom_1121_albumplayer.xml": 6,
    "custom_1122_breaking.xml": 4,
    "custom_1125_next_episode.xml": 2,
    "custom_1126_videoscrub.xml": 1,
    "custom_1127_search.xml": 5,
    "custom_1128_searchdetails.xml": 2,
    "custom_1129_artistalbums.xml": 2,
    "custom_1130_movie.xml": 3,
    "custom_1132_requests.xml": 6,
    "custom_1133_acquisition.xml": 4,
    "custom_1190_v3language.xml": 9,
    "custom_1191_youtube_rework.xml": 7,
    "custom_1192_tile_gallery.xml": 1,
    "custom_1193_button_gallery.xml": 15,
    "custom_1194_movie_rework.xml": 4,
    "custom_1195_person_library.xml": 1,
    "custom_1196_tv_rework.xml": 4,
}
EXPECTED_INCLUDE_DEFINITIONS = {
    "AsterCategoryButton",
    "AsterFilterButton",
    "AsterMusicPillButton",
    "AsterMusicSearchButton",
    "AsterPlayerControl",
    "AsterPlayerPrimaryControl",
    "AsterRailButton",
    "AsterV3MediaPill",
    "AsterV3MediaSearchPill",
    "AsterV3PrimaryAction",
    "AsterV3StateButton",
    "AsterV3TopPill",
}


def number(node: ET.Element, name: str) -> int:
    try:
        return int(node.findtext(name) or 0)
    except ValueError:
        return 0


def empty_texture(node: ET.Element | None) -> bool:
    return node is None or not (node.text or "").strip()


def include_names(button: ET.Element) -> set[str]:
    return {include.text for include in button.findall("include") if include.text}


def exclusion_reason(button: ET.Element) -> str | None:
    if ART_TILE_INCLUDE in include_names(button):
        return "art"
    if button.findtext("description") == ART_TILE_DESCRIPTION:
        return "art"
    focus = button.find("texturefocus")
    if (
        not (button.findtext("label") or "").strip()
        and focus is not None
        and focus.get("colordiffuse") == "asterSageGlass"
        and button.find("onclick") is None
    ):
        return "art"
    if (button.findtext("visible") or "").strip() == "false":
        return "hidden"
    width, height = number(button, "width"), number(button, "height")
    if 0 < width <= 2 and 0 < height <= 2:
        return "anchor"
    if (
        width >= 1000
        and height >= 500
        and empty_texture(button.find("texturefocus"))
        and empty_texture(button.find("texturenofocus"))
    ):
        return "catcher"
    return None


def set_focus_texture(parent: ET.Element) -> None:
    texture = parent.find("texturefocus")
    if texture is None:
        texture = ET.Element("texturefocus")
        nofocus = parent.find("texturenofocus")
        if nofocus is None:
            parent.append(texture)
        else:
            parent.insert(list(parent).index(nofocus), texture)
    texture.attrib.clear()
    texture.set("border", "20")
    texture.text = FOCUS_TEXTURE


def set_focused_color(parent: ET.Element) -> None:
    color = parent.find("focusedcolor")
    if color is None:
        color = ET.Element("focusedcolor")
        textcolor = parent.find("textcolor")
        if textcolor is None:
            parent.append(color)
        else:
            parent.insert(list(parent).index(textcolor) + 1, color)
    color.text = "asterIvory"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skin", type=Path)
    args = parser.parse_args()
    skin = args.skin.resolve()
    views = skin / "1080i"
    if not views.is_dir() or skin.name != "skin.asterhome.v3pilot":
        raise SystemExit(f"refusing unexpected skin path: {skin}")

    parsed: dict[Path, ET.ElementTree] = {}
    targets: dict[Path, list[ET.Element]] = {}
    skipped: Counter[str] = Counter()
    referenced_includes: set[str] = set()
    for path in sorted(views.glob("*.xml")):
        tree = ET.parse(path, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
        parsed[path] = tree
        file_targets = []
        for button in tree.getroot().iter("control"):
            if button.get("type") != "button":
                continue
            reason = exclusion_reason(button)
            if reason:
                skipped[reason] += 1
                continue
            file_targets.append(button)
            referenced_includes.update(include_names(button))
        if file_targets:
            targets[path] = file_targets

    inventory = {path.name: len(buttons) for path, buttons in targets.items()}
    if inventory != EXPECTED_BUTTONS:
        raise SystemExit(
            "button inventory changed: "
            f"expected {EXPECTED_BUTTONS}, found {inventory}"
        )

    include_definitions: dict[str, tuple[Path, ET.Element]] = {}
    for path, tree in parsed.items():
        for include in tree.getroot().iter("include"):
            name = include.get("name")
            if name in referenced_includes and include.find("texturefocus") is not None:
                include_definitions[name] = (path, include)
    found_definitions = set(include_definitions)
    if found_definitions != EXPECTED_INCLUDE_DEFINITIONS:
        raise SystemExit(
            "button include inventory changed: "
            f"expected {EXPECTED_INCLUDE_DEFINITIONS}, found {found_definitions}"
        )

    dirty: set[Path] = set()
    for path, buttons in targets.items():
        for button in buttons:
            set_focused_color(button)
            dirty.add(path)
            direct = button.find("texturefocus")
            inherited = include_names(button) & found_definitions
            if direct is not None or not inherited:
                set_focus_texture(button)
    for path, include in include_definitions.values():
        set_focus_texture(include)
        set_focused_color(include)
        dirty.add(path)

    for path in dirty:
        parsed[path].write(path, encoding="utf-8", xml_declaration=True)

    total = sum(inventory.values())
    print(f"Applied Gold Rim focus to {total} visible buttons")
    print(
        "Excluded "
        + ", ".join(f"{name}:{count}" for name, count in sorted(skipped.items()))
    )
    print(f"Patched {len(found_definitions)} shared button definitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
