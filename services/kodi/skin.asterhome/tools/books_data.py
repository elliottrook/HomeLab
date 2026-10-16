"""Aster Books catalogue, synopsis and bounded reader handoffs.

The feed has sanitized descriptions but no file paths, media URLs or secrets.
Cover JPEGs come from a separate validated private cache. Validated source IDs
may hand off to Calibre-Web or the installed Audiobookshelf add-on; neither
route grants access on its own, and the add-on still requires sign-in.
"""

import sys
import hashlib
import re
import stat
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

from hub_feeds import book_catalogue, read_feed


PAGES = {'home': 11110, 'ebooks': 11118, 'audiobooks': 11119,
         'podcasts': 11120}
KINDS = {'ebooks': 'ebook', 'audiobooks': 'audiobook',
         'podcasts': 'podcast'}
ICONS = {'ebook': '21-books-app.png', 'audiobook': '12-audiobooks.png',
         'podcast': '22-podcasts-app.png'}
HOME_CONTROLS = {'ebook': 501, 'audiobook': 502, 'podcast': 503}
ABS_ADDON = 'plugin.audio.audiobookshelf'
READER_BASE = 'https://books.elliottrook.com'


def page_records(records, page, query=''):
    """Return real catalogue rows only; home rows preserve source order."""
    kind = KINDS.get(page)
    selected = [row for row in records if kind is None or row['kind'] == kind]
    if query:
        term = query.casefold()
        selected = [row for row in selected if term in row['title'].casefold()]
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
        if item is not None:
            kind, identity = item.getProperty('AsterBooks.Kind'), item.getProperty('AsterBooks.Id')
        elif info_label is not None:
            # Kodi's panel wrapper does not expose getSelectedItem on every build.
            kind = info_label(f'Container({control_id}).ListItem.Property(AsterBooks.Kind)')
            identity = info_label(f'Container({control_id}).ListItem.Property(AsterBooks.Id)')
        else:
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
        action = 'play' if row['kind'] == 'audiobook' else 'episodes'
        return 'plugin://' + ABS_ADDON + '/?' + urlencode({'action': action, 'item_id': identity})
    return None


def activate_row(row, xbmc, xbmcgui):
    destination = handoff_target(row)
    if destination is None:
        xbmcgui.Dialog().ok('Aster Books', 'This title has no safe reader destination.')
    elif row['kind'] == 'ebook':
        if sys.platform == 'darwin' and webbrowser.open(destination):
            xbmcgui.Dialog().notification('Aster Books', 'Opened the Calibre-Web reader on this Mac.')
        else:
            xbmcgui.Dialog().textviewer('Read on your phone or tablet',
                                        'Open this link and sign in to Calibre-Web:\n\n' + destination)
    elif not xbmc.getCondVisibility('System.HasAddon(' + ABS_ADDON + ')'):
        xbmcgui.Dialog().ok('Audiobookshelf add-on needed',
                            'Install Audiobookshelf from the official Kodi add-on repository, then sign in there.')
    elif row['kind'] == 'podcast':
        xbmc.executebuiltin('ActivateWindow(Music,' + destination + ',return)')
    else:
        xbmc.executebuiltin('PlayMedia(' + destination + ')')


def main(page, action='load'):
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

    path = xbmcvfs.translatePath(
        'special://profile/addon_data/skin.asterhome/feeds/books.json')
    cover_root = xbmcvfs.translatePath(
        'special://profile/addon_data/skin.asterhome/feeds/covers')
    try:
        records = book_catalogue(read_feed(path))
        available = True
    except (OSError, ValueError, KeyError, TypeError):
        records = []
        available = False

    if action in ('open', 'activate'):
        row = selected_row(window, page, records, xbmc.getInfoLabel)
        if row:
            if action == 'open':
                xbmcgui.Dialog().textviewer(row['title'],
                                            row['synopsis'] or 'No synopsis available for this title.')
            else:
                activate_row(row, xbmc, xbmcgui)
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
        status = ('Read-only catalogue snapshot · no per-title added dates'
                  if available else 'Books feed unavailable or stale')
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

    for kind, count in counts.items():
        window.setProperty('AsterBooks.Count.' + kind, str(count))
    window.setProperty('AsterBooks.Status', status)
    window.setProperty('AsterBooks.Available', 'true' if available else 'false')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '',
         sys.argv[2] if len(sys.argv) > 2 else 'load')
