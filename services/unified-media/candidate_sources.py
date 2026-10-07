"""Bounded, read-only candidate adapters for non-video media.

These adapters return sanitized candidates only. They never call an acquisition
authority and deliberately require explicit seed queries, so a provider outage
or an empty configuration produces no guessed recommendations.
"""

from __future__ import annotations

import urllib.parse
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


def collect_openlibrary(query: str, *, media_type: str, request: Request,
                        limit: int = 6) -> list[dict[str, Any]]:
    """Return bounded Open Library work candidates for ebook-like media."""
    if media_type not in {"ebook", "audiobook"} or not _text(query):
        return []
    payload, _ = request(
        "https://openlibrary.org/search.json?" + urllib.parse.urlencode({
            "q": _text(query), "limit": max(1, min(int(limit), 10)),
            "fields": "key,title,author_name,first_publish_year,cover_i,ratings_average",
        }),
        headers={"Accept": "application/json"},
    )
    docs = payload.get("docs", []) if isinstance(payload, Mapping) else []
    results = []
    for doc in docs:
        if not isinstance(doc, Mapping):
            continue
        key = _text(doc.get("key"))
        title = _text(doc.get("title"))
        if not key or not title:
            continue
        authors = doc.get("author_name") if isinstance(doc.get("author_name"), list) else []
        author = _text(authors[0]) if authors else ""
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
            "poster_path": (f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
                            if doc.get("cover_i") else ""),
            "source_label": label,
            "signals": [f"matches the configured {media_type} seed: {_text(query)}"],
            "explanation": f"Discovered through {label.lower()} for the configured seed.",
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
        results.append({
            "media_type": "album",
            "authority": "musicbrainz",
            "authority_id": mbid,
            "title": title,
            "artist": credited_artist,
            "year": _first_year(group.get("first-release-date")),
            "score": _score(group.get("score"), 0.62),
            "source_label": "MusicBrainz exact release-group discovery",
            "signals": [f"matches the configured music seed: {artist} — {album}"],
            "explanation": "Exact artist and album match from MusicBrainz; Lidarr remains the request authority.",
        })
    return results
