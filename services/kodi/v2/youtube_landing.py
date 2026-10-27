"""Compose an Aster landing over the official YouTube add-on root only."""

import hashlib
import xml.etree.ElementTree as ET


NAV_SHA = "d1dc27ccde4eeed3e29f0a2ed935a1668d9757f527cb36fd1234ab28630c6c32"
INCLUDES_SHA = "fca53b5ee0f8e9f0fa25142bc993fbf902b3d213ec7b0bfc9a866f12d20d6ee2"
ROOT = "String.IsEqual(Container.FolderPath,plugin://plugin.video.youtube/)"
SEARCH = ("String.StartsWith(Container.FolderPath,"
          "plugin://plugin.video.youtube/kodion/search/)")
NOT_ROOT = "!" + ROOT
NOT_ROOT_OR_SEARCH = "!" + ROOT + " + !" + SEARCH

SEARCH_ROUTE = ("plugin://plugin.video.youtube/kodion/search/input_prompt/"
                "?category_label=Search&hide_folders=true")
LEGACY_SEARCH_ROUTE = ("plugin://plugin.video.youtube/kodion/search/list/"
                       "?category_label=Search")

ROUTES = (
    (9300, "Search", SEARCH_ROUTE, 420, 165),
    (9301, "Subscriptions", "plugin://plugin.video.youtube/special/my_subscriptions?category_label=My+Subscriptions&hide_folders=true", 595, 225),
    (9302, "Recommended", "plugin://plugin.video.youtube/special/recommendations?category_label=Recommendations", 830, 215),
    (9303, "Watch Later", "plugin://plugin.video.youtube/special/playlist/WL/?category_label=Watch+Later", 1055, 195),
    (9304, "Channels", "plugin://plugin.video.youtube/subscriptions/list/?category_label=Subscribed+Channels", 1260, 175),
)

LANDING_ROWS = (
    (9530, "New from subscriptions", ROUTES[1][2], 405, 438, 9531, 9301),
    (9531, "Recommended", ROUTES[2][2], 627, 660, 9532, 9530),
    (9532, "Watch later", ROUTES[3][2], 849, 882, 9532, 9531),
)
ROWS = (
    (50, "New from subscriptions", ROUTES[1][2], 405, 438, 51, 9301),
    (51, "Recommended", ROUTES[2][2], 627, 660, 52, 50),
    (52, "Watch later", ROUTES[3][2], 849, 882, 52, 51),
)


def require(value, code):
    if not value:
        raise ValueError(code)


def field(parent, name, value, **attributes):
    node = ET.SubElement(parent, name, attributes)
    node.text = str(value)
    return node


def image(parent, left, top, width, height, texture, **attributes):
    node = ET.SubElement(parent, "control", {"type": "image"})
    for name, value in (("left", left), ("top", top), ("width", width),
                        ("height", height)):
        field(node, name, value)
    field(node, "texture", texture, **attributes)
    return node


def label(parent, left, top, width, height, text, font="font20",
          colour="asterIvory"):
    node = ET.SubElement(parent, "control", {"type": "label"})
    for name, value in (("left", left), ("top", top), ("width", width),
                        ("height", height), ("label", text), ("font", font),
                        ("textcolor", colour)):
        field(node, name, value)
    return node


def variable(name, rows):
    node = ET.Element("variable", {"name": name})
    for condition, value in rows:
        if condition:
            field(node, "value", value, condition=condition)
        else:
            field(node, "value", value)
    return node


