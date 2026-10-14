"""Bounded, read-only candidate adapters for non-video media.

These adapters return sanitized candidates only. They never call an acquisition
authority and deliberately require explicit seed queries, so a provider outage
or an empty configuration produces no guessed recommendations.
"""

from __future__ import annotations

import urllib.parse
import re
import time
from typing import Any, Callable, Mapping


Request = Callable[..., tuple[Any, Mapping[str, str]]]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _first_year(value: Any) -> str:
    text = _text(value)
    return text[:4] if len(text) >= 4 and text[:4].isdigit() else ""


def _score(value: Any, default: float = 0.60) -> float:
    try:
        return max(0.0, min(1.0, float(value) / 10.0))
    except (TypeError, ValueError):
        return default


_STOPWORDS = {"a", "an", "and", "of", "the", "to", "in", "on", "for"}


def _meaningful_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.casefold())
            if token not in _STOPWORDS and len(token) > 1}


def _first_sentence(value: Any) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    return _text(value)


def _music_artwork(mbid: str, request: Request) -> str:
    try:
        payload, _ = request(
            f"https://coverartarchive.org/release-group/{urllib.parse.quote(mbid, safe='')}",
            headers={
                "Accept": "application/json",
                "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)",
            },
        )
    except (OSError, TimeoutError, ValueError):
        return ""
    images = payload.get("images", []) if isinstance(payload, Mapping) else []
    if not isinstance(images, list):
        return ""
    image = next((item for item in images if isinstance(item, Mapping) and item.get("front")), None)
    image = image or next((item for item in images if isinstance(item, Mapping)), None)
    if not isinstance(image, Mapping):
        return ""
    thumbnails = image.get("thumbnails") if isinstance(image.get("thumbnails"), Mapping) else {}
    return _text(thumbnails.get("large") or thumbnails.get("500") or image.get("image"))


def collect_openlibrary(query: str, *, media_type: str, request: Request,
                        limit: int = 6) -> list[dict[str, Any]]:
    """Return bounded Open Library work candidates for ebook-like media."""
    if media_type not in {"ebook", "audiobook"} or not _text(query):
        return []
    payload, _ = request(
        "https://openlibrary.org/search.json?" + urllib.parse.urlencode({
            "q": _text(query), "limit": max(1, min(int(limit), 10)),
            "fields": "key,title,author_name,first_publish_year,cover_i,ratings_average,first_sentence,subject",
        }),
        headers={"Accept": "application/json"},
    )
    docs = payload.get("docs", []) if isinstance(payload, Mapping) else []
    query_tokens = _meaningful_tokens(_text(query))
    required_overlap = max(1, min(2, len(query_tokens)))
    results = []
    for doc in docs:
        if not isinstance(doc, Mapping):
            continue
        key = _text(doc.get("key"))
        title = _text(doc.get("title"))
        if not key or not title:
            continue
        if len(query_tokens & _meaningful_tokens(title)) < required_overlap:
            continue
        authors = doc.get("author_name") if isinstance(doc.get("author_name"), list) else []
        author = _text(authors[0]) if authors else ""
        subjects = doc.get("subject") if isinstance(doc.get("subject"), list) else []
        genres = [_text(value) for value in subjects[:3] if _text(value)]
        poster_path = (f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
                       if doc.get("cover_i") else "")
        if not poster_path:
            continue
        label = "Open Library audiobook discovery" if media_type == "audiobook" else "Open Library ebook discovery"
        results.append({
            "media_type": media_type,
            "authority": "openlibrary",
            "authority_id": key,
            "title": title,
            "author": author,
            "year": _first_year(doc.get("first_publish_year")),
            "rating": doc.get("ratings_average"),
            "score": _score(doc.get("ratings_average")),
            "genres": genres,
            "overview": (_first_sentence(doc.get("first_sentence")) or
                         (f"A work by {author}." if author else "")),
            "poster_path": poster_path,
            "source_label": label,
            "signals": [f"matches the configured {media_type} seed: {_text(query)}"],
            "explanation": f"Discovered through {label.lower()} for the configured seed.",
        })
    return results


