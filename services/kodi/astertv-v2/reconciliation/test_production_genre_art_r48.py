#!/usr/bin/env python3
"""Pin the full-colour Aster Genre tile treatment and its existing behaviour."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
INCLUDES = HERE / "payload/skin.asterhome/1080i/Includes.xml"
root = ET.parse(INCLUDES).getroot()
include = root.find("./include[@name='AsterGenreTile']")
assert include is not None
panel = include.find("./definition/control[@type='panel']")
assert panel is not None

# Navigation, activation and data routes are deliberately unchanged.
expected = {
    "left": "$PARAM[left]",
    "onleft": "$PARAM[lefttarget]",
    "onright": "$PARAM[righttarget]",
    "onup": "$PARAM[uptarget]",
    "ondown": "$PARAM[id]",
    "onclick": "ActivateWindow(Videos,$PARAM[browse],return)",
}
for name, value in expected.items():
    assert panel.findtext(name) == value, name
assert panel.attrib["id"] == "$PARAM[id]"
content = panel.find("content")
assert content is not None and content.attrib["target"] == "videos"
assert content.text == "$PARAM[preview]"

item = panel.find("itemlayout")
focused = panel.find("focusedlayout")
assert item is not None and focused is not None
for layout, ring_colour in ((item, "asterSage"), (focused, "asterGold")):
    images = layout.findall("control[@type='image']")
    assert len(images) == 2
    art, ring = images
    art_texture = art.find("texture")
    assert art_texture is not None
    assert art_texture.text == "$VAR[AsterPosterArt]"
    assert "colordiffuse" not in art_texture.attrib
    assert art_texture.attrib["diffuse"] == "special://skin/media/ui-poster-mask.png"
    ring_texture = ring.find("texture")
    assert ring_texture is not None
    assert ring_texture.text == "special://skin/media/ui-poster-ring.png"
    assert ring_texture.attrib["colordiffuse"] == ring_colour
    label = layout.find("control[@type='label']")
    assert label is not None
    assert label.findtext("label") == "$PARAM[label]"
    assert label.findtext("top") == "330"
    assert label.findtext("textcolor") == "asterInk"
    assert label.findtext("align") == "left"
    assert label.findtext("truncate") == "true"

genre_xml = ET.tostring(include, encoding="unicode")
assert "48f2ede4" not in genre_xml
assert "d029302b" not in genre_xml and "f029302b" not in genre_xml
print("Genre gate passed: full-colour art, sage/gold edge, names below art and routes pinned")