def extend_includes(raw, include_search=True):
    require(hashlib.sha256(raw).hexdigest() == INCLUDES_SHA,
            "youtube-landing-includes-predecessor")
    root = ET.fromstring(raw)
    names = {node.get("name") for node in root.findall("variable")}
    fallback = 9530 if include_search else 50
    second = 9531 if include_search else 51
    third = 9532 if include_search else 52
    additions = (
        variable("AsterYouTubeHeroTitle", ((
            (SEARCH + " + Container(50).ListItem.IsParentFolder",
             "Choose a video"),
            (SEARCH, "$INFO[Container(50).ListItem.Label]"),)
              if include_search else ()) + (
            (f"Control.HasFocus({second})", f"$INFO[Container({second}).ListItem.Label]"),
            (f"Control.HasFocus({third})", f"$INFO[Container({third}).ListItem.Label]"),
            (None, f"$INFO[Container({fallback}).ListItem.Label]"))),
        variable("AsterYouTubeHeroPlot", ((
            (SEARCH + " + Container(50).ListItem.IsParentFolder",
             "Search results for $INFO[Container.PluginCategory]"),
            (SEARCH, "$INFO[Container(50).ListItem.Plot]"),)
              if include_search else ()) + (
            (f"Control.HasFocus({second})", f"$INFO[Container({second}).ListItem.Plot]"),
            (f"Control.HasFocus({third})", f"$INFO[Container({third}).ListItem.Plot]"),
            (None, f"$INFO[Container({fallback}).ListItem.Plot]"))),
        variable("AsterYouTubeHeroMeta", ((
            (SEARCH + " + Container(50).ListItem.IsParentFolder", ""),
            (SEARCH, "$INFO[Container(50).ListItem.Artist]  $INFO[Container(50).ListItem.Duration]"),)
              if include_search else ()) + (
            (f"Control.HasFocus({second})", f"$INFO[Container({second}).ListItem.Artist]  $INFO[Container({second}).ListItem.Duration]"),
            (f"Control.HasFocus({third})", f"$INFO[Container({third}).ListItem.Artist]  $INFO[Container({third}).ListItem.Duration]"),
            (None, f"$INFO[Container({fallback}).ListItem.Artist]  $INFO[Container({fallback}).ListItem.Duration]"))),
        variable("AsterYouTubeHeroArt", ((
            (SEARCH + " + Container(50).ListItem.IsParentFolder", ""),
            (SEARCH, "$INFO[Container(50).ListItem.Art(thumb)]"),)
              if include_search else ()) + (
            (f"Control.HasFocus({second})", f"$INFO[Container({second}).ListItem.Art(thumb)]"),
            (f"Control.HasFocus({third})", f"$INFO[Container({third}).ListItem.Art(thumb)]"),
            (None, f"$INFO[Container({fallback}).ListItem.Art(thumb)]"))),
    )
    require(not names.intersection({node.get("name") for node in additions}),
            "youtube-landing-variable-exists")
    for offset, node in enumerate(additions):
        root.insert(offset, node)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def top_button(parent, identity, text, route, left, width, left_id, right_id,
               down=50):
    node = ET.SubElement(parent, "control", {"type": "button", "id": str(identity)})
    for name, value in (("left", left), ("top", 30), ("width", width),
                        ("height", 48), ("label", text), ("font", "font20"),
                        ("align", "center"), ("aligny", "center"),
                        ("textcolor", "asterIvory"),
                        ("focusedcolor", "asterIvory"), ("onleft", left_id),
                        ("onright", right_id), ("onup", identity),
                        ("ondown", down)):
        field(node, name, value)
    field(node, "texturefocus", "special://skin/media/ui-panel.png",
          border="18", colordiffuse="ff005c46")
    field(node, "texturenofocus", "special://skin/media/ui-panel.png",
          border="18", colordiffuse="99000000")
    field(node, "onclick", f'ActivateWindow(Videos,"{route}",return)')
    return node


def card_layout(parent, focused=False):
    node = ET.SubElement(parent, "focusedlayout" if focused else "itemlayout",
                         {"width": "300", "height": "182"})
    if focused:
        ring = image(node, 0, 0, 292, 164,
                     "special://skin/media/ui-compact-card-ring.png")
        field(ring, "colordiffuse", "asterIvory")
    art = image(node, 6 if focused else 10, 4 if focused else 8,
                280 if focused else 272, 154 if focused else 146,
                "$INFO[ListItem.Art(thumb)]", background="true",
                diffuse="special://skin/media/ui-compact-card-mask.png")
    field(art, "aspectratio", "scale", scalediffuse="false")
    if focused:
        accent = image(node, 2, 2, 288, 160,
                       "special://skin/media/ui-compact-card-ring.png")
        field(accent, "colordiffuse", "asterGreen")
    title = label(node, 6 if focused else 10, 160, 280, 24,
                  "$INFO[ListItem.Label]", "font20",
                  "asterGreen" if focused else "asterIvory")
    field(title, "truncate", "true")


def landing_panel(parent, identity, heading, route, heading_top, panel_top,
                  down, up):
    label(parent, 125, heading_top, 700, 32, heading, "font24", "asterIvory")
    node = ET.SubElement(parent, "control", {"type": "panel", "id": str(identity)})
    for name, value in (("left", 125), ("top", panel_top), ("width", 1700),
                        ("height", 182), ("orientation", "horizontal"),
                        ("scrolltime", 180), ("preloaditems", 2),
                        ("onup", up), ("ondown", down)):
        field(node, name, value)
    card_layout(node, False); card_layout(node, True)
    field(node, "content", route, target="videos")
    return node


def search_button(parent, identity, text, route, left, width, left_id,
                  right_id):
    node = top_button(parent, identity, text, route, left, width,
                      left_id, right_id)
    node.find("ondown").text = "50"
    return node


