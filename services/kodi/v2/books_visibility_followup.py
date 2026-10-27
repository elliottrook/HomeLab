"""Exact HP correction for Books mixed AND/OR visibility expressions."""

import hashlib
import xml.etree.ElementTree as ET


PREDECESSOR = "d04c1bfdda056cd55a5c3f2046257a7ea20e63106701b0254f58526203cb486e"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def render(raw):
    if sha(raw) != PREDECESSOR:
        raise ValueError("books-visibility-predecessor")
    text = raw.decode()
    selected = ("Window.IsActive(1118) | Window.IsActive(1119) | "
                "Window.IsActive(1120) | Control.HasFocus(501) | "
                "Control.HasFocus(502) | Control.HasFocus(503)")
    old_selected = ("!Window.IsActive(1110) | Control.HasFocus(501) | "
                    "Control.HasFocus(502) | Control.HasFocus(503)")
    root = ET.fromstring(text)
    for identity in ('300', '304'):
        control = root.find(".//control[@id='%s']" % identity)
        nodes = control.findall('visible') if control is not None else []
        if len(nodes) != 1 or not nodes[0].text.endswith(') + ' + old_selected):
            raise ValueError("books-visibility-contract")
        base = nodes[0].text[:-len(' + ' + old_selected)]
        if not (base.startswith('(') and base.endswith(')')):
            raise ValueError("books-visibility-base")
        nodes[0].text = base[1:-1]
        extra = ET.SubElement(control, 'visible'); extra.text = selected
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
