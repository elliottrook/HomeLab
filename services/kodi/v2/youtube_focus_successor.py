"""Delay YouTube landing focus until Kodi has made the root group visible."""

import hashlib
import xml.etree.ElementTree as ET


PREDECESSOR = "63793bc11a3f0b81323527c65b348fdeed64c68f85273f2838399e662c80469b"
COMMAND = "AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:01,silent)"


def transform(raw: bytes) -> bytes:
    if hashlib.sha256(raw).hexdigest() != PREDECESSOR:
        raise ValueError("youtube-focus-predecessor")
    root = ET.fromstring(raw)
    loads = root.findall("onload")
    if len(loads) != 1 or loads[0].text != "SetFocus(9530)":
        raise ValueError("youtube-focus-onload")
    loads[0].text = COMMAND
    result = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    check = ET.fromstring(result)
    if check.findtext("onload") != COMMAND \
            or check.find(".//control[@id='9530']") is None:
        raise ValueError("youtube-focus-result")
    return result