def search_view(parent):
    group = ET.SubElement(parent, "control", {"type": "group", "id": "9892"})
    field(group, "visible", SEARCH)
    hero = image(group, 0, 0, 1920, 1080, "$VAR[AsterYouTubeHeroArt]",
                 background="true")
    field(hero, "aspectratio", "scale")
    field(hero, "fadetime", 250)
    fade = image(group, 0, 0, 1920, 1080,
                 "special://skin/media/ui-hero-left-fade.png")
    field(fade, "colordiffuse", "ee101412")
    field(fade, "aspectratio", "stretch")
    bottom = image(group, 0, 250, 1920, 300,
                   "special://skin/media/ui-hero-bottom-fade.png")
    field(bottom, "colordiffuse", "ee292721")
    field(bottom, "aspectratio", "stretch")
    result_back = image(group, 18, 450, 1884, 630,
                        "special://skin/media/ui-panel.png", border="20")
    field(result_back, "colordiffuse", "f2f2ede4")
    field(result_back, "aspectratio", "stretch")

    image(group, 70, 25, 72, 72,
          "special://skin/media/33-aster-youtube-128.png")
    label(group, 155, 32, 230, 52, "YouTube", "font40", "asterIvory")
    rail = image(group, 400, 18, 1120, 72,
                 "special://skin/media/ui-panel.png", border="20")
    field(rail, "colordiffuse", "99292721")
    search_ring = image(group, 416, 26, 198, 56,
                        "special://skin/media/ui-compact-card-ring.png")
    field(search_ring, "colordiffuse", "asterGold")
    buttons = (
        (9400, "Search again", SEARCH_ROUTE, 420, 190),
        (9401, "Subscriptions", ROUTES[1][2], 625, 225),
        (9402, "Recommended", ROUTES[2][2], 865, 215),
        (9403, "Watch Later", ROUTES[3][2], 1095, 195),
    )
    for index, row in enumerate(buttons):
        left_id = buttons[index - 1][0] if index else 9404
        right_id = buttons[index + 1][0] if index + 1 < len(buttons) else 9404
        search_button(group, *row, left_id, right_id)
    back = ET.SubElement(group, "control", {"type": "button", "id": "9404"})
    for name, value in (("left", 1305), ("top", 30), ("width", 190),
                        ("height", 48), ("label", "Back"),
                        ("font", "font20"), ("align", "center"),
                        ("aligny", "center"), ("textcolor", "asterIvory"),
                        ("focusedcolor", "asterIvory"), ("onleft", 9403),
                        ("onright", 9400), ("onup", 9404),
                        ("ondown", 50), ("onclick", "Action(Back)")):
        field(back, name, value)
    field(back, "texturefocus", "special://skin/media/ui-panel.png",
          border="18", colordiffuse="ff005c46")
    field(back, "texturenofocus", "special://skin/media/ui-panel.png",
          border="18", colordiffuse="99000000")

    query = label(group, 125, 135, 1120, 56,
                  "$INFO[Container.PluginCategory]", "font40", "asterIvory")
    field(query, "shadowcolor", "aa000000")
    field(query, "truncate", "true")
    title = label(group, 125, 202, 1120, 48,
                  "$VAR[AsterYouTubeHeroTitle]", "font30", "asterIvory")
    field(title, "shadowcolor", "aa000000")
    field(title, "truncate", "true")
    plot = ET.SubElement(group, "control", {"type": "textbox"})
    for name, value in (("left", 125), ("top", 254), ("width", 980),
                        ("height", 96), ("label", "$VAR[AsterYouTubeHeroPlot]"),
                        ("font", "font20"), ("textcolor", "asterIvory"),
                        ("shadowcolor", "aa000000"),
                        ("wrapmultiline", "true")):
        field(plot, name, value)
    label(group, 125, 356, 980, 30, "$VAR[AsterYouTubeHeroMeta]",
          "font20", "asterSage")
    label(group, 400, 445, 700, 40, "Results", "font24", "asterInk")
    return group


