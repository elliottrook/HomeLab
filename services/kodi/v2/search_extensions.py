"""Read-only search extension preparation; no installed navigation changes.

Artist relationships use Kodi IDs, not display-name matching. Movie info items
carry only identity and display metadata; Kodi remains the resolver authority.
"""
from copy import deepcopy
from global_search import Hit, SOURCES, SearchUnavailable, _hit


def checked_id(value):
    if type(value) is not int or not 0 < value <= 2147483647:
        raise SearchUnavailable('invalid-extension-identity')
    return value


def movie_info_item(gui, hit):
    if not isinstance(hit, Hit) or hit.kind != 'movie':
        raise SearchUnavailable('movie-info-only')
    checked_id(hit.identity)
    item = gui.ListItem(label=hit.title, offscreen=True)
    tag = item.getVideoInfoTag()
    tag.setDbId(hit.identity)
    tag.setMediaType('movie')
    tag.setTitle(hit.title)
    return item


def artist_albums(rpc, identity, *, page_size=100, cap=500, cancelled=lambda: False):
    """Double-read exact artist-ID album membership, with explicit truncation."""
    checked_id(identity)
    if (type(page_size) is not int or not 1 <= page_size <= 200
            or type(cap) is not int or not page_size <= cap <= 2000):
        raise SearchUnavailable('invalid-artist-album-options')
    source = next(s for s in SOURCES if s.kind == 'album')

    def snapshot():
        hits, identities, total = [], set(), None
        while total is None or len(hits) < min(total, cap):
            if cancelled():
                raise SearchUnavailable('cancelled')
            start = len(hits)
            params = dict(properties=list(source.properties), filter=dict(artistid=identity),
                          sort=dict(method='label', order='ascending', ignorearticle=True),
                          limits=dict(start=start, end=min(start+page_size, cap)))
            try:
                response = deepcopy(rpc('AudioLibrary.GetAlbums', params))
            except Exception:
                raise SearchUnavailable('artist-albums-unavailable') from None
            if not isinstance(response, dict):
                raise SearchUnavailable('invalid-artist-album-page')
            limits, rows = response.get('limits'), response.get('albums', [])
            if not isinstance(limits, dict) or not isinstance(rows, list):
                raise SearchUnavailable('invalid-artist-album-page')
            begin, end, count = (limits.get(k) for k in ('start', 'end', 'total'))
            if (any(type(v) is not int for v in (begin, end, count))
                    or not 0 <= count <= 10000000 or begin != start
                    or end != start+len(rows) or not start <= end <= min(count, start+page_size, cap)
                    or (not rows and start < min(count, cap))
                    or (total is not None and total != count)):
                raise SearchUnavailable('changing-artist-album-page')
            total = count
            for row in rows:
                hit = _hit(source, row)
                if hit.identity in identities:
                    raise SearchUnavailable('duplicate-artist-album')
                identities.add(hit.identity)
                hits.append(hit)
        return total, tuple(hits)

    first = snapshot()
    if first != snapshot():
        raise SearchUnavailable('artist-albums-changed')
    total, hits = first
    return dict(hits=hits, total=total, truncated=total > len(hits))