def collect_openlibrary_author(author: str, *, media_type: str, request: Request,
                               offset: int = 0, limit: int = 6) -> list[dict[str, Any]]:
    """Discover other works by a recently read or heard author."""
    if media_type not in {"ebook", "audiobook"} or not _text(author):
        return []
    payload, _ = request(
        "https://openlibrary.org/search.json?" + urllib.parse.urlencode({
            "author": _text(author), "limit": max(1, min(int(limit), 10)),
            "offset": max(0, int(offset)),
            "fields": "key,title,author_name,first_publish_year,cover_i,ratings_average,first_sentence,subject",
        }),
        headers={"Accept": "application/json", "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"},
    )
    docs = payload.get("docs", []) if isinstance(payload, Mapping) else []
    return _openlibrary_candidates(
        docs, media_type=media_type,
        source_label=f"Open Library {media_type} author discovery",
        signal=f"another work by recently enjoyed author: {_text(author)}",
        expected_author=_text(author),
    )


def collect_openlibrary_subject(subject: str, *, media_type: str, request: Request,
                                offset: int = 0, limit: int = 6) -> list[dict[str, Any]]:
    """Discover rotating works from a sanitized recent-history subject."""
    if media_type not in {"ebook", "audiobook"} or not _text(subject):
        return []
    slug = re.sub(r"[^a-z0-9]+", "_", _text(subject).casefold()).strip("_")
    if not slug:
        return []
    payload, _ = request(
        f"https://openlibrary.org/subjects/{urllib.parse.quote(slug, safe='')}.json?" +
        urllib.parse.urlencode({"limit": max(1, min(int(limit), 10)), "offset": max(0, int(offset))}),
        headers={"Accept": "application/json", "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"},
    )
    works = payload.get("works", []) if isinstance(payload, Mapping) else []
    docs = []
    for work in works if isinstance(works, list) else []:
        if not isinstance(work, Mapping):
            continue
        authors = work.get("authors") if isinstance(work.get("authors"), list) else []
        docs.append({
            "key": work.get("key"), "title": work.get("title"),
            "author_name": [value.get("name") for value in authors if isinstance(value, Mapping) and value.get("name")],
            "first_publish_year": work.get("first_publish_year"),
            "cover_i": work.get("cover_id"), "subject": [subject],
            "ratings_average": work.get("ratings_average"),
        })
    return _openlibrary_candidates(
        docs, media_type=media_type,
        source_label=f"Open Library {media_type} subject discovery",
        signal=f"matches a subject from recent reading or listening: {_text(subject)}",
    )


def _openlibrary_candidates(docs, *, media_type: str, source_label: str,
                            signal: str, expected_author: str = "") -> list[dict[str, Any]]:
    results = []
    for doc in docs if isinstance(docs, list) else []:
        if not isinstance(doc, Mapping):
            continue
        key, title = _text(doc.get("key")), _text(doc.get("title"))
        authors = doc.get("author_name") if isinstance(doc.get("author_name"), list) else []
        author = _text(authors[0]) if authors else ""
        if not key or not title or (expected_author and expected_author.casefold() not in
                                   {_text(value).casefold() for value in authors}):
            continue
        cover_id = doc.get("cover_i")
        if not cover_id:
            continue
        subjects = doc.get("subject") if isinstance(doc.get("subject"), list) else []
        results.append({
            "media_type": media_type, "authority": "openlibrary", "authority_id": key,
            "title": title, "author": author, "year": _first_year(doc.get("first_publish_year")),
            "rating": doc.get("ratings_average"), "score": _score(doc.get("ratings_average")),
            "genres": [_text(value) for value in subjects[:3] if _text(value)],
            "overview": (_first_sentence(doc.get("first_sentence")) or
                         (f"A work by {author}." if author else "")),
            "poster_path": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg",
            "source_url": "https://openlibrary.org" + key,
            "source_label": source_label, "signals": [signal],
            "explanation": f"Discovered through {source_label.lower()}.",
        })
    return results


def collect_musicbrainz(query: str, *, request: Request, limit: int = 6) -> list[dict[str, Any]]:
    """Return exact release-group candidates from MusicBrainz.

    ``query`` is an explicit ``artist|album`` seed. Exact matching prevents a
    broad catalog search from becoming an accidental acquisition suggestion.
    """
    artist, separator, album = _text(query).partition("|")
    if not separator or not artist or not album:
        return []
    mb_query = f'artist:"{artist}" AND releasegroup:"{album}"'
    payload, _ = request(
        "https://musicbrainz.org/ws/2/release-group/?" + urllib.parse.urlencode({
            "query": mb_query, "fmt": "json", "limit": max(1, min(int(limit), 10)),
        }),
        headers={
            "Accept": "application/json",
            "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)",
        },
    )
    groups = payload.get("release-groups", []) if isinstance(payload, Mapping) else []
    results = []
    for group in groups:
        if not isinstance(group, Mapping):
            continue
        title = _text(group.get("title"))
        mbid = _text(group.get("id"))
        if not title or not mbid:
            continue
        artists = group.get("artist-credit") if isinstance(group.get("artist-credit"), list) else []
        credited_artist = _text((artists[0] or {}).get("name")) if artists and isinstance(artists[0], Mapping) else ""
        if credited_artist.casefold() != artist.casefold() or title.casefold() != album.casefold():
            continue
        poster_path = _music_artwork(mbid, request)
        if not poster_path:
            continue
        results.append({
            "media_type": "album",
            "authority": "musicbrainz",
            "authority_id": mbid,
            "title": title,
            "artist": credited_artist,
            "year": _first_year(group.get("first-release-date")),
            "score": _score(group.get("score"), 0.62),
            "poster_path": poster_path,
            "overview": f"{title} by {credited_artist}.",
            "source_label": "MusicBrainz exact release-group discovery",
            "signals": [f"matches the configured music seed: {artist} — {album}"],
            "explanation": "Exact artist and album match from MusicBrainz; Lidarr remains the request authority.",
        })
    return results


