"""Compose Media recommendations onto the accepted v2 Home shell."""

import hashlib
import json
import xml.etree.ElementTree as ET


ACCEPTED_HOME = '5c8e4f5a1d184db06fdc1a65ada51cf93ab9a62c6655ef712e6ad2a41b744176'
ACCEPTED_SEARCH = '6f1fbe60d9d1ef9187ad0524602268145c9412c5d2c886c104243103b692e55e'
ACCEPTED_SEARCH_MANIFEST = '3637230db1859df2d9dabdda487b08666f49a85eff7813ce2cd049c108227e1d'
IDLE = '!Control.HasFocus(100) + !Control.HasFocus(110)'


def require(value, code):
    if not value:
        raise ValueError(code)


def field(control, name, value, **attributes):
    node = control.find(name)
    if node is None:
        node = ET.SubElement(control, name, attributes)
    else:
        node.attrib.clear(); node.attrib.update(attributes)
    node.text = str(value)
    return node


def action(control, value, **attributes):
    node = ET.SubElement(control, 'onclick', attributes)
    node.text = value
    return node


def transform(raw):
    require(hashlib.sha256(raw).hexdigest() == ACCEPTED_HOME,
            'media-hero-home-predecessor')
    root = ET.fromstring(raw)
    default = root.find('defaultcontrol')
    root.insert(list(root).index(default) + 1, ET.Element('onload'))
    root.find('onload').text = (
        'AlarmClock(AsterMediaHero,RunScript(special://home/addons/'
        'plugin.video.asterhome/default.py,hero-tick),00:12,silent,loop)')
    root.insert(list(root).index(root.find('onload')) + 1, ET.Element('onunload'))
    root.find('onunload').text = 'CancelAlarm(AsterMediaHero,silent)'

    source = root.find(".//control[@id='101']")
    require(source is not None, 'media-hero-source')
    field(source, 'left', '-5'); field(source, 'top', '-5')
    visible = source.find('visible')
    if visible is not None:
        source.remove(visible)
    field(source, 'content',
          'plugin://plugin.video.asterhome/?mode=recommended', target='videos')

    recent = root.find(".//control[@id='110']")
    require(recent is not None, 'media-hero-recent-source')
    field(recent, 'content', 'plugin://plugin.video.asterhome/?mode=recent',
          target='videos')
    recent_label = next((node for node in root.findall(".//control[@type='label']")
                         if node.findtext('label') == 'Recommended for You'), None)
    require(recent_label is not None, 'media-hero-recent-label')
    field(recent_label, 'label', 'Recently Added')

    hero = root.find(".//control[@id='21']")
    require(hero is not None, 'media-hero-copy')
    synopsis = next((node for node in hero.findall('control')
                     if node.get('type') == 'textbox'
                     and node.findtext('label', '').endswith('[AsterHeroPlot]')),
                    None)
    require(synopsis is not None, 'media-hero-synopsis')
    # Keep a deliberate gap below the 70px title.  The former 313px origin
    # touched the title as soon as the synopsis moved up to font20.
    field(synopsis, 'top', '318'); field(synopsis, 'height', '86')
    field(synopsis, 'font', 'font20')
    rating = next((node for node in hero.findall('control')
                   if node.get('type') == 'label'
                   and node.findtext('label', '').endswith('[AsterHeroRating]')),
                  None)
    require(rating is not None, 'media-hero-rating')
    field(rating, 'top', '408')

    play = hero.find("control[@id='120']")
    info = hero.find("control[@id='121']")
    require(play is not None and info is not None, 'media-hero-actions')
    for control, left, width in ((play, 145, 180), (info, 340, 165)):
        field(control, 'visible', IDLE)
        field(control, 'left', left); field(control, 'top', 442)
        field(control, 'width', width); field(control, 'height', 44)
        field(control, 'font', 'font20')
        field(control, 'texturefocus', 'special://skin/media/ui-panel.png',
              border='18', colordiffuse='ff005c46')
        field(control, 'texturenofocus', 'special://skin/media/ui-panel.png',
              border='18', colordiffuse='66000000')
        field(control, 'textcolor', 'asterIvory')
        field(control, 'focusedcolor', 'asterIvory')
    field(play, 'onright', 121)
    for node in list(play.findall('onclick')):
        play.remove(node)
    action(play, 'ActivateWindow(videos,$VAR[AsterHeroPath],return)',
           condition='String.IsEqual($VAR[AsterHeroKind],tvshow)')
    action(play, 'PlayMedia($VAR[AsterHeroPath])',
           condition='!String.IsEqual($VAR[AsterHeroKind],tvshow)')

    for node in list(info.findall('onclick')):
        info.remove(node)
    action(info, 'SetFocus(101)')
    action(info, 'Action(Info)')
    action(info, 'SetFocus(121)')
    field(info, 'onleft', 120); field(info, 'onright', 122)

    next_button = ET.Element('control', {'type': 'button', 'id': '122'})
    for name, value in (
            ('visible', IDLE), ('left', 520), ('top', 442), ('width', 120),
            ('height', 44), ('label', 'Next  ›'), ('font', 'font20'),
            ('align', 'center'), ('aligny', 'center'), ('textcolor', 'asterIvory'),
            ('focusedcolor', 'asterIvory'), ('onleft', 121), ('onright', 120),
            ('onup', 136), ('ondown', 100), ('onclick', 'Control.Move(101,1)')):
        field(next_button, name, value)
    field(next_button, 'texturefocus', 'special://skin/media/ui-panel.png',
          border='18', colordiffuse='ff005c46')
    field(next_button, 'texturenofocus', 'special://skin/media/ui-panel.png',
          border='18', colordiffuse='66000000')
    hero.insert(list(hero).index(info) + 1, next_button)

    rings = [node for node in hero.findall('control')
             if node.get('type') == 'image'
             and node.findtext('texture') == 'special://skin/media/ui-button-ring.png']
    require(len(rings) == 2, 'media-hero-rings')
    for ring, identity, left, width in ((rings[0], 120, 145, 180),
                                        (rings[1], 121, 340, 165)):
        field(ring, 'visible', f'{IDLE} + Control.HasFocus({identity})')
        field(ring, 'left', left); field(ring, 'top', 442)
        field(ring, 'width', width); field(ring, 'height', 44)
    ring = ET.Element('control', {'type': 'image'})
    for name, value in (('visible', IDLE + ' + Control.HasFocus(122)'),
                        ('left', 520), ('top', 442), ('width', 120),
                        ('height', 44),
                        ('texture', 'special://skin/media/ui-button-ring.png')):
        field(ring, name, value)
    hero.insert(list(hero).index(rings[1]) + 1, ring)

    result = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    check = ET.fromstring(result)
    require(check.find(".//control[@id='135']") is not None
            and check.find(".//control[@id='136']") is not None
            and check.find(".//control[@id='137']") is not None,
            'media-hero-header-regression')
    return result


