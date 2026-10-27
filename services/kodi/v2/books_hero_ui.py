"""Pure transforms for the owned-library Books recommendation hero."""
import xml.etree.ElementTree as ET


def field(parent, name, value):
    node = ET.SubElement(parent, name); node.text = str(value); return node


def extend_books_data(source):
    text = source.decode()
    anchor = "from hub_feeds import book_catalogue, read_feed\n"
    addition = """from books_landing import landing_rows
from owned_landing import normalize, recently_added, recommendations
import json
"""
    if text.count(anchor) != 1 or addition in text:
        raise ValueError('books-hero-import-anchor')
    text = text.replace(anchor, anchor + addition)
    marker = "\ndef main(page, action='load'):\n"
    helpers = r'''

def _hero_rows(records, cover_root):
    items = normalize(landing_rows(records,
        lambda row: cached_cover(cover_root, row)), 'books')
    recent = tuple(item for kind in ('ebook', 'audiobook', 'podcast')
                   for item in recently_added(tuple(row for row in items
                                                    if row.media_type == kind)))
    return [dict(identity=item.identity, kind=item.media_type, title=item.title,
                 detail=item.detail, synopsis=item.synopsis,
                 artwork=item.artwork, backdrop=item.backdrop,
                 reason=item.recommendation_reason)
            for item in recommendations(items, recent)]


def _set_hero(window, rows, index):
    for name in ('Title', 'Detail', 'Synopsis', 'Artwork', 'Backdrop',
                 'Reason', 'Kind', 'Id', 'Action'):
        window.clearProperty('AsterBooks.Hero' + name)
    if not rows:
        window.setProperty('AsterBooks.HeroIndex', '0')
        window.setProperty('AsterBooks.HeroCount', '0')
        return
    index %= len(rows); row = rows[index]
    identity = row.get('identity', '')
    authority, separator, source_id = identity.partition(':')
    kind = row.get('kind')
    if (separator != ':' or kind not in ('ebook', 'audiobook', 'podcast')
            or authority != ('calibre' if kind == 'ebook' else 'audiobookshelf')
            or not source_id):
        raise ValueError('books-hero-identity')
    action = 'Read' if kind == 'ebook' else 'Listen'
    values = dict(Title=row.get('title', ''), Detail=row.get('detail', ''),
                  Synopsis=row.get('synopsis', ''), Artwork=row.get('artwork', ''),
                  Backdrop=row.get('backdrop', ''), Reason=row.get('reason', ''),
                  Kind=kind, Id=source_id, Action=action)
    for name, value in values.items():
        window.setProperty('AsterBooks.Hero' + name, str(value or '')[:3000])
    window.setProperty('AsterBooks.HeroIndex', str(index))
    window.setProperty('AsterBooks.HeroCount', str(len(rows)))


def load_books_hero(window, records, cover_root):
    try:
        rows = _hero_rows(records, cover_root)
        window.setProperty('AsterBooks.HeroRows', json.dumps(rows, separators=(',', ':')))
        _set_hero(window, rows, 0)
    except (ValueError, KeyError, TypeError):
        window.clearProperty('AsterBooks.HeroRows'); _set_hero(window, [], 0)


def books_hero_action(xbmc, xbmcgui, action, records):
    window = xbmcgui.Window(PAGES['home'])
    try:
        raw = window.getProperty('AsterBooks.HeroRows')
        if not raw or len(raw) > 65536:return
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) > 12:return
        index = int(window.getProperty('AsterBooks.HeroIndex') or 0)
        if action in ('hero-next', 'hero-tick'):
            if action == 'hero-tick' and window.getFocusId() in HOME_CONTROLS.values():return
            _set_hero(window, rows, index + 1); return
        kind = window.getProperty('AsterBooks.HeroKind')
        identity = window.getProperty('AsterBooks.HeroId')
        row = next((item for item in records
                    if item['kind'] == kind and item['id'] == identity), None)
        if row is None:return
        if action == 'hero-open':
            xbmcgui.Dialog().textviewer(row['title'],
                row['synopsis'] or 'No synopsis available for this title.')
        elif action == 'hero-activate':activate_row(row, xbmc, xbmcgui)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):return
'''
    if text.count(marker) != 1:
        raise ValueError('books-hero-main-anchor')
    text = text.replace(marker, helpers + marker)
    records_anchor = """    if action in ('open', 'activate'):
"""
    records_replacement = """    if page == 'home' and action.startswith('hero-'):
        books_hero_action(xbmc, xbmcgui, action, records)
        return

    if action in ('open', 'activate'):
"""
    if text.count(records_anchor) != 1:
        raise ValueError('books-hero-dispatch-anchor')
    text = text.replace(records_anchor, records_replacement)
    focus = """        if action == 'load':
            first_row = next((HOME_CONTROLS[kind] for kind in
                              ('ebook', 'audiobook', 'podcast') if counts[kind]), None)
            if first_row is not None:
                xbmc.executebuiltin(f'Control.SetFocus({first_row},0,absolute)')
"""
    replacement = """        load_books_hero(window, records, cover_root)
"""
    if text.count(focus) != 1:
        raise ValueError('books-hero-focus-anchor')
    return text.replace(focus, replacement).encode()


