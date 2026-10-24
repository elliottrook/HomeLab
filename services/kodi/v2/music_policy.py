"""Offline v2 music-category/shuffle policy; no Kodi, network or state writes.

Prototype against the HP's aggregate inventory. This is deliberately outside
the shipped v1 add-on trees so starting v2 cannot change a v1.1 release hash.
"""
import random
import re
import unicodedata


CATEGORIES = (
    'Pop, Electronic & Hip-Hop', 'Jazz, Blues, R&B & Soul',
    'Rock & Alternative', 'Country & Folk', 'Christmas', 'Classical',
)
OTHER = 'Other / unclassified'
# Exact legacy aliases observed in the current index. These are presentation
# proposals, not edits to source tags. Never split canonical labels on commas.
ALIASES = {
    'pop': CATEGORIES[0], 'dance-pop': CATEGORIES[0],
    'alternative pop': CATEGORIES[0], 'synth-pop': CATEGORIES[0],
    'funk': CATEGORIES[1], 'new jack swing': CATEGORIES[1],
    'rock': CATEGORIES[2], 'pop rock': CATEGORIES[2],
    'alternative rock': CATEGORIES[2], 'funk rock': CATEGORIES[2],
    'soft rock': CATEGORIES[2],
    'country': CATEGORIES[3], 'country pop': CATEGORIES[3],
    'country rock': CATEGORIES[3], 'americana': CATEGORIES[3],
}
HOLIDAY = re.compile(r'(?<!\w)(?:christmas|xmas|x-mas|holiday|holidays|noel)(?!\w)')


def normalized(value):
    if not isinstance(value, str):
        return ''
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', value)
                           if not unicodedata.combining(c)).casefold().split())


def labels(row):
    values = row.get('genre', []) if isinstance(row, dict) else []
    return [value.strip() for value in values if isinstance(value, str) and value.strip()] if isinstance(values, list) else []


def is_holiday(row):
    """Only classification tags count; a festive word in a title is not a tag."""
    return any(HOLIDAY.search(normalized(label)) for label in labels(row))


def categories_for(song, album=None):
    """Prefer track classification; inherit album genre only when unmatched."""
    canonical = {normalized(label): label for label in CATEGORIES}
    for row in (song, album):
        result = []
        for label in labels(row):
            key = normalized(label)
            category = canonical.get(key) or ALIASES.get(key)
            if category and category not in result:
                result.append(category)
        if result:
            return tuple(result)
    return (OTHER,)


def shuffle_candidates(songs, albums, *, expected_total):
    """Require a complete snapshot; exclude direct and inherited holiday tags.

    Return IDs only, without altering source lists, playlists or playback.
    Duplicate/missing IDs fail instead of silently weighting or dropping songs.
    """
    if (not isinstance(songs, list) or type(expected_total) is not int
            or expected_total < 0 or len(songs) != expected_total):
        raise ValueError('Complete song inventory required')
    if not isinstance(albums, list):
        raise ValueError('Album inventory required')
    album_map = {}
    for row in albums:
        if not isinstance(row, dict) or type(row.get('albumid')) is not int:
            raise ValueError('Invalid album identity')
        if row['albumid'] in album_map:
            raise ValueError('Duplicate album identity')
        album_map[row['albumid']] = row
    seen, eligible, excluded, unclassified = set(), [], 0, 0
    for row in songs:
        if not isinstance(row, dict) or type(row.get('songid')) is not int:
            raise ValueError('Invalid song identity')
        identity = row['songid']
        if identity < 1 or identity in seen:
            raise ValueError('Duplicate or invalid song identity')
        seen.add(identity)
        album = album_map.get(row.get('albumid'))
        if row.get('albumid') and album is None:
            raise ValueError('Incomplete album inventory')
        if is_holiday(row) or is_holiday(album):
            excluded += 1
            continue
        eligible.append(identity)
        if categories_for(row, album) == (OTHER,):
            unclassified += 1
    return {'eligible_ids': eligible, 'excluded': excluded,
            'unclassified_eligible': unclassified, 'total': len(songs)}


def shuffled_ids(candidates, rng=None):
    """Explicit caller action only; never open or clear a Kodi queue here."""
    result = list(candidates['eligible_ids'])
    (rng or random.SystemRandom()).shuffle(result)
    return result
