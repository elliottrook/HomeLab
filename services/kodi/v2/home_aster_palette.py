"""Presentation-only correction: Aster stone, forest green and brushed gold."""
import xml.etree.ElementTree as ET
from home_layered_visual import panel_svg, brush_svg
from review2_ui import encoded, field

FOLDER = 'aster-home-palette-v1'
MEDIA = 'special://skin/media/' + FOLDER + '/'
GREEN = ('#34483a', '#1e3026', '#c2a06b')
CHARCOAL = ('#3b3e33', '#242b23', '#c2a06b')

def assets():
    background = '''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><defs>
    <linearGradient id="stone" x1="0" y1="0" x2="0.8" y2="1"><stop stop-color="#f0e9dd"/><stop offset=".55" stop-color="#e6dac8"/><stop offset="1" stop-color="#d5c5ad"/></linearGradient>
    <radialGradient id="light"><stop stop-color="#fffaf0" stop-opacity=".5"/><stop offset="1" stop-color="#fffaf0" stop-opacity="0"/></radialGradient>
    </defs><rect width="1920" height="1080" fill="url(#stone)"/><ellipse cx="450" cy="210" rx="1100" ry="800" fill="url(#light)"/></svg>'''
    result = {'background': background,
              'camera-panel': panel_svg(560, 510, CHARCOAL, 30),
              'timer-panel': panel_svg(550, 510, GREEN, 30),
              'row': panel_svg(480, 98, CHARCOAL, 26),
              'row-focus': panel_svg(480, 98, ('#286044', '#1f513b', '#f3eee5'), 26)}
    for index, colours in enumerate((GREEN, CHARCOAL, GREEN, CHARCOAL)):
        result['metric-' + str(index)] = panel_svg(395, 116, colours)
    result.update({'arc-' + str(i): brush_svg(i) for i in range(61)})
    return result

def build(raw):
    root = ET.fromstring(raw)
    if root.get('id') != '1112' or root.findtext('onload') != 'RunScript(/storage/.aster-camera/view.py,entry)':
        raise ValueError('home-palette-predecessor')
    field(root, 'backgroundcolor', 'ffe6dac8')
    for node in root.iter():
        if node.text and 'special://skin/media/aster-home-layered-v1/' in node.text:
            node.text = node.text.replace('special://skin/media/aster-home-layered-v1/', MEDIA)
        for key, value in list(node.attrib.items()):
            if 'special://skin/media/aster-home-layered-v1/' in value:
                node.set(key, value.replace('special://skin/media/aster-home-layered-v1/', MEDIA))
    # Heading/caption on stone; ivory text stays on the raised dark cards.
    for node in root.iter('control'):
        if node.get('type') != 'label':
            continue
        top = node.findtext('top')
        if top in ('171', '226', '425', '946'):
            field(node, 'textcolor', 'ff1e241f' if top != '226' else 'ff65675d')
        elif top == '296':
            field(node, 'textcolor', 'ffd6bb8d')
        elif node.findtext('textcolor') == 'ffb7c1cb':
            field(node, 'textcolor', 'ffcec7b8')
    return encoded(root)
