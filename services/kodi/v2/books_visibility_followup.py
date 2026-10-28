"""Exact HP correction for Books mixed AND/OR visibility expressions."""

import hashlib
import xml.etree.ElementTree as ET


PREDECESSOR = "d04c1bfdda056cd55a5c3f2046257a7ea20e63106701b0254f58526203cb486e"
CURRENT_SOURCE = "f7a1956f4d3d0e2ae8aa75d7c6f42ce7e3b62799979381495797fd7a75989d76"
DEPLOYED_SOURCE = "42261b715acbe0a1ef348564313078e71e071f1f3a0bdc3ca21e4120f7e66902"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def render(raw):
    # The first HP candidate was rendered from a pre-branding source which
    # already carried the old page/focus clause.  The current source carries
    # only the catalogue-content clause, while the deployed file has the two
    # clauses as separate <visible> nodes.  Kodi concatenates those nodes
    # without safe grouping and reports "Misplaced !" during skin parsing.
    if sha(raw) not in (PREDECESSOR, CURRENT_SOURCE, DEPLOYED_SOURCE):
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
        if len(nodes) not in (1, 2):
            raise ValueError("books-visibility-contract")
        expression = (nodes[0].text or '').strip()
        if expression.endswith(') + ' + old_selected):
            base = expression[:-len(' + ' + old_selected)]
            if not (base.startswith('(') and base.endswith(')')):
                raise ValueError("books-visibility-base")
            expression = base[1:-1]
        if not expression:
            raise ValueError("books-visibility-base")
        # Keep one visible node and explicitly group both sides of the AND.
        # This is accepted by Kodi's boolean parser and avoids the implicit
        # concatenation it performs when multiple visible nodes are present.
        nodes[0].text = '(' + expression + ') + (' + selected + ')'
        for extra in nodes[1:]:
            control.remove(extra)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
