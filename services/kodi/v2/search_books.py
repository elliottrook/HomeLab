"""Read-only, stable Books search over the already sanitized local feed."""

from pathlib import Path
import re

from global_search import Group, Hit, normalize_query


FEED = Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/books.json')
KINDS = (('ebook', 'Ebooks'), ('audiobook', 'Audiobooks'), ('podcast', 'Podcasts'))
AUDIO_ID = re.compile(r'[A-Za-z0-9_-]{1,128}\Z')
EBOOK_ID = re.compile(r'[1-9][0-9]{0,9}\Z')


def permitted_id(kind, identity):
    return (isinstance(identity, str) and
            bool((EBOOK_ID if kind == 'ebook' else AUDIO_ID).fullmatch(identity)))


def search_books(catalogue, query):
    """Double-read local catalogue; show unavailable rather than mixed snapshots."""
    query = normalize_query(query)
    if not query:
        return tuple(Group(kind, label, 'idle') for kind, label in KINDS)
    try:
        first = catalogue()
        second = catalogue()
        if first != second or not isinstance(first, list) or len(first) > 1000:
            raise ValueError('books-feed-changed')
        groups = []
        words = tuple(word.casefold() for word in query.split())
        for kind, label in KINDS:
            hits = []
            seen = set()
            for row in first:
                if not isinstance(row, dict) or row.get('kind') != kind:
                    continue
                identity, title, detail = row.get('id'), row.get('title'), row.get('detail')
                if (not permitted_id(kind, identity) or identity in seen
                        or not isinstance(title, str) or not 0 < len(title) <= 160
                        or not isinstance(detail, str) or len(detail) > 240):
                    raise ValueError('invalid-books-result')
                seen.add(identity)
                if all(word in title.casefold() for word in words):
                    hits.append(Hit(kind, identity, title, detail))
            groups.append(Group(kind, label, 'ready' if hits else 'empty',
                                tuple(hits[:500]), len(hits), len(hits) > 500))
        return tuple(groups)
    except (OSError, ValueError, KeyError, TypeError):
        return tuple(Group(kind, label, 'unavailable', reason='books-feed-unavailable')
                     for kind, label in KINDS)


def local_groups(query, path=FEED):
    from hub_feeds import book_catalogue, read_feed
    return search_books(lambda: book_catalogue(read_feed(path)), query)
