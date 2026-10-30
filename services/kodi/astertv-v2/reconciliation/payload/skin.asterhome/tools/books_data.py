"""Aster Books catalogue, synopsis and bounded reader handoffs.

The feed has sanitized descriptions but no file paths, media URLs or secrets.
Cover JPEGs come from a separate validated private cache. Validated source IDs
may hand off to Calibre-Web or the installed Audiobookshelf add-on; neither
route grants access on its own, and the audio bridge still requires a private
credential and HTTPS endpoint.
"""

import sys
import hashlib
import re
import stat
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

from hub_feeds import book_catalogue, read_feed
from books_landing import landing_rows
from owned_landing import normalize, recently_added, recommendations
import json


PAGES = {'home': 11110, 'ebooks': 11118, 'audiobooks': 11119,
         'podcasts': 11120}
KINDS = {'ebooks': 'ebook', 'audiobooks': 'audiobook',
         'podcasts': 'podcast'}
ICONS = {'ebook': '11-books.png', 'audiobook': '12-audiobooks.png',
         'podcast': 'aster-compass-128.png'}
HOME_CONTROLS = {'ebook': 501, 'audiobook': 502, 'podcast': 503}
AUDIO_ADDON = 'plugin.audio.asterbooks'
READER_BASE = 'https://books.elliottrook.com'
COMPILED_READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')
COMPILED_READER_STATE = Path('/storage/.aster-state/aster-books-compiler-reader-v1')
COMPILED_OUTPUT = Path('/storage/aster-reader')
SHA256 = re.compile(r'[a-f0-9]{64}')
MAX_READER_RECORD = 4096


def page_records(records, page, query=''):
    """Return real rows, ordering only from source-owned item timestamps."""
    kind = KINDS.get(page)
    selected = [row for row in records if kind is None or row['kind'] == kind]
    if query:
        term = query.casefold()
        selected = [row for row in selected if term in row['title'].casefold()]
    if page == 'home' or kind is not None:
        selected = sorted(selected,
                          key=lambda row: (row.get('added_at') or '',
                                           row['title'].casefold()),
                          reverse=True)
    return selected[:1000]


def cover_filename(row):
    """Stable opaque cache key; no source path or title reaches the skin."""
    identity = (row['kind'] + ':' + row['id']).encode('utf-8')
    return hashlib.sha256(identity).hexdigest() + '.jpg'


def cached_cover(root, row):
    """Accept only a small regular JPEG in the skin's private cache."""
    path = Path(root) / cover_filename(row)
    try:
        metadata = path.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= 1024 * 1024:
        return None
    try:
        with path.open('rb') as handle:
            if handle.read(3) != b'\xff\xd8\xff':
                return None
    except OSError:
        return None
    return str(path)


def make_item(xbmcgui, row, cover_root=None):
    item = xbmcgui.ListItem(row['title'], row['detail'])
    cover = cached_cover(cover_root, row) if cover_root else None
    item.setArt({'thumb': cover or 'special://skin/media/' + ICONS[row['kind']]})
    item.setProperty('AsterBooks.HasCover', 'true' if cover else 'false')
    item.setProperty('AsterBooks.Kind', row['kind'])
    item.setProperty('AsterBooks.Id', row['id'])
    item.setProperty('AsterBooks.Summary', row.get('synopsis', ''))
    return item


def selected_row(window, page, records, info_label=None):
    """Resolve only a row currently present in the approved local feed."""
    controls = (500,) if page != 'home' else (502, 501, 503)
    focused = window.getFocusId()
    order = ([focused] if focused in controls else []) + [id for id in controls if id != focused]
    for control_id in order:
        try:
            item = window.getControl(control_id).getSelectedItem()
        except (AttributeError, RuntimeError):
            item = None
        kind = item.getProperty('AsterBooks.Kind') if item is not None else ''
        identity = item.getProperty('AsterBooks.Id') if item is not None else ''
        if info_label is not None and (not kind or not identity):
            # Kodi may return a selected ListItem before its custom properties
            # have propagated; use the focused container's current item then.
            kind = kind or info_label(f'Container({control_id}).ListItem.Property(AsterBooks.Kind)')
            identity = identity or info_label(f'Container({control_id}).ListItem.Property(AsterBooks.Id)')
        if not kind or not identity:
            continue
        match = next((row for row in records if row['kind'] == kind and row['id'] == identity), None)
        if match:
            return match
    return None


