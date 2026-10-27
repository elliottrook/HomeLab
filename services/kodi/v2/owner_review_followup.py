"""Fail-closed follow-up to the 2026-10-27 HP owner visual review."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET


PREDECESSORS = {
    "Home.xml": "ac3381236aa99cde98538b9ace882a5b999f3a4ee087a01c5bcf2dfc3ba3ff87",
    "MyVideoNav.xml": "1b38da1eec850bad126a978b9eacd2461d6a84cb375a63fd3c433ec1d00a7e49",
    "IncludesHub.xml": "096cdb812424ad42dd3b1210005472ed8b3081d1bc4b3e0fffb204702ceb42c7",
    "IncludesBooks.xml": "a4c211a3c1dc7fab93d6b30c590ae11f16af924a4cdd45e2679a415ce4d8e19a",
    "IncludesMusic.xml": "c7cfd977222fc91dd7f36dc7b202c02f8b28d67f169e7e8d28eb55d1bd0a48bc",
    "Settings.xml": "b019b3d70701de4658154e51812e6aca231835b453ce6760b6202e4c9db1d44e",
    "custom_1133_acquisition.xml": "c74dfe624bf033b5b8213f1e27e242a80c01443cd6fcab1572af41734a89f644",
    "family-manifest.json": "9d75941f4984d22bec0ad64a2e41b0c8e7742d0a1758ea74c179145ed0f0237d",
}

RAIL_IDS = (8999, 9001, 9002, 9003, 9004, 9005, 9007, 9009)
RAIL_VISIBLE = " | ".join("Control.HasFocus(%s)" % value for value in RAIL_IDS)
CONTENT_VISIBLE = " + ".join("!Control.HasFocus(%s)" % value for value in RAIL_IDS)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(value, code):
    if not value:
        raise ValueError(code)


def field(node, name, value, **attributes):
    child = node.find(name)
    if child is None:
        child = ET.SubElement(node, name)
    child.attrib.clear(); child.attrib.update(attributes); child.text = str(value)
    return child


def encoded(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _admit_requests(root):
    """Extend existing rail-aware visibility without changing other logic."""
    for node in root.iter():
        candidates = []
        if node.tag == "visible": candidates.append((None, node.text or ""))
        if "condition" in node.attrib:
            candidates.append(("condition", node.get("condition") or ""))
        for attribute, text in candidates:
            if "9007" not in text or "9009" in text:
                continue
            if "!Control.HasFocus(9007)" in text:
                text = text.replace("!Control.HasFocus(9007)",
                                    "!Control.HasFocus(9007) + !Control.HasFocus(9009)")
            else:
                text = text.replace("Control.HasFocus(9007)",
                                    "Control.HasFocus(9007) | Control.HasFocus(9009)")
            if attribute is None: node.text = text
            else: node.set(attribute, text)


def _compact_button(node, left, width, top=350):
    for name, value in (("left", left), ("top", top), ("width", width),
                        ("height", 44), ("font", "font20"),
                        ("align", "center"), ("aligny", "center"),
                        ("textcolor", "asterIvory"),
                        ("focusedcolor", "asterIvory")):
        field(node, name, value)
    for include in list(node.findall("include")):
        node.remove(include)
    focus = field(node, "texturefocus", "special://skin/media/ui-panel.png")
    focus.set("border", "18"); focus.set("colordiffuse", "ff005c46")
    idle = field(node, "texturenofocus", "special://skin/media/ui-panel.png")
    idle.set("border", "18"); idle.set("colordiffuse", "52000000")


def home(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["Home.xml"], "followup-home-predecessor")
    root = ET.fromstring(raw); hero = root.find(".//control[@id='21']")
    synopsis = next((node for node in hero.findall("control")
                     if node.get("type") == "textbox"), None)
    require(synopsis is not None, "followup-home-synopsis")
    field(synopsis, "font", "font18")
    _admit_requests(root)
    result = encoded(root)
    require(b"<font>font18</font>" in result and b"Control.HasFocus(9009)" in result,
            "followup-home-result")
    return result


def side_rail(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["IncludesHub.xml"], "followup-rail-predecessor")
    root = ET.fromstring(raw); definition = root.find("include[@name='AsterNavigationRail']/definition")
    changed = 0
    for group_id, expected_top in ((9000, "349"), (9006, "345")):
        group = definition.find("control[@id='%s']" % group_id)
        for image in group.findall("control[@type='image']"):
            if image.findtext("top") == expected_top \
                    and image.findtext("texture") == "special://skin/media/aster-compass-128.png":
                field(image, "texture", "special://skin/media/aster-icon-128.png")
                changed += 1
    require(changed == 2, "followup-request-icons")
    return encoded(root)


def media_browser(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["MyVideoNav.xml"], "followup-media-predecessor")
    root = ET.fromstring(raw); generic = root.find(".//control[@id='9893']")
    require(generic is not None, "followup-media-generic")
    images = generic.findall("control[@type='image']")
    require(len(images) >= 3, "followup-media-images")
    for image in images[:3]: field(image, "height", 620)
    plot = next((node for node in generic.findall("control")
                 if node.findtext("label") == "$VAR[AsterBrowsePlot]"), None)
    require(plot is not None, "followup-media-plot")
    field(plot, "font", "font18"); field(plot, "height", 68)
    play = generic.find("control[@id='9100']"); info = generic.find("control[@id='9101']")
    require(play is not None and info is not None, "followup-media-actions")
    _compact_button(play, 145, 180); _compact_button(info, 340, 165)
    rings = [node for node in generic.findall("control[@type='image']")
             if "Control.HasFocus(910" in (node.findtext("visible") or "")]
    require(len(rings) == 2, "followup-media-rings")
    for ring, left, width in ((rings[0], 145, 180), (rings[1], 340, 165)):
        field(ring, "left", left); field(ring, "top", 350)
        field(ring, "width", width); field(ring, "height", 44)
    return encoded(root)


def books(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["IncludesBooks.xml"], "followup-books-predecessor")
    root = ET.fromstring(raw); definition = root.find("include[@name='AsterBooksPage']/definition")
    require(definition is not None, "followup-books-template")
    for image in definition.findall("control[@type='image']"):
        texture = image.findtext("texture") or ""
        if texture == "$INFO[Window.Property(AsterBooks.HeroBackdrop)]" \
                or texture.endswith("ui-hero-bottom-fade.png"):
            field(image, "height", 620)
    group = next(node for node in definition.findall("control[@type='group']")
                 if node.find("control[@id='300']") is not None)
    first = group.find("control[@id='300']"); second = group.find("control[@id='304']")
    _compact_button(first, 1050, 180, 454); _compact_button(second, 1242, 180, 454)
    _admit_requests(root)
    return encoded(root)


def music(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["IncludesMusic.xml"], "followup-music-predecessor")
    root = ET.fromstring(raw); definition = root.find("include[@name='AsterMusicPage']/definition")
    require(definition is not None, "followup-music-template")
    for image in definition.findall("control[@type='image']"):
        texture = image.findtext("texture") or ""
        if texture in ("$INFO[Window.Property(AsterMusic.HeroBackdrop)]",
                       "$INFO[Container(500).ListItem.Art(fanart)]") \
                or texture.endswith(("ui-hero-left-fade.png", "ui-hero-bottom-fade.png")):
            field(image, "height", 620)
    genre = next((node for node in definition.findall(".//control[@type='image']")
                  if node.findtext("texture") == "special://skin/media/20-music-app.png"), None)
    require(genre is not None, "followup-music-genre-icon")
    field(genre, "texture", "special://skin/media/13-music.png")
    _admit_requests(root)
    return encoded(root)


def settings(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["Settings.xml"], "followup-settings-predecessor")
    root = ET.fromstring(raw); first = root.find(".//control[@id='200']")
    require(first is not None, "followup-settings-first")
    field(first, "onleft", 8999); _admit_requests(root)
    return encoded(root)


def acquisition(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["custom_1133_acquisition.xml"],
            "followup-acquisition-predecessor")
    root = ET.fromstring(raw); controls = root.find("controls"); group = controls.find("control[@id='600']")
    require(group is not None, "followup-acquisition-group")
    rail = ET.Element("include", {"content": "AsterNavigationRail"})
    ET.SubElement(rail, "param", {"name": "content", "value": "30"})
    ET.SubElement(rail, "param", {"name": "railfocus", "value": "9009"})
    controls.insert(list(controls).index(group), rail)
    field(group, "visible", CONTENT_VISIBLE)
    images = group.findall("control[@type='image']")
    for image in images[:4]: field(image, "height", 620)
    for identity, left in ((10, 790), (11, 922), (12, 1054)):
        button = group.find("control[@id='%s']" % identity)
        _compact_button(button, left, 120, 31)
    field(group.find("control[@id='10']"), "onleft", 8999)
    action = group.find("control[@id='50']"); require(action is not None, "followup-acquisition-action")
    field(action, "left", 455); field(action, "top", 640); field(action, "width", 180); field(action, "height", 44)
    field(action, "onleft", 8999)
    for node in group.findall("control"):
        if node is action: continue
        if node.findtext("left") == "455" and node.findtext("top") == "640" \
                and node.findtext("width") == "390":
            field(node, "width", 180); field(node, "height", 44)
            if node.get("type") == "label": field(node, "font", "font20")
    listing = group.find("control[@id='30']"); field(listing, "onleft", 8999)
    return encoded(root)


def family(raw: bytes, changed: dict[str, bytes]) -> bytes:
    require(sha(raw) == PREDECESSORS["family-manifest.json"], "followup-family-predecessor")
    value = json.loads(raw)
    for name in ("Home.xml", "Settings.xml"):
        require(value["skin"]["1080i/" + name] == PREDECESSORS[name],
                "followup-family-" + name)
        value["skin"]["1080i/" + name] = sha(changed[name])
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
