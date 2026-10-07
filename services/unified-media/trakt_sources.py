"""Bounded, read-only Trakt recommendation adapter.

The Jellyfin Trakt plugin and this adapter have separate credential boundaries.
The adapter is inert unless an explicit access-token path and client-id path are
configured. It never reads Jellyfin's plugin XML or writes to Trakt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping
import urllib.parse


Request = Callable[..., tuple[Any, Mapping[str, str]]]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _year(value: Any) -> str:
    text = _text(value)
    return text[:4] if len(text) >= 4 and text[:4].isdigit() else ""


def _candidate(item: Mapping[str, Any], media_type: str) -> dict[str, Any] | None:
    title = item.get("title") or item.get("show", {}).get("title")
    ids = item.get("ids") or item.get("movie", {}).get("ids") or item.get("show", {}).get("ids")
    if not _text(title) or not isinstance(ids, Mapping):
        return None
    trakt_id = ids.get("trakt")
    tmdb_id = ids.get("tmdb")
    if not trakt_id:
        return None
    return {
        "media_type": media_type,
        "authority": "trakt",
        "authority_id": str(tmdb_id or trakt_id),
        "trakt_id": str(trakt_id),
        "title": _text(title),
        "year": _year(item.get("year")),
        "overview": _text(item.get("overview")),
        "poster_path": "",
        "source_label": "Trakt personal recommendations",
        "source_url": f"https://trakt.tv/{'movies' if media_type == 'movie' else 'shows'}/{urllib.parse.quote(_text(title).lower().replace(' ', '-'))}",
        "explanation": "Recommended from the connected personal Trakt profile.",
    }


def collect_trakt_recommendations(*, request: Request, access_token_path: str,
                                  client_id_path: str, limit: int = 6) -> list[dict[str, Any]]:
    """Read small personal recommendation lists from Trakt.

    Trakt endpoint responses are intentionally treated as untrusted metadata;
    malformed items are skipped and results are hard-capped per media type.
    """
    access_token = Path(access_token_path).read_text(encoding="utf-8").strip()
    client_id = Path(client_id_path).read_text(encoding="utf-8").strip()
    if not access_token or not client_id:
        return []
    headers = {
        "Authorization": f"Bearer {access_token}",
        "trakt-api-key": client_id,
        "trakt-api-version": "2",
        "Accept": "application/json",
        "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)",
    }
    results: list[dict[str, Any]] = []
    for media_type, endpoint in (("movie", "/recommendations/movies"),
                                 ("tv", "/recommendations/shows")):
        payload, _ = request("https://api.trakt.tv" + endpoint,
                             headers=headers,
                             params={"limit": max(1, min(int(limit), 10))})
        if not isinstance(payload, list):
            continue
        for item in payload[:max(1, min(int(limit), 10))]:
            if isinstance(item, Mapping):
                candidate = _candidate(item, media_type)
                if candidate:
                    results.append(candidate)
    return results
