"""Pure transforms for the owned-library Music recommendation hero."""
import xml.etree.ElementTree as ET


def _field(parent, name, value):
    node = ET.SubElement(parent, name)
    node.text = str(value)
    return node


def extend_music_data(source):
    text = source.decode()
    imports = "from aster_v2_music import handoff, restore_focus\n"
    addition = """from music_landing import fetch_albums, landing_rows
from owned_landing import normalize, recently_added, recommendations
import json
from datetime import datetime
"""
    if text.count(imports) != 1 or addition in text:
        raise ValueError('music-hero-import-anchor')
    text = text.replace(imports, imports + addition)
    marker = "\ndef main(page, action='load'):\n"
    helpers = r'''

def _hero_rows(xbmc):
    albums = fetch_albums(lambda method, params: kodi_rpc(xbmc, method, params))
    raw_offset = datetime.now().astimezone().strftime('%z')
    offset = raw_offset[:3] + ':' + raw_offset[3:]
    items = normalize(landing_rows(albums, source_offset=offset), 'music')
    recent = recently_added(items)
    return [dict(identity=item.identity, title=item.title, detail=item.detail,
                 synopsis=item.synopsis, artwork=item.artwork,
                 backdrop=item.backdrop, reason=item.recommendation_reason)
            for item in recommendations(items, recent)]


def _set_hero(window, rows, index):
    for name in ('Title', 'Detail', 'Synopsis', 'Artwork', 'Backdrop', 'Reason', 'Id'):
        window.clearProperty('AsterMusic.Hero' + name)
    if not rows:
        window.setProperty('AsterMusic.HeroIndex', '0')
        window.setProperty('AsterMusic.HeroCount', '0')
        return
    index = index % len(rows)
    row = rows[index]
    identity = row.get('identity', '')
    if not identity.startswith('kodi:album-') or not identity[11:].isdigit():
        raise ValueError('music-hero-identity')
    values = dict(Title=row.get('title', ''), Detail=row.get('detail', ''),
                  Synopsis=row.get('synopsis', ''), Artwork=row.get('artwork', ''),
                  Backdrop=row.get('backdrop', ''), Reason=row.get('reason', ''),
                  Id=identity[11:])
    for name, value in values.items():
        window.setProperty('AsterMusic.Hero' + name, str(value or '')[:3000])
    window.setProperty('AsterMusic.HeroIndex', str(index))
    window.setProperty('AsterMusic.HeroCount', str(len(rows)))


def load_music_hero(xbmc, window):
    try:
        rows = _hero_rows(xbmc)
        window.setProperty('AsterMusic.HeroRows', json.dumps(rows, separators=(',', ':')))
        _set_hero(window, rows, 0)
    except (ValueError, KeyError, TypeError):
        window.clearProperty('AsterMusic.HeroRows')
        _set_hero(window, [], 0)


def music_hero_action(xbmc, xbmcgui, action):
    window = xbmcgui.Window(PAGES['home'])
    try:
        raw = window.getProperty('AsterMusic.HeroRows')
        if not raw or len(raw) > 65536:
            return
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) > 12:
            return
        index = int(window.getProperty('AsterMusic.HeroIndex') or 0)
        if action in ('hero-next', 'hero-tick'):
            if action == 'hero-tick' and window.getFocusId() == 500:
                return
            _set_hero(window, rows, index + 1)
            return
        identifier = window.getProperty('AsterMusic.HeroId')
        if not identifier.isdigit():
            return
        if action == 'hero-play':
            play_album(xbmc, int(identifier))
        elif action == 'hero-open':
            if handoff(xbmc, xbmcgui, 'home', identifier):
                return
            row = rows[index % len(rows)]
            pending = xbmcgui.Window(10000)
            for name, value in dict(Kind='album', Id=identifier,
                                    Title=row.get('title', ''),
                                    Artist=row.get('detail', ''),
                                    Cover=row.get('artwork', ''), Path='').items():
                pending.setProperty('AsterMusic.Pending' + name, str(value or ''))
            xbmc.executebuiltin('ActivateWindow(1121)')
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return
'''
    if text.count(marker) != 1:
        raise ValueError('music-hero-main-anchor')
    text = text.replace(marker, helpers + marker)
    dispatch = "    if page == 'music-player':\n"
    replacement = """    if page == 'home' and action.startswith('hero-'):
        music_hero_action(xbmc, xbmcgui, action)
        return
    if page == 'music-player':
"""
    if text.count(dispatch) != 1:
        raise ValueError('music-hero-dispatch-anchor')
    text = text.replace(dispatch, replacement)
    completion = "    window.setProperty('AsterMusic.LoadReady', 'true')\n"
    replacement = """    if page == 'home':
        load_music_hero(xbmc, window)
    window.setProperty('AsterMusic.LoadReady', 'true')
"""
    if text.count(completion) != 1:
        raise ValueError('music-hero-load-anchor')
    return text.replace(completion, replacement).encode()


