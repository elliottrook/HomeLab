"""Keep official YouTube navigation inside Kodi's Videos directory stack."""

import xml.etree.ElementTree as ET


ROUTE_BUTTONS = (9300, 9301, 9302, 9303, 9304,
                 9400, 9401, 9402, 9403)
BACK_HELPER = "RunScript(special://home/addons/skin.asterhome/tools/youtube_back.py)"
ROUTE_FOCUS = "special://home/addons/skin.asterhome/tools/youtube_route_focus.py"
YOUTUBE = "String.Contains(Container.FolderPath,plugin.video.youtube)"
ROUTES = {
    9301: ("Subscriptions", "plugin://plugin.video.youtube/subscriptions/list/"),
    9302: ("Trending", "plugin://plugin.video.youtube/special/popular_right_now"),
    9303: ("Watch Later", "plugin://plugin.video.youtube/special/playlist/WL"),
    9304: ("My Channel", "plugin://plugin.video.youtube/channel/mine"),
    9401: ("Subscriptions", "plugin://plugin.video.youtube/subscriptions/list/"),
    9402: ("Trending", "plugin://plugin.video.youtube/special/popular_right_now"),
    9403: ("Watch Later", "plugin://plugin.video.youtube/special/playlist/WL"),
}
ROWS = {
    9530: ("Subscribed channels", ROUTES[9301][1]),
    9531: ("Trending", ROUTES[9302][1]),
    9532: ("Watch later", ROUTES[9303][1]),
}


def transform(raw):
    root = ET.fromstring(raw)
    for identity in ROUTE_BUTTONS:
        button = root.find(f".//control[@id='{identity}']")
        action = button.find("onclick") if button is not None else None
        if action is None or not (action.text or "").startswith(
                'ActivateWindow(Videos,"plugin://plugin.video.youtube/'):
            raise ValueError(f"unexpected YouTube button {identity}")
        old = action.text
        if not old.endswith('",return)'):
            raise ValueError(f"unexpected YouTube button route {identity}")
        route = ROUTES[identity][1] if identity in ROUTES else old[
            len('ActivateWindow(Videos,"'):-len('",return)')]
        action.text = f"Container.Update({route})"
        if identity in ROUTES:
            ET.SubElement(button, "onclick").text = f"RunScript({ROUTE_FOCUS},{route})"
        if identity in ROUTES:
            label = button.find("label")
            if label is None:
                raise ValueError(f"missing YouTube button label {identity}")
            label.text = ROUTES[identity][0]

    for identity, (name, route) in ROWS.items():
        panel = root.find(f".//control[@id='{identity}']")
        content = panel.find("content") if panel is not None else None
        if content is None or not (content.text or "").startswith(
                "plugin://plugin.video.youtube/"):
            raise ValueError(f"unexpected YouTube row {identity}")
        content.text = route
        for parent in root.iter():
            children = list(parent)
            if panel in children:
                index = children.index(panel)
                heading = children[index - 1] if index else None
                if heading is None or heading.get("type") != "label" \
                        or heading.find("label") is None:
                    raise ValueError(f"unexpected YouTube row heading {identity}")
                heading.find("label").text = name
                break
        else:
            raise ValueError(f"missing YouTube row parent {identity}")

    back = root.find(".//control[@id='9000']")
    action = back.find("onclick") if back is not None else None
    if action is None or action.text != "Action(Back)" or action.attrib:
        raise ValueError("unexpected generic Back button")
    action.set("condition", "!" + YOUTUBE)
    ET.SubElement(back, "onclick", {"condition": YOUTUBE}).text = BACK_HELPER

    for identity in (9305, 9404):
        button = root.find(f".//control[@id='{identity}']")
        action = button.find("onclick") if button is not None else None
        if action is None or action.text != BACK_HELPER:
            raise ValueError(f"unexpected YouTube Back button {identity}")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def add_route_focus_to_live(raw):
    """Advance the already installed lab navigation without repeating its rewrite."""
    root = ET.fromstring(raw)
    for identity, (_, route) in ROUTES.items():
        button = root.find(f".//control[@id='{identity}']")
        actions = button.findall("onclick") if button is not None else []
        if len(actions) != 1 or actions[0].text != f"Container.Update({route})":
            raise ValueError(f"unexpected installed YouTube button {identity}")
        ET.SubElement(button, "onclick").text = f"RunScript({ROUTE_FOCUS},{route})"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def correct_watch_later_live(raw):
    """Replace the empty local list with the signed-in online WL playlist."""
    root = ET.fromstring(raw)
    old = "plugin://plugin.video.youtube/kodion/watch_later/list"
    new = ROUTES[9303][1]
    for identity in (9303, 9403):
        button = root.find(f".//control[@id='{identity}']")
        actions = button.findall("onclick") if button is not None else []
        if [action.text for action in actions] != [
                f"Container.Update({old})",
                f"RunScript({ROUTE_FOCUS},{old})"]:
            raise ValueError(f"unexpected installed Watch Later button {identity}")
        actions[0].text = f"Container.Update({new})"
        actions[1].text = f"RunScript({ROUTE_FOCUS},{new})"
    row = root.find(".//control[@id='9532']/content")
    if row is None or row.text != old:
        raise ValueError("unexpected installed Watch Later row")
    row.text = new
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
