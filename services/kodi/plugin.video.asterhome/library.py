"""Pure helpers for Aster's read-only combined video library views."""

GENRES = {
    'Comedy': ('comedy',),
    'Drama': ('drama',),
    'Action': ('action',),
    'Sci-Fi': ('sci-fi', 'science fiction'),
    'Documentary': ('documentary',),
    'Horror': ('horror',),
    'Family': ('family',),
}


def canonical_genre(value):
    """Return an allowed display genre or None for an untrusted value."""
    candidate = (value or '').strip().casefold()
    return next((name for name in GENRES if name.casefold() == candidate), None)


def matches_genre(item, genre):
    """Match Kodi's list of genre labels, including common Sci-Fi spelling."""
    tokens = GENRES[genre]
    values = item.get('genre', [])
    if not isinstance(values, list):
        return False
    return any(token in str(value).casefold() for value in values for token in tokens)


def combined_items(movies, shows, genre):
    """Merge matching movie and TV-show rows without changing source records."""
    result = []
    for kind, identifier, rows in (('movie', 'movieid', movies),
                                   ('tvshow', 'tvshowid', shows)):
        if not isinstance(rows, list):
            continue
        for source in rows:
            if not isinstance(source, dict) or identifier not in source:
                continue
            if matches_genre(source, genre):
                row = dict(source)
                row['kind'] = kind
                row['id'] = source[identifier]
                row['label'] = source.get('label') or source.get('title') or 'Untitled'
                result.append(row)
    return sorted(result, key=lambda row: (row['label'].casefold(), row['kind']))
