"""Read-only v2 Music adapter. Inject Kodi RPC; no player or queue APIs.

Kept outside the v1 add-on roots. No media paths, credentials or persistence.
Two matching complete reads provide an optimistic consistency check, not a
database transaction. Callers must not publish a partially constructed view.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json

from music_policy import CATEGORIES, OTHER, categories_for, shuffle_candidates


class CatalogueUnavailable(ValueError):
    """Safe user-facing failure code; never include a raw RPC error or URL."""


TABLES = (
    ('AudioLibrary.GetAlbums', 'albums', 'albumid', ['genre'], 10000),
    ('AudioLibrary.GetArtists', 'artists', 'artistid', ['genre'], 10000),
    ('AudioLibrary.GetSongs', 'songs', 'songid', ['genre', 'albumid', 'artistid'], 100000),
)


def call_read(rpc, method, params):
    try:
        return rpc(method, params)
    except Exception:
        raise CatalogueUnavailable('library-read-failed') from None


def recover_artist_omissions(rpc, params, page, limits, budget):
    """Keep songs omitted by Kodi's artist join, without inventing credits.

    A complete basic page is mandatory; this is not permission to accept a
    short primary inventory. Existing enriched rows must agree with that page.
    Unknown credits remain explicitly flagged and songs stay in Albums/Songs.
    """
    base_params = deepcopy(params)
    base_params['properties'].remove('artistid')
    basic = call_read(rpc, 'AudioLibrary.GetSongs', base_params)
    span = limits['end'] - limits['start']
    if (not isinstance(basic, dict) or basic.get('limits') != limits
            or not isinstance(basic.get('songs'), list)
            or len(basic['songs']) != span or span-len(page) > budget):
        raise CatalogueUnavailable('incomplete-library-page')
    enriched = {}
    for row in page:
        if (not isinstance(row, dict) or type(row.get('songid')) is not int
                or row['songid'] in enriched or 'artistid' not in row):
            raise CatalogueUnavailable('invalid-or-duplicate-identity')
        enriched[row['songid']] = row
    recovered = []
    for basic_row in basic['songs']:
        if not isinstance(basic_row, dict) or type(basic_row.get('songid')) is not int:
            raise CatalogueUnavailable('invalid-or-duplicate-identity')
        identity = basic_row['songid']
        rich = enriched.pop(identity, None)
        if rich is not None:
            if any(rich.get(k) != basic_row.get(k) for k in ('genre','albumid')):
                raise CatalogueUnavailable('library-changed-during-read')
            recovered.append(rich)
        else:
            recovered.append({**basic_row, 'artistid': [], 'artist_credit_available': False})
    if enriched:
        raise CatalogueUnavailable('library-changed-during-read')
    return recovered, span-len(page)


def read_pages(rpc, table, *, page_size=1000):
    if table not in TABLES or type(page_size) is not int or not 1 <= page_size <= 2000:
        raise CatalogueUnavailable('invalid-read-options')
    method, key, identity, properties, cap = table
    rows, seen, expected, artist_omissions = [], set(), None, 0
    while True:
        start = len(rows)
        params = {'properties': list(properties),
                  'sort': {'method': 'title', 'order': 'ascending'},
                  'limits': {'start': start, 'end': start + page_size}}
        if key == 'artists':
            params['albumartistsonly'] = False  # Include credited guest artists.
        result = call_read(rpc, method, params)
        if not isinstance(result, dict):
            raise CatalogueUnavailable('invalid-library-response')
        limits = result.get('limits')
        empty = limits == {'start': 0, 'end': 0, 'total': 0}
        page = result.get(key, [] if empty else None)
        if not isinstance(page, list) or not isinstance(limits, dict):
            raise CatalogueUnavailable('missing-page-or-limits')
        total, end = limits.get('total'), limits.get('end')
        if (key == 'songs' and type(total) is int and 0 <= total <= cap
                and type(end) is int and limits.get('start') == start
                and start <= end <= total and 0 < end-start <= page_size
                and len(page) < end-start):
            page, recovered = recover_artist_omissions(rpc, params, page, limits,
                                                      128-artist_omissions)
            artist_omissions += recovered
        if (type(total) is not int or type(end) is not int
                or type(limits.get('start')) is not int
                or total < 0 or total > cap or limits['start'] != start
                or end != start + len(page) or end > total
                or len(page) > page_size or (end < total and not page)):
            raise CatalogueUnavailable('incomplete-library-page')
        if expected is not None and total != expected:
            raise CatalogueUnavailable('library-changed-during-read')
        expected = total
        for row in page:
            if (not isinstance(row, dict) or type(row.get(identity)) is not int
                    or row[identity] < 1 or row[identity] in seen):
                raise CatalogueUnavailable('invalid-or-duplicate-identity')
            if not isinstance(row.get('genre', []), list) or any(
                    not isinstance(label, str) for label in row.get('genre', [])):
                raise CatalogueUnavailable('invalid-genre-metadata')
            seen.add(row[identity])
        allowed = {identity, 'label', *properties}
        if key == 'songs':
            allowed.add('artist_credit_available')
        rows.extend({key: deepcopy(value) for key, value in row.items() if key in allowed}
                    for row in page)
        if end == total:
            return rows


def fingerprint(tables):
    canonical = [[sorted(rows, key=lambda row: row[table[2]])]
                 for table, rows in zip(TABLES, tables)]
    return hashlib.sha256(json.dumps(canonical, sort_keys=True,
                                    ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class Catalogue:
    """Owned in-memory rows. View results are copies, not mutable references."""
    albums: dict
    artists: dict
    songs: dict
    membership: dict
    shuffle_summary: dict

    def credited(self,identity):
        return any(not (i==1 and self.artists.get(i,{}).get('label')=='[Missing Tag]')
                   for i in self.songs[identity].get('artistid',[]))

    def categories(self):
        return [{'label': label,
                 **{kind + '_count': len(self.membership[label][kind])
                    for kind in ('song', 'album', 'artist')},
                 'uncredited_song_count': sum(not self.credited(i)
                                             for i in self.membership[label]['song'])}
                for label in (*CATEGORIES, OTHER)]

    def browse(self, category, kind, *, query='', offset=0, limit=50, artist_id=None):
        if (category not in self.membership or kind not in ('song', 'album', 'artist')
                or not isinstance(query, str) or type(offset) is not int or offset < 0
                or type(limit) is not int or not 1 <= limit <= 200
                or (artist_id is not None and (type(artist_id) is not int or artist_id not in self.artists or kind=='artist'))):
            raise CatalogueUnavailable('invalid-browse-options')
        source = {'song': self.songs, 'album': self.albums, 'artist': self.artists}[kind]
        query = query.strip().casefold()
        members=self.membership[category][kind]
        if artist_id is not None:
            songs={i for i in self.membership[category]['song'] if artist_id in self.songs[i].get('artistid',[])}
            members=members & (songs if kind=='song' else {self.songs[i].get('albumid') for i in songs})
        rows = [source[identity] for identity in members
                if query in str(source[identity].get('label') or '').casefold()]
        rows.sort(key=lambda row: (str(row.get('label') or '').casefold(), row[kind + 'id']))
        return {'rows': deepcopy(rows[offset:offset+limit]), 'total': len(rows),
                'offset': offset, 'has_more': offset+limit < len(rows),
                'uncredited_song_count': sum(not self.credited(i)
                                            for i in self.membership[category]['song'])}


def build_catalogue(albums, artists, songs):
    album_map = {row['albumid']: deepcopy(row) for row in albums}
    artist_map = {row['artistid']: deepcopy(row) for row in artists}
    song_map = {row['songid']: deepcopy(row) for row in songs}
    try:
        summary = shuffle_candidates(songs, albums, expected_total=len(songs))
    except ValueError:
        raise CatalogueUnavailable('incomplete-classification-metadata') from None
    memberships = {label: {'song': set(), 'album': set(), 'artist': set()}
                   for label in (*CATEGORIES, OTHER)}
    for song in songs:
        album_id, artist_ids = song.get('albumid'), song.get('artistid', [])
        if (album_id is not None and (type(album_id) is not int or album_id < 0)
                or not isinstance(artist_ids, list)
                or any(type(i) is not int or i < 1 or i not in artist_map for i in artist_ids)):
            raise CatalogueUnavailable('incomplete-artist-or-album-links')
        for label in categories_for(song, album_map.get(album_id)):
            group = memberships[label]
            group['song'].add(song['songid'])
            if album_id:
                group['album'].add(album_id)
            group['artist'].update(i for i in artist_ids
                                  if not (i==1 and artist_map[i].get('label')=='[Missing Tag]'))
    summary['artist_unavailable_songs'] = sum(not any(
        not (i==1 and artist_map[i].get('label')=='[Missing Tag]')
        for i in row.get('artistid',[])) for row in songs)
    return Catalogue(album_map, artist_map, song_map, memberships, summary)


def read_catalogue(rpc, *, page_size=1000):
    """Only return after two complete matching reads and relationship checks."""
    first = [read_pages(rpc, table, page_size=page_size) for table in TABLES]
    second = [read_pages(rpc, table, page_size=page_size) for table in TABLES]
    if fingerprint(first) != fingerprint(second):
        raise CatalogueUnavailable('library-changed-during-verification')
    return build_catalogue(*second)
