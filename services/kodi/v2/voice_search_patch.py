"""Exact transformation joining voice results to the accepted grouped Search."""
import xml.etree.ElementTree as ET


def controller(raw):
    old = b"                if command=='back' and artist_enabled:\n"
    new = (b"                if command=='voice':\n"
           b"                    value=home.getProperty(PREFIX+'VoiceQuery')\n"
           b"                    home.clearProperty(PREFIX+'VoiceQuery')\n"
           b"                    try:\n"
           b"                        run_query(value)\n"
           b"                        xbmc.executebuiltin('SetFocus(30)' if any(group.hits for group in groups) else 'SetFocus(10)')\n"
           b"                    except SearchUnavailable:\n"
           b"                        home.setProperty(PREFIX+'Status','Voice search could not be used. Try the keyboard.')\n"
           b"                elif command=='back' and home.getProperty(PREFIX+'VoiceBusy')=='true':\n"
           b"                    home.setProperty(PREFIX+'VoiceCancel','true')\n"
           b"                elif command=='back' and artist_enabled:\n")
    if raw.count(old) != 1:
        raise ValueError('voice-search-controller-predecessor')
    return raw.replace(old, new)


def window(raw):
    root = ET.fromstring(raw)
    field = root.find(".//control[@id='10']")
    if field is None or field.findtext('onclick') != 'SetProperty(AsterSearch.Command,query,home)':
        raise ValueError('voice-search-window-predecessor')
    field.find('width').text = '1190'
    field.find('onright').text = '11'
    controls = root.find('controls')
    if controls is None or root.find(".//control[@id='11']") is not None:
        raise ValueError('voice-search-window-controls')
    button = ET.Element('control', {'type': 'button', 'id': '11'})
    values = (
        ('left', '1590'), ('top', '155'), ('width', '160'), ('height', '70'),
        ('label', 'Voice'), ('font', 'font24'), ('textcolor', 'asterIvory'),
        ('focusedcolor', 'asterIvory'),
        ('texturefocus', 'special://skin/media/ui-panel.png'),
        ('texturenofocus', 'special://skin/media/ui-panel.png'),
        ('align', 'center'), ('aligny', 'center'),
        ('onclick', 'RunScript(script.astervoice.v2lab)'),
        ('ondown', '30'), ('onup', '50'), ('onleft', '10'), ('onright', '10'),
    )
    for name, value in values:
        node = ET.SubElement(button, name)
        node.text = value
        if name == 'texturefocus':
            node.set('border', '24'); node.set('colordiffuse', 'asterGreen')
        elif name == 'texturenofocus':
            node.set('border', '24'); node.set('colordiffuse', 'cc202b25')
    field_index = list(controls).index(field)
    controls.insert(field_index + 1, button)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
