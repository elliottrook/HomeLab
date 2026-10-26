"""Centre Home's Search + navigation rail, independently of logo and clock."""
import xml.etree.ElementTree as ET
from review2_ui import encoded, field

def build(raw):
    root = ET.fromstring(raw)
    if root.get('id') != '1112':
        raise ValueError('home-header-window')
    groups = [g for g in root.iter('control') if g.get('type') == 'group' and g.find('control[@id="301"]') is not None]
    if len(groups) != 1:
        raise ValueError('home-header-group')
    group = groups[0]
    search = group.find('control[@id="139"]')
    if search is None or search.findtext('left') != '350':
        raise ValueError('home-header-predecessor')
    # The visible Search outline begins at348; rail ends at1386. Shift93
    # makes their combined bounds441..1479, centred on the1920 canvas.
    for control in group.findall('control'):
        left, top = control.findtext('left'), control.findtext('top')
        if left is not None and top is not None and 348 <= int(left) <= 1378 and 0 <= int(top) <= 85:
            field(control, 'left', str(int(left) + 93))
    return encoded(root)