def extend_navigation(raw, include_search=True):
    require(hashlib.sha256(raw).hexdigest() == NAV_SHA,
            "youtube-landing-nav-predecessor")
    root = ET.fromstring(raw)
    controls = root.find("controls")
    require(controls is not None and len(list(controls)) > 10,
            "youtube-landing-controls")
    original = list(controls)
    for node in original:
        controls.remove(node)
    if include_search:
        onload = ET.Element("onload", {"condition": ROOT})
        onload.text = ("AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),"
                       "00:01,silent)")
        root.insert(1, onload)
    landing = ET.Element("control", {"type": "group", "id": "9891"})
    field(landing, "visible", ROOT)
    base = image(landing, 0, 0, 1920, 1080,
                 "special://skin/media/ui-panel.png")
    field(base, "colordiffuse", "ff292721")
    field(base, "aspectratio", "stretch")
    hero = image(landing, 0, 0, 1920, 620, "$VAR[AsterYouTubeHeroArt]",
                 background="true")
    field(hero, "aspectratio", "scale")
    field(hero, "fadetime", 250)
    fade = image(landing, 0, 0, 1920, 620,
                 "special://skin/media/ui-hero-left-fade.png")
    field(fade, "colordiffuse", "ee101412"); field(fade, "aspectratio", "stretch")
    bottom = image(landing, 0, 250, 1920, 370,
                   "special://skin/media/ui-hero-bottom-fade.png")
    field(bottom, "colordiffuse", "ee292721"); field(bottom, "aspectratio", "stretch")

    image(landing, 70, 25, 72, 72, "special://skin/media/33-aster-youtube-128.png")
    label(landing, 155, 32, 230, 52, "YouTube", "font40", "asterIvory")
    rail = image(landing, 400, 18, 1255, 72, "special://skin/media/ui-panel.png",
                 border="20")
    field(rail, "colordiffuse", "99292721")
    search_ring = image(landing, 416, 26, 173, 56,
                        "special://skin/media/ui-compact-card-ring.png")
    field(search_ring, "colordiffuse", "asterGold")

    for index, (identity, text, route, left, width) in enumerate(ROUTES):
        if not include_search and identity == 9300:
            route = LEGACY_SEARCH_ROUTE
        left_id = ROUTES[index - 1][0] if index else 9305
        right_id = ROUTES[index + 1][0] if index + 1 < len(ROUTES) else 9305
        top_button(landing, identity, text, route, left, width, left_id,
                   right_id, 9530 if include_search else 50)
    back = ET.SubElement(landing, "control", {"type": "button", "id": "9305"})
    for name, value in (("left", 1445), ("top", 30), ("width", 190),
                        ("height", 48), ("label", "Back"), ("font", "font20"),
                        ("align", "center"), ("aligny", "center"),
                        ("textcolor", "asterIvory"),
                        ("focusedcolor", "asterIvory"), ("onleft", 9304),
                        ("onright", 9300), ("onup", 9305),
                        ("ondown", 9530 if include_search else 50),
                        ("onclick", "Action(Back)")):
        field(back, name, value)
    field(back, "texturefocus", "special://skin/media/ui-panel.png",
          border="18", colordiffuse="ff005c46")
    field(back, "texturenofocus", "special://skin/media/ui-panel.png",
          border="18", colordiffuse="99000000")

    title = label(landing, 125, 142, 1120, 62,
                  "$VAR[AsterYouTubeHeroTitle]", "font40", "asterIvory")
    field(title, "shadowcolor", "aa000000"); field(title, "truncate", "true")
    plot = ET.SubElement(landing, "control", {"type": "textbox"})
    for name, value in (("left", 125), ("top", 210), ("width", 980),
                        ("height", 105), ("label", "$VAR[AsterYouTubeHeroPlot]"),
                        ("font", "font20"), ("textcolor", "asterIvory"),
                        ("shadowcolor", "aa000000"), ("wrapmultiline", "true")):
        field(plot, name, value)
    label(landing, 125, 326, 980, 30, "$VAR[AsterYouTubeHeroMeta]",
          "font20", "asterSage")

    for row in (LANDING_ROWS if include_search else ROWS):
        landing_panel(landing, *row)

    # Keep the landing first. Kodi resolves the shared default container ID to
    # its explicit content while the established browser container continues
    # to receive ordinary directory and official search results.
    generic = ET.Element("control", {"type": "group", "id": "9890"})
    field(generic, "visible", NOT_ROOT)
    if include_search:
        browse_chrome = ET.SubElement(generic, "control",
                                      {"type": "group", "id": "9893"})
        field(browse_chrome, "visible", "!" + SEARCH)
        result_panel = None
        for node in original:
            if node.tag == "control" and node.get("id") == "50":
                result_panel = node
            else:
                browse_chrome.append(node)
        search_view(generic)
        require(result_panel is not None, "youtube-landing-result-panel")
        old_up = result_panel.find("onup")
        require(old_up is not None and old_up.text == "9100",
                "youtube-landing-result-navigation")
        result_panel.remove(old_up)
        field(result_panel, "onup", 9400, condition=SEARCH)
        field(result_panel, "onup", 9100, condition="!" + SEARCH)
        generic.append(result_panel)
    else:
        for node in original:
            generic.append(node)

    if include_search:
        controls.append(generic)
        controls.append(landing)
    else:
        controls.append(landing)
        controls.append(generic)

    result = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    check = ET.fromstring(result)
    require(len(check.findall(".//control[@id='50']"))
            == (1 if include_search else 2),
            "youtube-landing-context-container")
    require(check.find(".//control[@id='9300']") is not None
            and check.find(f".//control[@id='{'9532' if include_search else '52'}']") is not None
            and (not include_search
                 or check.find(".//control[@id='9400']") is not None),
            "youtube-landing-controls-missing")
    return result