def _button(identity, left, width, label, action, left_id, right_id):
    control = ET.Element('control', {'type': 'button', 'id': str(identity)})
    for name, value in (
            ('left', left), ('top', 448), ('width', width), ('height', 48),
            ('label', label), ('font', 'font20'), ('align', 'center'),
            ('aligny', 'center'), ('textcolor', 'asterIvory'),
            ('focusedcolor', 'asterIvory'), ('onleft', left_id),
            ('onright', right_id), ('onup', 110), ('ondown', 500),
            ('onclick', 'RunScript(special://skin/tools/music_data.py,home,' + action + ')'),
            ('visible', 'Window.IsActive(11113) + !Control.HasFocus(500) + '
                        '!String.IsEmpty(Window.Property(AsterMusic.HeroId))')):
        _field(control, name, value)
    focus = _field(control, 'texturefocus', 'special://skin/media/ui-panel.png')
    focus.set('border', '18'); focus.set('colordiffuse', 'ff005c46')
    idle = _field(control, 'texturenofocus', 'special://skin/media/ui-panel.png')
    idle.set('border', '18'); idle.set('colordiffuse', '52000000')
    return control


def extend_includes(source):
    root = ET.fromstring(source)
    include = root.find("include[@name='AsterMusicPage']")
    definition = include.find('definition') if include is not None else None
    group = next((node for node in definition.findall('control')
                  if node.get('type') == 'group' and node.find("control[@id='500']") is not None), None)
    if include is None or definition is None or group is None:
        raise ValueError('music-hero-template')
    params = {node.get('name') for node in include.findall('param')}
    if 'topdown' in params or 'landing' in params:
        raise ValueError('music-hero-already-applied')
    include.insert(0, ET.Element('param', {'name': 'topdown', 'default': '500'}))
    include.insert(0, ET.Element('param', {'name': 'landing', 'default': 'false'}))

    fanart = next((node for node in definition.findall('control')
                   if node.findtext('texture') == '$INFO[Container(500).ListItem.Art(fanart)]'), None)
    if fanart is None:
        raise ValueError('music-hero-fanart')
    _field(fanart, 'visible', '!Window.IsActive(11113) | Control.HasFocus(500)')
    recommendation = ET.Element('control', {'type': 'image'})
    for name, value in (('left', 0), ('top', 0), ('width', 1920), ('height', 620),
                        ('texture', '$INFO[Window.Property(AsterMusic.HeroBackdrop)]'),
                        ('aspectratio', 'scale'), ('fadetime', 250),
                        ('visible', 'Window.IsActive(11113) + !Control.HasFocus(500)')):
        _field(recommendation, name, value)
    definition.insert(list(definition).index(fanart), recommendation)

    for identity in (110, 111, 112, 113, 114, 139):
        control = group.find("control[@id='%s']" % identity)
        if control is None or control.find('ondown') is None:
            raise ValueError('music-hero-top-navigation')
        control.find('ondown').text = '$PARAM[topdown]'
    panel = group.find("control[@id='500']")
    panel.find('onup').text = '$PARAM[gridup]'

    old = group.find("control[@id='115']")
    if old is None:
        raise ValueError('music-hero-shuffle')
    group.remove(old)
    for node in (
            _button(116, 1050, 138, 'Play', 'hero-play', 115, 117),
            _button(117, 1200, 180, 'Open album', 'hero-open', 116, 118),
            _button(118, 1392, 130, 'Next', 'hero-next', 117, 115),
            _button(115, 1534, 190, 'Shuffle all', 'hero-shuffle', 118, 116)):
        group.append(node)
    # Shuffle remains the established bounded integration action.
    group.find("control[@id='115']/onclick").text = (
        'RunScript(special://skin/tools/aster_v2_music.py,shuffle,home)')

    def duplicate_label(top, source_info, hero_info, font, height, colour='asterRailText'):
        current = next((node for node in group.findall('control')
                        if node.get('type') in ('label', 'textbox')
                        and node.findtext('top') == str(top)
                        and node.findtext('label') == source_info), None)
        if current is None:
            raise ValueError('music-hero-label')
        _field(current, 'visible', '!Window.IsActive(11113) | Control.HasFocus(500)')
        hero = ET.Element('control', {'type': current.get('type')})
        for name, value in (('left', 1050), ('top', top), ('width', 710),
                            ('height', height), ('label', hero_info), ('font', font),
                            ('textcolor', colour),
                            ('visible', 'Window.IsActive(11113) + !Control.HasFocus(500)')):
            _field(hero, name, value)
        group.insert(list(group).index(current) + 1, hero)

    heading = next((node for node in group.findall('control')
                    if node.get('type') == 'label' and node.findtext('top') == '163'), None)
    if heading is None:
        raise ValueError('music-hero-heading')
    _field(heading, 'visible', '!Window.IsActive(11113) | Control.HasFocus(500)')
    hero_heading = ET.Element('control', {'type': 'label'})
    for name, value in (('left', 1050), ('top', 163), ('width', 700), ('height', 38),
                        ('label', 'Recommended for You'), ('font', 'font24'),
                        ('textcolor', 'asterGold'),
                        ('visible', 'Window.IsActive(11113) + !Control.HasFocus(500)')):
        _field(hero_heading, name, value)
    group.insert(list(group).index(heading) + 1, hero_heading)
    duplicate_label(214, '$INFO[Container(500).ListItem.Label]',
                    '$INFO[Window.Property(AsterMusic.HeroTitle)]', 'font40', 68)
    duplicate_label(288, '$INFO[Container(500).ListItem.Property(AsterMusic.Summary)]',
                    '$INFO[Window.Property(AsterMusic.HeroSynopsis)]', 'font24', 85)
    duplicate_label(386, '$INFO[Window.Property(AsterMusic.Status)]',
                    '$INFO[Window.Property(AsterMusic.HeroReason)]', 'font20', 32,
                    'asterSage')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def extend_home(source):
    root = ET.fromstring(source)
    default = root.find('defaultcontrol')
    include = root.find(".//include[@content='AsterMusicPage']")
    if default is None or include is None:
        raise ValueError('music-hero-home')
    default.text = '110'
    for node in include.findall('param'):
        if node.get('name') == 'gridup':
            node.set('value', '116')
    ET.SubElement(include, 'param', {'name': 'topdown', 'value': '116'})
    ET.SubElement(include, 'param', {'name': 'landing', 'value': 'true'})
    onload = ET.Element('onload')
    onload.text = ('AlarmClock(AsterMusicHero,RunScript(special://skin/tools/'
                   'music_data.py,home,hero-tick),00:12,silent,loop)')
    onunload = ET.Element('onunload'); onunload.text = 'CancelAlarm(AsterMusicHero,silent)'
    controls = root.find('controls')
    position = list(root).index(controls)
    root.insert(position, onload); root.insert(position + 1, onunload)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