def handoff_target(row):
    """Only validated catalogue IDs may become reader or plugin destinations."""
    identity = row['id']
    if row['kind'] == 'ebook' and re.fullmatch(r'[1-9][0-9]{0,9}', identity):
        return READER_BASE + '/book/' + identity
    if row['kind'] in ('audiobook', 'podcast') and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', identity):
        action = 'book' if row['kind'] == 'audiobook' else 'episodes'
        return 'plugin://' + AUDIO_ADDON + '/?' + urlencode({'action': action, 'item_id': identity})
    return None



def _bounded_json(path):
    """Read a small regular JSON record without following a symlink."""
    try:
        metadata = path.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or path.is_symlink() or
                not 0 < metadata.st_size <= MAX_READER_RECORD):
            return None
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def compiled_reader_target(row, reader=COMPILED_READER,
                           state=COMPILED_READER_STATE,
                           output=COMPILED_OUTPUT):
    """Return the pinned local reader command for one atomic ready ebook."""
    identity = row.get('id')
    if row.get('kind') != 'ebook' or not isinstance(identity, str) or not re.fullmatch(
            r'[1-9][0-9]{0,9}', identity):
        return None
    activation = _bounded_json(Path(state) / 'activation.json')
    expected_activation = {'schema', 'active', 'bundle', 'bundle_sha256', 'output'}
    if (not isinstance(activation, dict) or set(activation) != expected_activation or
            activation['schema'] != 1 or activation['active'] is not True or
            activation['bundle'] != str(Path(reader)) or
            activation['output'] != str(Path(output)) or
            not isinstance(activation['bundle_sha256'], str) or
            SHA256.fullmatch(activation['bundle_sha256']) is None):
        return None
    pointer = _bounded_json(Path(output) / 'ready' / (identity + '.json'))
    expected_pointer = {'schema', 'book_id', 'source_sha256',
                        'generation', 'manifest_sha256'}
    book_id = int(identity)
    if (not isinstance(pointer, dict) or set(pointer) != expected_pointer or
            pointer['schema'] != 1 or pointer['book_id'] != book_id or
            not isinstance(pointer['source_sha256'], str) or
            SHA256.fullmatch(pointer['source_sha256']) is None or
            not isinstance(pointer['manifest_sha256'], str) or
            SHA256.fullmatch(pointer['manifest_sha256']) is None or
            pointer['generation'] != ('generations/' + identity + '/' +
                                      pointer['source_sha256'])):
        return None
    entry = Path(reader) / 'default.py'
    try:
        metadata = entry.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or entry.is_symlink():
        return None
    return ('RunScript(' + str(entry) + ',' + activation['bundle_sha256'] + ',' +
            identity + ')')


def narrated_ebook_records(records, compiled_target=compiled_reader_target,
                           output=COMPILED_OUTPUT):
    """Keep only EPUB rows whose published reader target is currently usable.

    Audiobooks and podcasts remain untouched. The ready directory gives us a
    bounded candidate set; the existing pinned-reader check validates every
    ebook that is shown before it can be selected.
    """
    ready_dir = Path(output) / 'ready'
    try:
        metadata = ready_dir.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or ready_dir.is_symlink():
            ready_ids = set()
        else:
            ready_ids = {path.stem for path in ready_dir.iterdir()
                         if re.fullmatch(r'[1-9][0-9]{0,9}', path.stem)}
    except OSError:
        ready_ids = set()

    result = []
    for row in records:
        if row.get('kind') != 'ebook':
            result.append(row)
        elif row.get('id') in ready_ids and compiled_target(row) is not None:
            result.append(row)
    return result


