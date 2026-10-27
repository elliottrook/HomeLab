"""Build truthful owned Music landing records from Kodi album metadata."""
import math

from music_policy import is_holiday


PROPERTIES = [
    'title', 'description', 'artist', 'genre', 'rating', 'userrating', 'year',
    'fanart', 'thumbnail', 'playcount', 'displayartist', 'dateadded', 'art',
    'lastplayed',
]
MAX_ALBUMS = 20000


def require(value, code):
    if not value:
        raise ValueError(code)


def _number(value, maximum):
    if type(value) not in (int, float) or type(value) is bool:
        return 0.0
    value = float(value)
    return value if math.isfinite(value) and 0 <= value <= maximum else 0.0


def _genres(value):
    return tuple(str(item).strip() for item in value
                 if str(item).strip()) if isinstance(value, list) else ()


def fetch_albums(rpc, page_size=1000, maximum=MAX_ALBUMS):
    """Read a complete bounded Kodi album catalogue or fail closed."""
    require(callable(rpc) and type(page_size) is int and 1 <= page_size <= 2000
            and type(maximum) is int and page_size <= maximum <= MAX_ALBUMS,
            'music-landing-fetch')
    rows = []
    total = None
    for start in range(0, maximum, page_size):
        result = rpc('AudioLibrary.GetAlbums', {
            'properties': PROPERTIES,
            'limits': {'start': start, 'end': min(start + page_size, maximum)},
            'sort': {'method': 'album', 'order': 'ascending'},
        })
        page = result.get('albums', []) if isinstance(result, dict) else None
        limits = result.get('limits', {}) if isinstance(result, dict) else {}
        page_total = limits.get('total')
        require(isinstance(page, list) and type(page_total) is int
                and 0 <= page_total <= maximum, 'music-landing-page')
        if total is None:
            total = page_total
        require(page_total == total and len(rows) + len(page) <= total,
                'music-landing-page')
        rows.extend(page)
        if len(rows) == total:
            return rows
        require(page, 'music-landing-pagination')
    raise ValueError('music-landing-cap')


def landing_rows(albums, recent_limit=12):
    """Project local albums with source dates and evidence-based suggestions."""
    require(isinstance(albums, list) and len(albums) <= MAX_ALBUMS
            and type(recent_limit) is int and 1 <= recent_limit <= 50,
            'music-landing-input')
    normalized = []
    seen = set()
    affinity = {}
    for source in albums:
        require(isinstance(source, dict) and type(source.get('albumid')) is int
                and source['albumid'] > 0 and source['albumid'] not in seen,
                'music-landing-album')
        seen.add(source['albumid'])
        title = source.get('label') or source.get('title')
        require(isinstance(title, str) and title.strip() and len(title) <= 200,
                'music-landing-album')
        genres = _genres(source.get('genre'))
        plays = source.get('playcount', 0)
        require(type(plays) is int and plays >= 0, 'music-landing-playcount')
        weight = min(plays, 10)
        if source.get('lastplayed') and not weight:
            weight = 1
        for genre in genres:
            token = genre.casefold()
            affinity[token] = affinity.get(token, 0) + weight
        normalized.append((source, title.strip(), genres))

    newest = sorted((source for source, _title, _genres_value in normalized
                     if isinstance(source.get('dateadded'), str)
                     and source['dateadded'].strip()),
                    key=lambda row: (row['dateadded'],
                                     (row.get('label') or row.get('title')).casefold()),
                    reverse=True)[:recent_limit]
    recent_ids = {row['albumid'] for row in newest}

    output = []
    for source, title, genres in normalized:
        art = source.get('art') if isinstance(source.get('art'), dict) else {}
        artwork = source.get('thumbnail') or art.get('thumb') or ''
        backdrop = source.get('fanart') or art.get('fanart') or artwork
        artist = source.get('displayartist')
        if not isinstance(artist, str) or not artist.strip():
            value = source.get('artist')
            artist = ', '.join(str(item) for item in value if item) if isinstance(value, list) else ''
        row = {
            'identity': 'kodi:album-' + str(source['albumid']),
            'media_type': 'album',
            'title': title,
            'detail': (artist.strip() or 'Unknown artist')
                      + (f" · {source['year']}" if type(source.get('year')) is int
                         and source['year'] > 0 else ''),
            'synopsis': str(source.get('description') or '')[:3000],
            'artwork': str(artwork),
            'backdrop': str(backdrop),
            'added_at': source.get('dateadded') or None,
            'recommendation_score': None,
            'recommendation_reason': '',
        }
        if source['albumid'] not in recent_ids and backdrop and not is_holiday(source):
            ranked = sorted(((affinity.get(genre.casefold(), 0), genre)
                             for genre in genres), reverse=True)
            best_score, best_genre = ranked[0] if ranked else (0, '')
            userrating = _number(source.get('userrating'), 10)
            rating = _number(source.get('rating'), 10)
            if best_score > 0:
                row['recommendation_score'] = min(
                    100.0, best_score * 8 + userrating * 2 + rating)
                row['recommendation_reason'] = (
                    'Because you listen to ' + best_genre)
            elif userrating >= 7:
                row['recommendation_score'] = min(100.0, userrating * 8 + rating * 2)
                row['recommendation_reason'] = 'Highly rated in your library'
        output.append(row)
    return output
