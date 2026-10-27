"""Exact, fail-closed corrections from the accepted HP owner review."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import xml.etree.ElementTree as ET


PREDECESSORS = {
    "Home.xml": "4c118dd42c3d97c1899a0dcbdce8e6ab42b22d3f309c09802f1a861fac9f830d",
    "MyVideoNav.xml": "2c5770babbc59879cebb0cf2d66bd6b2b2b4155b2197110a9548328836593eff",
    "Includes.xml": "c80a9842b11e1bd715e2df9bf2482093e76477420ec2cc21247269381a2e79aa",
    "IncludesHub.xml": "a06a827b489acf8ba557dabab6ee1f1092d632bbea758fbd4d6b8e0889fa95c1",
    "custom_1112_home.xml": "bd0c380922214b22b117205419b1fcf575a2394f72267ab7e23416be13551c88",
    "Settings.xml": "f7c6b0345647f1eb21c3dc3da16eb66de1822e1766a0a6dcafb066dce08520e2",
    "custom_1111_digest.xml": "8d39956f2c437ead3451910b61f3d07223cd078dfa1d7b070d9a6ca023b9be35",
    "IncludesBooks.xml": "3b1ed0f4151d8888c71f75f36710710441e694fdde97924d97ec36eb972996cc",
    "custom_1122_breaking.xml": "d55e4db24217966d34d110c037f9c100c9a2d3ab2b8325ae7b878dd65ed9395d",
    "IncludesMusic.xml": "c682bdf16362914b2273770a63d77ba21841c8a75dc375b53d9c2374f65f1ccd",
    "family-manifest.json": "11d4e7ab45f0123aa5135e1fdd7924fcf14010cb7ba12add1828c9f3fc139a58",
}

OUTLINE = "75cbb991"
SURFACE = "f23b3a32"


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


def home(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["Home.xml"], "review-home-predecessor")
    root = ET.fromstring(raw)
    hero = root.find(".//control[@id='21']")
    require(hero is not None, "review-home-hero")
    synopsis = next((node for node in hero.findall("control")
                     if node.get("type") == "textbox"), None)
    rating = next((node for node in hero.findall("control")
                   if (node.findtext("label") or "").endswith("[AsterHeroRating]")), None)
    require(synopsis is not None and rating is not None, "review-home-copy")
    field(synopsis, "top", 318); field(synopsis, "height", 86)
    field(rating, "top", 408)
    for identity in (120, 121, 122):
        control = hero.find(f"control[@id='{identity}']")
        require(control is not None, "review-home-action")
        field(control, "top", 442)
    for ring in hero.findall("control[@type='image']"):
        visible = ring.findtext("visible") or ""
        if any(f"Control.HasFocus({identity})" in visible for identity in (120, 121, 122)):
            field(ring, "top", 442)

    rail = root.find(".//control[@id='23']")
    require(rail is not None, "review-home-rail")
    request = rail.find("control[@id='137']")
    require(request is not None and request.findtext("label") == "Requests",
            "review-home-request")
    rail.remove(request)
    for child in list(rail):
        if "137" in (child.findtext("visible") or ""):
            rail.remove(child)
    collections = rail.find("control[@id='134']")
    youtube = rail.find("control[@id='136']")
    search = rail.find("control[@id='135']")
    require(collections is not None and youtube is not None and search is not None,
            "review-home-destinations")
    field(collections, "onright", 136); field(youtube, "onleft", 134)
    field(search, "onleft", 136); field(youtube, "left", 1408)
    for child in rail.findall("control"):
        visible = child.findtext("visible") or ""
        left = child.findtext("left")
        if visible == "Control.IsVisible(136)":
            field(child, "left", 1456)
        elif visible == "Control.HasFocus(136)":
            field(child, "left", 1407)
        elif child.get("type") == "image" and left == "1583":
            field(child, "left", 1418)
    back = next((node for node in rail.findall("control[@type='image']")
                 if node.findtext("left") == "532" and node.findtext("top") == "23"), None)
    require(back is not None, "review-home-rail-back")
    field(back, "width", 1050)
    for animation in rail.findall("animation"):
        condition = animation.get("condition") or ""
        animation.set("condition", condition.replace(" | Control.HasFocus(9007)",
                                                       " | Control.HasFocus(9007) | Control.HasFocus(9009)"))
    result = standard_search(encoded(root), "Home.xml")
    check = ET.fromstring(result)
    require(check.find(".//control[@id='137']") is None
            and check.find(".//control[@id='122']").findtext("top") == "442",
            "review-home-result")
    return result


def youtube(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["MyVideoNav.xml"], "review-youtube-predecessor")
    root = ET.fromstring(raw)
    landing = root.find(".//control[@id='9891']")
    require(landing is not None, "review-youtube-landing")
    mapping = {"53": "9530", "51": "9531", "52": "9532"}
    for node in landing.iter("control"):
        if node.get("id") in mapping:
            node.set("id", mapping[node.get("id")])
        for key in ("onup", "ondown"):
            child = node.find(key)
            if child is not None and child.text in mapping:
                child.text = mapping[child.text]
    for button in landing.findall("control[@type='button']"):
        down = button.find("ondown")
        if down is not None and down.text == "53": down.text = "9530"
    for onload in root.findall("onload"):
        if onload.text == "SetFocus(53)":
            onload.text = ("AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),"
                           "00:01,silent)")

    images = landing.findall("control[@type='image']")
    require(len(images) >= 3, "review-youtube-images")
    art, left_fade, bottom_fade = images[:3]
    require(art.findtext("height") == "1080" and left_fade.findtext("height") == "1080",
            "review-youtube-full-hero")
    base = ET.Element("control", {"type": "image"})
    for name, value in (("left", 0), ("top", 0), ("width", 1920), ("height", 1080)):
        field(base, name, value)
    field(base, "texture", "special://skin/media/ui-panel.png")
    field(base, "colordiffuse", "ff292721"); field(base, "aspectratio", "stretch")
    landing.insert(0, base)
    field(art, "height", 620); field(left_fade, "height", 620)
    field(bottom_fade, "top", 250); field(bottom_fade, "height", 370)
    result = standard_search(encoded(root), "MyVideoNav.xml")
    check = ET.fromstring(result)
    require(check.find(".//control[@id='9530']") is not None
            and check.find(".//control[@id='53']") is None
            and check.findtext("onload").startswith("AlarmClock(AsterYouTubeLandingFocus"),
            "review-youtube-result")
    return result


def includes(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["Includes.xml"], "review-includes-predecessor")
    root = ET.fromstring(raw)
    names = {"AsterYouTubeHeroTitle", "AsterYouTubeHeroPlot",
             "AsterYouTubeHeroMeta", "AsterYouTubeHeroArt"}
    found = 0
    for variable in root.findall("variable"):
        if variable.get("name") not in names: continue
        found += 1
        for value in variable.findall("value"):
            text = value.text or ""
            text = text.replace("Control.HasFocus(51)", "Control.HasFocus(9531)")
            text = text.replace("Control.HasFocus(52)", "Control.HasFocus(9532)")
            text = text.replace("Container(51)", "Container(9531)")
            text = text.replace("Container(52)", "Container(9532)")
            text = text.replace("Container(53)", "Container(9530)")
            value.text = text
    require(found == 4, "review-includes-variables")
    clock = root.find("include[@name='AsterClockPill']/definition")
    require(clock is not None, "review-clock")
    clock_images = clock.findall("control[@type='image']")
    require(len(clock_images) == 2, "review-clock-images")
    field(clock_images[0], "colordiffuse", OUTLINE)
    field(clock_images[1], "colordiffuse", SURFACE)
    result = encoded(root)
    require(b"Container(9530)" in result and b"Container(53)" not in result,
            "review-includes-result")
    return result


def side_rail(raw: bytes) -> bytes:
    require(sha(raw) == PREDECESSORS["IncludesHub.xml"], "review-side-rail-predecessor")
    root = ET.fromstring(raw)
    definition = root.find("include[@name='AsterNavigationRail']/definition")
    expanded = definition.find("control[@id='9000']")
    collapsed = definition.find("control[@id='9006']")
    require(expanded is not None and collapsed is not None, "review-side-rail-groups")
    for group, inner_height in ((expanded, 478), (collapsed, 478)):
        field(group, "top", 300); field(group, "height", 480)
        for node in group.findall("control"):
            if node.findtext("height") == "416": field(node, "height", 480)
            elif node.findtext("height") == "414": field(node, "height", inner_height)
        outer = next((node for node in group.findall("control[@type='image']")
                      if node.findtext("left") == "0" and node.findtext("top") == "0"), None)
        require(outer is not None, "review-side-rail-outer")
        texture = outer.find("texture")
        require(texture is not None, "review-side-rail-texture")
        texture.set("colordiffuse", OUTLINE)
    settings = expanded.find("control[@id='9005']")
    music = expanded.find("control[@id='9007']")
    require(settings is not None and music is not None, "review-side-rail-routes")
    settings_icon = next((node for node in expanded.findall("control[@type='image']")
                          if node.findtext("texture") == "special://skin/media/31-settings-app.png"), None)
    require(settings_icon is not None, "review-side-rail-settings-icon")
    request_icon = deepcopy(settings_icon)
    field(request_icon, "top", 349)
    field(request_icon, "texture", "special://skin/media/aster-compass-128.png")
    expanded.insert(list(expanded).index(settings_icon), request_icon)
    field(settings_icon, "top", 413); field(settings, "top", 400); field(settings, "onup", 9009)
    request = deepcopy(settings); request.set("id", "9009")
    field(request, "top", 336); field(request, "label", "Requests")
    field(request, "onclick", "RunScript(script.asteracquisition)")
    field(request, "onup", 9007); field(request, "ondown", 9005)
    expanded.insert(list(expanded).index(settings), request)
    field(music, "ondown", 9009)

    collapsed_settings = next((node for node in collapsed.findall("control[@type='image']")
                               if node.findtext("texture") == "special://skin/media/31-settings-app.png"), None)
    require(collapsed_settings is not None, "review-side-rail-collapsed-settings")
    collapsed_request = deepcopy(collapsed_settings)
    field(collapsed_request, "top", 345)
    field(collapsed_request, "texture", "special://skin/media/aster-compass-128.png")
    collapsed.insert(list(collapsed).index(collapsed_settings), collapsed_request)
    field(collapsed_settings, "top", 409)
    opener = collapsed.find("control[@id='8999']")
    field(opener, "height", 480)
    for node in root.iter("visible"):
        text = node.text or ""
        if "9009" not in text:
            if "!Control.HasFocus(9007)" in text:
                text = text.replace("!Control.HasFocus(9007)",
                                    "!Control.HasFocus(9007) + !Control.HasFocus(9009)")
            elif "Control.HasFocus(9007)" in text:
                text = text.replace("Control.HasFocus(9007)",
                                    "Control.HasFocus(9007) | Control.HasFocus(9009)")
            node.text = text
    result = encoded(root)
    check = ET.fromstring(result)
    route = check.find(".//control[@id='9009']")
    require(route is not None and route.findtext("onclick") == "RunScript(script.asteracquisition)"
            and check.find(".//control[@id='9005']").findtext("onup") == "9009",
            "review-side-rail-result")
    return result


def standard_search(raw: bytes, name: str) -> bytes:
    """Apply the shared clock-outline/rail-surface treatment to page Search."""
    require(sha(raw) == PREDECESSORS[name] or name in ("Home.xml", "MyVideoNav.xml"),
            "review-search-predecessor")
    root = ET.fromstring(raw)
    buttons = [node for node in root.iter("control")
               if node.get("type") == "button" and node.findtext("label") == "Search"]
    require(len(buttons) == 1, "review-search-button")
    button = buttons[0]
    nofocus = button.find("texturenofocus")
    require(nofocus is not None, "review-search-surface")
    nofocus.set("colordiffuse", SURFACE)
    left, top = int(button.findtext("left")), int(button.findtext("top"))
    parent = next(node for node in root.iter() if button in list(node))
    rings = []
    for node in parent.findall("control[@type='image']"):
        if node.findtext("left", "").lstrip("-").isdigit() \
                and node.findtext("top", "").lstrip("-").isdigit():
            x, y = int(node.findtext("left")), int(node.findtext("top"))
            if abs(x - left) <= 5 and abs(y - top) <= 5 \
                    and not node.findtext("visible"):
                rings.append(node)
    require(len(rings) == 1, "review-search-outline")
    texture = rings[0].find("texture")
    if texture is not None: texture.set("colordiffuse", OUTLINE)
    colour = rings[0].find("colordiffuse")
    if colour is not None: colour.text = OUTLINE
    return encoded(root)


def family(raw: bytes, changed: dict[str, bytes]) -> bytes:
    require(sha(raw) == PREDECESSORS["family-manifest.json"],
            "review-family-predecessor")
    value = json.loads(raw)
    tracked = {
        "Home.xml", "Settings.xml", "custom_1111_digest.xml",
        "custom_1112_home.xml",
    }
    for name in tracked:
        key = "1080i/" + name
        require(value["skin"][key] == PREDECESSORS[name],
                "review-family-" + name)
        value["skin"][key] = sha(changed[name])
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
