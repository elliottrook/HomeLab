"""Read-only Aster Books tiles from the existing sanitized local feed.

The current feed has no per-title date, cover, synopsis or playback path.
Never infer recency or create a working Play action from its catalogue IDs.
"""

import sys

from hub_feeds import book_catalogue, read_feed


PAGES = {'home': 11110, 'ebooks': 11118, 'audiobooks': 11119,
         'podcasts': 11120}
KINDS = {'ebooks': 'ebook', 'audiobooks': 'audiobook',
         'podcasts': 'podcast'}
ICONS = {'ebook': '21-books-app.png', 'audiobook': '12-audiobooks.png',
         'podcast': '22-podcasts-app.png'}
HOME_CONTROLS = {'ebook': 501, 'audiobook': 502, 'podcast': 503}


def page_records(records, page, query=''):
    """Return real catalogue rows only; home rows preserve source order."""
    kind = KINDS.get(page)
    selected = [row for row in records if kind is None or row['kind'] == kind]
    if query:
        term = query.casefold()
        selected = [row for row in selected if term in row['title'].casefold()]
    return selected[:200]


def make_item(xbmcgui, row):
    item = xbmcgui.ListItem(row['title'], row['detail'])
    item.setArt({'thumb': 'special://skin/media/' + ICONS[row['kind']]})
    item.setProperty('AsterBooks.Kind', row['kind'])
    item.setProperty('AsterBooks.Id', row['id'])
    item.setProperty('AsterBooks.Summary',
                     'Catalogue title · cover and synopsis not in the current feed')
    return item


def main(page, action='load'):
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
    elif action == 'open':
        xbmcgui.Dialog().notification('Aster Books',
                                      'Catalogue only · reading and listening are not connected')
        return

    path = xbmcvfs.translatePath(
        'special://profile/addon_data/skin.asterhome/feeds/books.json')
    try:
        records = book_catalogue(read_feed(path))
        available = True
    except (OSError, ValueError, KeyError, TypeError):
        records = []
        available = False

    counts = {kind: sum(row['kind'] == kind for row in records)
              for kind in HOME_CONTROLS}
    if page == 'home':
        for kind, control_id in HOME_CONTROLS.items():
            listing = window.getControl(control_id)
            listing.reset()
            listing.addItems([make_item(xbmcgui, row) for row in
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
        listing.addItems([make_item(xbmcgui, row) for row in rows])
        total = counts[KINDS[page]]
        status = (f'{len(rows)} / {total} catalogue titles' if available else
                  'Books feed unavailable or stale')
        window.setProperty('AsterBooks.SearchLabel',
                           'Search: ' + query if query else 'Search ' + page)

    for kind, count in counts.items():
        window.setProperty('AsterBooks.Count.' + kind, str(count))
    window.setProperty('AsterBooks.Status', status)
    window.setProperty('AsterBooks.Available', 'true' if available else 'false')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '',
         sys.argv[2] if len(sys.argv) > 2 else 'load')
