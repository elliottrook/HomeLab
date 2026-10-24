"""Read-only album ordering for future queue proposals; not part of the pilot.

No media paths, artist joins, player calls or persistence. Two complete matching
reads plus exact catalogue membership guard against stale/truncated selections;
these are optimistic checks, not a transaction with a future queue writer.
"""
from dataclasses import dataclass


class AlbumUnavailable(ValueError):
    """Safe UI error code; no raw transport messages or library paths."""


@dataclass(frozen=True)
class AlbumTrack:
    song_id: int
    disc: int
    track: int
    title: str
    duration: int


@dataclass(frozen=True)
class AlbumSelection:
    album_id: int
    tracks: tuple
    disc_numbers_available: bool

    @property
    def song_ids(self):
        return tuple(row.song_id for row in self.tracks)


def order_album(album_id, rows, expected_song_ids):
    if type(album_id) is not int or album_id < 1:
        raise AlbumUnavailable('invalid-album-identity')
    if (not isinstance(expected_song_ids, (list, tuple)) or not expected_song_ids
            or len(expected_song_ids) > 10000
            or any(type(i) is not int or i < 1 for i in expected_song_ids)
            or len(set(expected_song_ids)) != len(expected_song_ids)):
        raise AlbumUnavailable('complete-album-membership-required')
    if not isinstance(rows, list) or len(rows) != len(expected_song_ids):
        raise AlbumUnavailable('album-membership-changed')
    tracks, seen, positions = [], set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise AlbumUnavailable('invalid-album-track')
        song, parent = row.get('songid'), row.get('albumid')
        disc, track = row.get('disc'), row.get('track')
        title, duration = row.get('label'), row.get('duration')
        if type(track) is int and track == 0:
            raise AlbumUnavailable('album-track-number-unavailable')
        if (type(song) is not int or song < 1 or song in seen
                or type(parent) is not int or parent != album_id
                or type(disc) is not int or not 0 <= disc <= 65535
                or type(track) is not int or not 1 <= track <= 65535
                or not isinstance(title, str)
                or type(duration) is not int or duration < 0):
            raise AlbumUnavailable('invalid-album-track')
        if (disc, track) in positions:
            raise AlbumUnavailable('ambiguous-album-order')
        seen.add(song); positions.add((disc, track))
        tracks.append(AlbumTrack(song, disc, track, title, duration))
    if seen != set(expected_song_ids):
        raise AlbumUnavailable('album-membership-changed')
    # All-zero disc tags retain truthful unknown disc numbers and order by
    # unique track tags. Mixed known/unknown discs cannot be placed reliably.
    discs = {row.disc for row in tracks}
    if 0 in discs and len(discs) > 1:
        raise AlbumUnavailable('ambiguous-album-order')
    tracks.sort(key=lambda row: (row.disc, row.track))
    return AlbumSelection(album_id, tuple(tracks), 0 not in discs)


def read_album(rpc, album_id, expected_song_ids, *, page_size=200):
    """Use only GetSongs with an album ID; never silently stop at 500 tracks."""
    # Validate caller options before any RPC.
    if type(album_id) is not int or album_id < 1:
        raise AlbumUnavailable('invalid-album-identity')
    if type(page_size) is not int or not 1 <= page_size <= 1000:
        raise AlbumUnavailable('invalid-album-read-options')
    if (not isinstance(expected_song_ids, (list, tuple)) or not expected_song_ids
            or len(expected_song_ids) > 10000
            or any(type(i) is not int or i < 1 for i in expected_song_ids)
            or len(set(expected_song_ids)) != len(expected_song_ids)):
        raise AlbumUnavailable('complete-album-membership-required')
    expected_song_ids = tuple(expected_song_ids)

    def complete_read():
        rows = []
        while len(rows) < len(expected_song_ids):
            start = len(rows)
            try:
                result = rpc('AudioLibrary.GetSongs', {
                    'filter': {'albumid': album_id},
                    'properties': ['albumid', 'disc', 'track', 'duration'],
                    'sort': {'method': 'track', 'order': 'ascending'},
                    'limits': {'start': start, 'end': start + page_size}})
            except Exception:
                raise AlbumUnavailable('album-read-failed') from None
            if not isinstance(result, dict):
                raise AlbumUnavailable('incomplete-album-page')
            page, limits = result.get('songs'), result.get('limits')
            if (not isinstance(page, list) or not isinstance(limits, dict)
                    or any(type(limits.get(k)) is not int for k in ('start','end','total'))
                    or limits['start'] != start
                    or limits['total'] != len(expected_song_ids)
                    or limits['end'] != start + len(page)
                    or not 0 < len(page) <= page_size
                    or limits['end'] > limits['total']):
                raise AlbumUnavailable('incomplete-album-page')
            # Drop unexpected fields immediately, including paths/credentials.
            if any(not isinstance(row, dict) for row in page):
                raise AlbumUnavailable('invalid-album-track')
            rows.extend({k: row[k] for k in ('songid','albumid','disc','track','label','duration')
                         if k in row} for row in page)
        return order_album(album_id, rows, expected_song_ids)

    first, second = complete_read(), complete_read()
    if first != second:
        raise AlbumUnavailable('album-changed-during-verification')
    return second