def collect_listenbrainz_albums(seed_artist: str, *, request: Request,
                                rotation: int = 0, limit: int = 2,
                                pause: Callable[[float], None] = time.sleep) -> list[dict[str, Any]]:
    """Discover albums from artists related to a recent Jellyfin artist.

    ListenBrainz supplies the similarity signal. MusicBrainz remains the stable
    release-group identity and Cover Art Archive supplies display art.
    """
    artist = _text(seed_artist)
    if not artist:
        return []
    headers = {"Accept": "application/json",
               "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"}
    search, _ = request(
        "https://musicbrainz.org/ws/2/artist/?" + urllib.parse.urlencode({
            "query": f'artist:"{artist}"', "fmt": "json", "limit": 5,
        }), headers=headers)
    matches = [value for value in search.get("artists", [])
               if isinstance(value, Mapping) and _text(value.get("name")).casefold() == artist.casefold()]
    if not matches:
        return []
    best_score = max(int(value.get("score") or 0) for value in matches)
    best = [value for value in matches if int(value.get("score") or 0) == best_score]
    if len(best) != 1 or not best[0].get("id"):
        return []
    seed_mbid = _text(best[0]["id"])
    radio, _ = request(
        f"https://api.listenbrainz.org/1/lb-radio/artist/{urllib.parse.quote(seed_mbid, safe='')}?" +
        urllib.parse.urlencode({"mode": "medium", "max_similar_artists": 8,
                                "max_recordings_per_artist": 1,
                                "pop_begin": 20, "pop_end": 80}),
        headers=headers)
    similar = []
    if isinstance(radio, Mapping):
        for values in radio.values():
            for value in values if isinstance(values, list) else []:
                if not isinstance(value, Mapping):
                    continue
                mbid = _text(value.get("similar_artist_mbid"))
                name = _text(value.get("similar_artist_name"))
                if mbid and name and mbid != seed_mbid:
                    similar.append((mbid, name, int(value.get("total_listen_count") or 0)))
    similar = list(dict.fromkeys(similar))
    if not similar:
        return []
    start = max(0, int(rotation)) % len(similar)
    similar = similar[start:] + similar[:start]
    results = []
    for mbid, name, listen_count in similar[:max(1, min(int(limit), 3))]:
        pause(1.05)
        payload, _ = request(
            "https://musicbrainz.org/ws/2/release-group/?" + urllib.parse.urlencode({
                "artist": mbid, "type": "album", "release-group-status": "website-default",
                "fmt": "json", "limit": 6, "offset": (max(0, int(rotation)) % 3) * 6,
            }), headers=headers)
        groups = payload.get("release-groups", []) if isinstance(payload, Mapping) else []
        for group in groups if isinstance(groups, list) else []:
            if not isinstance(group, Mapping) or not group.get("id") or not group.get("title"):
                continue
            poster_path = _music_artwork(_text(group["id"]), request)
            if not poster_path:
                continue
            results.append({
                "media_type": "album", "authority": "musicbrainz",
                "authority_id": _text(group["id"]), "title": _text(group["title"]),
                "artist": name, "year": _first_year(group.get("first-release-date")),
                "score": min(0.90, 0.62 + min(listen_count, 10000) / 50000.0),
                "poster_path": poster_path, "overview": f"{group['title']} by {name}.",
                "source_url": f"https://musicbrainz.org/release-group/{group['id']}",
                "source_label": "ListenBrainz similar-artist discovery",
                "signals": [f"related to recently played artist: {artist}"],
                "explanation": "ListenBrainz identified a related artist; MusicBrainz supplied the album identity.",
            })
            break
    return results