def activate_row(row, xbmc, xbmcgui, compiled_target=compiled_reader_target):
    destination = handoff_target(row)
    if destination is None:
        xbmcgui.Dialog().ok('Aster Books', 'This title has no safe reader destination.')
    elif row['kind'] == 'ebook':
        compiled = compiled_target(row)
        if compiled is not None:
            xbmc.executebuiltin(compiled)
        elif sys.platform == 'darwin' and webbrowser.open(destination):
            xbmcgui.Dialog().notification('Aster Books', 'Opened the Calibre-Web reader on this Mac.')
        else:
            xbmcgui.Dialog().textviewer('Read on your phone or tablet',
                                        'Open this link and sign in to Calibre-Web:\n\n' + destination)
    elif not xbmc.getCondVisibility('System.HasAddon(' + AUDIO_ADDON + ')'):
        xbmcgui.Dialog().ok('Aster Books Audio needed',
                            'Install and configure the private Aster Books Audio bridge before listening.')
    else:
        xbmc.executebuiltin('ActivateWindow(Music,' + destination + ',return)')



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

def main(page, action='load', identity=None):
    import xbmc
    import xbmcgui
    import xbmcvfs

    if page not in PAGES:
        return
    window = xbmcgui.Window(PAGES[page])
    if action == 'search' and page != 'home':
        value = xbmcgui.Dialog().input('Search ' + page,
                                       defaultt=window.getProperty('AsterBooks.Search'))
        window.setProperty('AsterBooks.Search', value[:120])
    elif action == 'clear' and page != 'home':
        window.clearProperty('AsterBooks.Search')
    elif action == 'focus' and page != 'home':
        window.clearProperty('AsterBooks.Search')

    path = xbmcvfs.translatePath(
        'special://profile/addon_data/skin.asterhome/feeds/books.json')
    cover_root = xbmcvfs.translatePath(
        'special://profile/addon_data/skin.asterhome/feeds/covers')
    try:
        records = narrated_ebook_records(book_catalogue(read_feed(path)))
        available = True
    except (OSError, ValueError, KeyError, TypeError):
        records = []
        available = False

    if page == 'home' and action.startswith('hero-'):
        books_hero_action(xbmc, xbmcgui, action, records)
        return

    if action in ('open', 'activate'):
        row = selected_row(window, page, records, xbmc.getInfoLabel)
        if row:
            if action == 'open':
                xbmcgui.Dialog().textviewer(row['title'],
                                            row['synopsis'] or 'No synopsis available for this title.')
            else:
                activate_row(row, xbmc, xbmcgui)
        else:
            xbmcgui.Dialog().notification('Aster Books', 'Could not resolve the selected title.')
        return

    counts = {kind: sum(row['kind'] == kind for row in records)
              for kind in HOME_CONTROLS}
    if page == 'home':
        for kind, control_id in HOME_CONTROLS.items():
            listing = window.getControl(control_id)
            listing.reset()
            listing.addItems([make_item(xbmcgui, row, cover_root) for row in
                              page_records(records, {'ebook': 'ebooks',
                                                     'audiobook': 'audiobooks',
                                                     'podcast': 'podcasts'}[kind])[:12]])
        dated = sum(bool(row.get('added_at')) for row in records)
        status = (f'Read-only catalogue · {dated} source-dated titles'
                  if available and dated else
                  'Read-only catalogue · source dates not yet available'
                  if available else 'Books feed unavailable or stale')
        load_books_hero(window, records, cover_root)
    else:
        query = window.getProperty('AsterBooks.Search').strip()
        rows = page_records(records, page, query)
        listing = window.getControl(500)
        listing.reset()
        listing.addItems([make_item(xbmcgui, row, cover_root) for row in rows])
        total = counts[KINDS[page]]
        status = (f'{len(rows)} / {total} catalogue titles' if available else
                  'Books feed unavailable or stale')
        window.setProperty('AsterBooks.SearchLabel',
                           'Search: ' + query if query else
                           'Filter my shows' if page == 'podcasts' else
                           'Search ' + page)
        if action == 'focus' and identity is not None:
            match = next((index for index, row in enumerate(rows)
                          if row['id'] == identity and row['kind'] == KINDS[page]), None)
            if match is not None:
                listing.selectItem(match)
                xbmc.executebuiltin('Control.SetFocus(500)')
        elif action == 'load' and rows:
            xbmc.executebuiltin('Control.SetFocus(500,0,absolute)')

    for kind, count in counts.items():
        window.setProperty('AsterBooks.Count.' + kind, str(count))
    window.setProperty('AsterBooks.Status', status)
    window.setProperty('AsterBooks.Available', 'true' if available else 'false')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '',
         sys.argv[2] if len(sys.argv) > 2 else 'load',
         sys.argv[3] if len(sys.argv) > 3 else None)
