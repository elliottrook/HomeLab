#!/usr/bin/env python3
"""Guard the bounded AsterTV media-art screensaver contract."""
from __future__ import annotations

import ast
from pathlib import Path
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
PAYLOAD = HERE / "payload/screensaver.asterhome.v2lab"
SOURCE = (PAYLOAD / "default.py").read_text()
tree = ast.parse(SOURCE)


def assigned_tuple(name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            assert isinstance(value, tuple)
            return value
    raise AssertionError(name)


assert assigned_tuple("SOURCES") == (
    "special://skin/playlists/tv-shows.xsp",
    "special://skin/playlists/movies.xsp",
    "special://skin/playlists/archive-tv.xsp",
    "special://skin/playlists/archive-film.xsp",
)
assert assigned_tuple("ART_PRIORITY") == ("fanart", "landscape", "thumb", "poster")
for guard in (
    '("AsterTV-Family", "AsterTV-Bedroom")',
    'getCondVisibility("Player.HasMedia")',
    '"HomeTimerActive", "HomeTimerExpired"',
    'selected.get("value") != IDENTITY',
    "source_index % len(available)",
    "chooser.randrange(total)",
    'image.setImage(art, True)',
    "CHANGE_SECONDS = 18",
):
    assert guard in SOURCE, guard
for forbidden in ("PlayMedia", "Player.Open", "urllib", "requests", "CameraImage"):
    assert forbidden not in SOURCE, forbidden

xml = ET.parse(PAYLOAD / "resources/skins/Default/1080i/AsterIdle.xml").getroot()
art = xml.find("./controls/control[@type='image'][@id='10']")
logo = xml.find("./controls/control[@type='image'][@id='11']")
assert art is not None and logo is not None
assert [art.findtext(name) for name in ("left", "top", "width", "height")] == [
    "0", "0", "1920", "1080"]
assert art.findtext("aspectratio") == "scale"
assert int(logo.findtext("left")) >= 1600 and int(logo.findtext("top")) >= 850
assert logo.find("texture").text.endswith("/resources/mark.png")

addon = ET.parse(PAYLOAD / "addon.xml").getroot()
assert addon.attrib["id"] == "screensaver.asterhome.v2lab"
assert addon.attrib["version"] == "0.2.0"

wish = (HERE.parents[1] / "ASTER-TV-V3-WISHLIST.md").read_text()
assert "multiple Aster idle presentations" in wish
assert "Music presentation" in wish

print("r50 media screensaver gate passed: four balanced sources, art priority, logo and safety guards pinned")
