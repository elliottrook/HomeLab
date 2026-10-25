"""Bounded, read-only search of Kodi's existing index; no playback or secrets.

Each group is independently consistent across two reads. This is not a cross-
database transaction or proof that a server/media file is currently reachable.
Only projected display metadata and positive local IDs leave this adapter.
"""
from copy import deepcopy
from dataclasses import dataclass
import unicodedata


class SearchUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    kind: str
    label: str
    method: str
    rows: str
    identity: str
    field: str
    properties: tuple


SOURCES = (
    Source('tvshow', 'TV shows', 'VideoLibrary.GetTVShows', 'tvshows', 'tvshowid', 'title', ('title', 'year')),
    Source('movie', 'Movies', 'VideoLibrary.GetMovies', 'movies', 'movieid', 'title', ('title', 'year')),
    Source('album', 'Albums', 'AudioLibrary.GetAlbums', 'albums', 'albumid', 'album', ('title', 'artist', 'year')),
    Source('artist', 'Artists', 'AudioLibrary.GetArtists', 'artists', 'artistid', 'artist', ()),
    Source('song', 'Songs', 'AudioLibrary.GetSongs', 'songs', 'songid', 'title', ('title', 'artist', 'album')),
)
READS = frozenset(source.method for source in SOURCES)


def normalize_query(value):
    if not isinstance(value, str) or len(value) > 256:
        raise SearchUnavailable('invalid-query')
    value = unicodedata.normalize('NFC', value)
    if any(unicodedata.category(c).startswith('C') for c in value):
        raise SearchUnavailable('invalid-query')
    value = ' '.join(value.split())
    if len(value) > 100 or len(value.split()) > 8:
        raise SearchUnavailable('query-too-long')
    return value


@dataclass(frozen=True)
class Hit:
    kind: str
    identity: int
    title: str
    detail: str


@dataclass(frozen=True)
class Group:
    kind: str
    label: str
    state: str
    hits: tuple = ()
    total: int = 0
    truncated: bool = False
    reason: str = ''


def _hit(source, row):
    if not isinstance(row, dict):
        raise SearchUnavailable('invalid-row')
    identity = row.get(source.identity)
    title = row.get('title') or row.get('label')
    if (type(identity) is not int or not 0 < identity <= 2147483647
            or not isinstance(title, str) or not title.strip() or len(title) > 4096):
        raise SearchUnavailable('invalid-result-identity')
    details = []
    # Kodi artists carry a scalar `artist` name; album/song credits are lists.
    artists = row.get('artist', []) if source.kind in ('album', 'song') else []
    if not isinstance(artists, list) or any(not isinstance(a, str) or len(a) > 4096 for a in artists):
        raise SearchUnavailable('invalid-result-metadata')
    if source.kind in ('album', 'song'):
        details.extend(artists)
    if source.kind == 'song':
        album = row.get('album', '')
        if not isinstance(album, str) or len(album) > 4096:
            raise SearchUnavailable('invalid-result-metadata')
        if album:
            details.append(album)
    year = row.get('year')
    if type(year) is int and 0 < year < 10000:
        details.append(str(year))
    return Hit(source.kind, identity, title.strip(), ' · '.join(details)[:4096])


def _snapshot(rpc, source, query, page_size, cap, cancelled):
    rows, identities, total = [], set(), None
    while total is None or len(rows) < min(total, cap):
        if cancelled():
            raise SearchUnavailable('cancelled')
        start = len(rows)
        filters = [dict(field=source.field, operator='contains', value=token)
                   for token in query.split()]
        params = dict(properties=list(source.properties),
                      filter=filters[0] if len(filters) == 1 else {'and': filters},
                      sort=dict(method='label', order='ascending', ignorearticle=True),
                      limits=dict(start=start, end=min(start+page_size, cap)))
        if source.kind == 'artist':
            params['albumartistsonly'] = False
        try:
            result = deepcopy(rpc(source.method, params))
        except Exception:
            raise SearchUnavailable('source-unavailable') from None
        if not isinstance(result, dict):
            raise SearchUnavailable('invalid-response')
        limits = result.get('limits')
        batch = result.get(source.rows, [])
        if not isinstance(limits, dict) or not isinstance(batch, list):
            raise SearchUnavailable('invalid-page')
        n, end, begin = (limits.get(k) for k in ('total', 'end', 'start'))
        if (any(type(v) is not int for v in (n, end, begin)) or not 0 <= n <= 10000000
                or begin != start or end != start+len(batch)
                or not start <= end <= min(n, start+page_size, cap)
                or (not batch and start < min(n, cap))
                or (total is not None and n != total)):
            raise SearchUnavailable('incomplete-or-changing-source')
        total = n
        for row in batch:
            hit = _hit(source, row)
            if hit.identity in identities:
                raise SearchUnavailable('duplicate-result-identity')
            identities.add(hit.identity)
            rows.append(hit)
    return total, tuple(rows)


def search_group(rpc, source, query, *, page_size=100, cap=500, cancelled=lambda: False):
    query = normalize_query(query)
    if (source not in SOURCES or type(page_size) is not int or not 1 <= page_size <= 200
            or type(cap) is not int or not page_size <= cap <= 2000):
        raise SearchUnavailable('invalid-search-options')
    if not query:
        return Group(source.kind, source.label, 'idle')
    try:
        first = _snapshot(rpc, source, query, page_size, cap, cancelled)
        second = _snapshot(rpc, source, query, page_size, cap, cancelled)
        if first != second:
            raise SearchUnavailable('source-changed-during-search')
        total, hits = second
        return Group(source.kind, source.label, 'ready' if hits else 'empty',
                     hits, total, total > len(hits))
    except SearchUnavailable as error:
        if str(error) == 'cancelled':
            raise
        return Group(source.kind, source.label, 'unavailable', reason=str(error))


def search(rpc, query, **options):
    query = normalize_query(query)
    return tuple(search_group(rpc, source, query, **options) for source in SOURCES)
