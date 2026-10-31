#!/usr/bin/env python3
"""Prevent AsterTV's native Resume prompt from regressing to a generic Kodi dialog."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESUME = HERE / "payload/skin.asterhome/1080i/DialogContextMenu.xml"


def text(node: ET.Element, path: str) -> str:
    value = node.findtext(path)
    assert value is not None, path
    return value


root = ET.parse(RESUME).getroot()
group = root.find("./controls/control[@type='group']")
assert group is not None

# Exact Aster Skip Intro/Recap popup footprint and canvas treatment.
assert text(group, "left") == "1120"
assert text(group, "top") == "825"
assert text(group, "width") == "730"
assert text(group, "height") == "205"
background = group.find("./control[@type='image']")
assert background is not None
assert text(background, "texture") == "special://skin/media/ui-solid.png"
assert text(background, "colordiffuse") == "e6202923"

# Resume and Start remain Kodi-owned actions in one horizontal remote flow.
options = group.find("./control[@type='grouplist'][@id='996']")
assert options is not None
assert text(options, "orientation") == "horizontal"
assert text(options, "itemgap") == "19"
template = root.find("./controls/control[@type='button'][@id='1000']")
assert template is not None
assert text(template, "height") == "68"
assert text(template, "font") == "font24"
assert text(template, "textcolor") == "asterSage"
assert text(template, "focusedcolor") == "asterIvory"
focus = template.find("texturefocus")
assert focus is not None
assert focus.attrib["border"] == "24"
assert focus.attrib["colordiffuse"] == "asterSage"
assert focus.text == "special://skin/media/ui-button-ring.png"
assert text(template, "texturenofocus") == "none"

# The abandoned full-screen stone panel must not return.
xml = RESUME.read_text()
for legacy in ("-1920", "5760", "3240", "asterStone", "ui-panel.png"):
    assert legacy not in xml, legacy

print("r47 Resume dialog gate passed: Aster player geometry, palette, focus and actions pinned")