def update_search_manifest(raw, search):
    """Pin the installed search component to its revised native window."""
    value = json.loads(raw)
    require(value.get('component') == 'aster-global-search-ui22',
            'media-hero-search-manifest-kind')
    rows = value.get('files', [])
    row = next((item for item in rows
                if item.get('path') == 'overlay/custom_1127_search.xml'), None)
    require(row is not None and row.get('sha256') == ACCEPTED_SEARCH,
            'media-hero-search-manifest-predecessor')
    row['bytes'] = len(search)
    row['sha256'] = hashlib.sha256(search).hexdigest()
    return (json.dumps(value, indent=2) + '\n').encode()


def update_family_manifest(raw, home, search, search_manifest):
    """Keep the installed runtime integrity contract coherent after composition."""
    value = json.loads(raw)
    require(value.get('kind') == 'aster-family-runtime.v1',
            'media-hero-family-manifest-kind')
    skin = value.get('skin', {})
    component = value.get('components', {}).get('aster-global-search-ui22', {})
    require(skin.get('1080i/Home.xml') == ACCEPTED_HOME
            and skin.get('1080i/custom_1127_search.xml') == ACCEPTED_SEARCH
            and component.get('manifest_sha256') == ACCEPTED_SEARCH_MANIFEST,
            'media-hero-family-manifest-predecessor')
    skin['1080i/Home.xml'] = hashlib.sha256(home).hexdigest()
    skin['1080i/custom_1127_search.xml'] = hashlib.sha256(search).hexdigest()
    component['manifest_sha256'] = hashlib.sha256(search_manifest).hexdigest()
    return (json.dumps(value, indent=2) + '\n').encode()