def button(identity, left, width, label, action, left_id, right_id):
    node = ET.Element('control', {'type': 'button', 'id': str(identity)})
    for name, value in (('left', left), ('top', 454), ('width', width), ('height', 48),
        ('label', label), ('font', 'font20'), ('align', 'center'), ('aligny', 'center'),
        ('textcolor', 'asterIvory'), ('focusedcolor', 'asterIvory'),
        ('onleft', left_id), ('onright', right_id), ('onup', 111), ('ondown', 501),
        ('onclick', 'RunScript(special://skin/tools/books_data.py,home,' + action + ')'),
        ('visible', 'Window.IsActive(1110) + !Control.HasFocus(501) + '
                    '!Control.HasFocus(502) + !Control.HasFocus(503) + '
                    '!String.IsEmpty(Window.Property(AsterBooks.HeroId))')):
        field(node, name, value)
    focus = field(node, 'texturefocus', 'special://skin/media/ui-panel.png')
    focus.set('border', '18'); focus.set('colordiffuse', 'ff005c46')
    idle = field(node, 'texturenofocus', 'special://skin/media/ui-panel.png')
    idle.set('border', '18'); idle.set('colordiffuse', '52000000')
    return node


def extend_includes(source):
    root = ET.fromstring(source)
    include = root.find("include[@name='AsterBooksPage']")
    definition = include.find('definition') if include is not None else None
    group = next((node for node in definition.findall('control')
                  if node.get('type') == 'group' and node.find("control[@id='110']") is not None), None)
    if include is None or definition is None or group is None:
        raise ValueError('books-hero-template')
    field(include, 'param', '') if False else None

    selected_art = ET.Element('variable', {'name': 'AsterBooksSelectedArt'})
    for condition, value in (
        ('Control.HasFocus(501)', '$INFO[Container(501).ListItem.Art(thumb)]'),
        ('Control.HasFocus(502)', '$INFO[Container(502).ListItem.Art(thumb)]'),
        ('Control.HasFocus(503)', '$INFO[Container(503).ListItem.Art(thumb)]'),
        ('!String.IsEmpty(Container(500).ListItem.Art(thumb))',
         '$INFO[Container(500).ListItem.Art(thumb)]')):
        node=field(selected_art,'value',value);node.set('condition',condition)
    field(selected_art,'value','$PARAM[icon]')
    root.insert(list(root).index(include),selected_art)

    # Hero image layers sit above the base surfaces but below page controls.
    first_group = next(node for node in definition.findall('control') if node.get('type') == 'group')
    backdrop = ET.Element('control', {'type': 'image'})
    for name, value in (('left', 0), ('top', 0), ('width', 1920), ('height', 1080),
                        ('texture', '$INFO[Window.Property(AsterBooks.HeroBackdrop)]'),
                        ('aspectratio', 'scale'), ('fadetime', 250),
                        ('colordiffuse', '88FFFFFF'),
                        ('visible', 'Window.IsActive(1110) + !Control.HasFocus(501) + '
                                    '!Control.HasFocus(502) + !Control.HasFocus(503)')):
        field(backdrop, name, value)
    definition.insert(list(definition).index(first_group), backdrop)

    for identity in (110, 111, 112, 139):
        control = group.find("control[@id='%s']" % identity)
        if control is None or control.find('ondown') is None:raise ValueError('books-hero-top-navigation')
        control.find('ondown').text = '305'

    generic = next((node for node in group.findall('control')
                    if node.get('type') == 'image' and node.findtext('left') == '220'
                    and node.findtext('top') == '200'), None)
    if generic is None:raise ValueError('books-hero-art')
    generic.find('texture').text = '$VAR[AsterBooksSelectedArt]'
    colour = generic.find('colordiffuse')
    if colour is not None:generic.remove(colour)
    field(generic, 'visible', '!Window.IsActive(1110) | Control.HasFocus(501) | Control.HasFocus(502) | Control.HasFocus(503)')
    art = ET.Element('control', {'type': 'image'})
    for name, value in (('left', 220), ('top', 174), ('width', 320), ('height', 320),
                        ('texture', '$INFO[Window.Property(AsterBooks.HeroArtwork)]'),
                        ('aspectratio', 'keep'),
                        ('visible', 'Window.IsActive(1110) + !Control.HasFocus(501) + '
                                    '!Control.HasFocus(502) + !Control.HasFocus(503)')):
        field(art, name, value)
    group.insert(list(group).index(generic) + 1, art)

    selected = ('!Window.IsActive(1110) | Control.HasFocus(501) | '
                'Control.HasFocus(502) | Control.HasFocus(503)')
    labels = [(160, '$PARAM[heading]', 'Recommended for You', 'font24', 38, 'asterGold'),
              (214, '$VAR[AsterBooksHeroTitle]', '$INFO[Window.Property(AsterBooks.HeroTitle)]', 'font30', 110, 'asterRailText'),
              (330, '$VAR[AsterBooksHeroDetail]', '$INFO[Window.Property(AsterBooks.HeroSynopsis)]', 'font20', 70, 'asterRailText'),
              (406, '$INFO[Window.Property(AsterBooks.Status)]', '$INFO[Window.Property(AsterBooks.HeroReason)]', 'font20', 34, 'asterSage')]
    for top, original, hero_value, font, height, colour in labels:
        current = next((node for node in group.findall('control')
                        if node.findtext('top') == str(top) and node.findtext('label') == original), None)
        if current is None:raise ValueError('books-hero-label')
        field(current, 'visible', selected)
        hero = ET.Element('control', {'type': current.get('type')})
        for name, value in (('left', 1050), ('top', top), ('width', 710), ('height', height),
                            ('label', hero_value), ('font', font), ('textcolor', colour),
                            ('visible', 'Window.IsActive(1110) + !Control.HasFocus(501) + '
                                        '!Control.HasFocus(502) + !Control.HasFocus(503)')):
            field(hero, name, value)
        group.insert(list(group).index(current) + 1, hero)

    for identity in (300, 304):
        existing = group.find("control[@id='%s']" % identity)
        if existing is None:raise ValueError('books-hero-existing-action')
        visible = existing.find('visible')
        visible.text = '(' + visible.text + ') + ' + selected
    for node in (button(305, 1050, 150, 'About', 'hero-open', 307, 306),
                 button(306, 1212, 180, '$INFO[Window.Property(AsterBooks.HeroAction)]',
                        'hero-activate', 305, 307),
                 button(307, 1404, 130, 'Next', 'hero-next', 306, 305)):
        group.append(node)

    for identity, title in ((501, 'Recently Added eBooks'),
                            (502, 'Recently Added Audiobooks'),
                            (503, 'Recently Added Podcasts')):
        row_include = next((node for node in group.findall(".//include[@content='AsterBooksHomeRow']")
                            if any(param.get('name') == 'id' and param.get('value') == str(identity)
                                   for param in node.findall('param'))), None)
        if row_include is None:raise ValueError('books-hero-row')
        up = next((param for param in row_include.findall('param')
                   if param.get('name') == 'up'), None)
        if up is None:raise ValueError('books-hero-row-up')
        up.set('value', '305' if identity == 501 else str(identity - 1))
        row_top = {'501': '520', '502': '700', '503': '880'}[str(identity)]
        heading = next((node for node in group.findall('.//control')
                        if node.get('type') == 'label' and node.findtext('top') == row_top), None)
        if heading is None:raise ValueError('books-hero-row-label')
        heading.find('label').text = title
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def extend_home(source):
    root = ET.fromstring(source)
    default = root.find('defaultcontrol'); controls = root.find('controls')
    if default is None or controls is None:raise ValueError('books-hero-home')
    default.text = '110'
    onload = ET.Element('onload'); onload.text = ('AlarmClock(AsterBooksHero,RunScript('
        'special://skin/tools/books_data.py,home,hero-tick),00:12,silent,loop)')
    onunload = ET.Element('onunload'); onunload.text = 'CancelAlarm(AsterBooksHero,silent)'
    position = list(root).index(controls); root.insert(position, onload); root.insert(position + 1, onunload)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
