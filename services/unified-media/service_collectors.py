"""Opt-in, read-only service collectors for the unified media snapshot.

Collectors require an explicit URL and secret path. They return sanitized
SnapshotItem values and accept an injected request function so transport and
credential handling can be tested without contacting live services.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Tuple

from snapshot_contract import SnapshotItem
from snapshot_readers import (
    audiobookshelf_items,
    calibre_books,
    jellyfin_items,
    lazylibrarian_items,
    lidarr_albums,
    radarr_movies,
    sonarr_series,
)


Request = Callable[..., Tuple[Mapping[str, Any], Mapping[str, str]]]


def _secret(path: str) -> str:
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("configured secret path is empty")
    return value


def collect_arr(url: str, secret_path: str, authority: str, *, request: Request,
                endpoint: str = "") -> Tuple[SnapshotItem, ...]:
    """Read a Sonarr/Radarr library with an API key and no write methods."""
    if not endpoint:
        endpoint = "/api/v3/series" if authority == "sonarr" else "/api/v3/movie"
    payload, _ = request(url.rstrip("/") + endpoint, headers={"X-Api-Key": _secret(secret_path)})
    if not isinstance(payload, list):
        raise ValueError("ARR library response was not a list")
    if authority == "sonarr":
        return sonarr_series(payload)
    if authority == "radarr":
        return radarr_movies(payload)
    raise ValueError("unsupported ARR authority")


def collect_lidarr(url: str, secret_path: str, *, request: Request) -> Tuple[SnapshotItem, ...]:
    """Read the Lidarr album library using its v1 API and API key."""
    payload, _ = request(
        url.rstrip("/") + "/api/v1/album",
        headers={"X-Api-Key": _secret(secret_path)},
    )
    if not isinstance(payload, list):
        raise ValueError("Lidarr library response was not a list")
    return lidarr_albums(payload)


def collect_jellyfin(url: str, secret_path: str, *, request: Request,
                     archive_ids: Iterable[str] = ()) -> Tuple[SnapshotItem, ...]:
    """Read the Jellyfin library using an API key, retaining no user data."""
    payload, _ = request(
        url.rstrip("/") + "/Items",
        params={
            "Recursive": "true",
            "IncludeItemTypes": "Movie,Series,MusicAlbum,Book",
            "Fields": "ProviderIds",
        },
        headers={"Authorization": (
            'MediaBrowser Client="unified-media-reader", Device="TrueNAS", '
            'DeviceId="unified-media-reader", Version="1", '
            "Token=\"" + _secret(secret_path) + "\""
        )},
    )
    if not isinstance(payload, Mapping):
        raise ValueError("Jellyfin response was not an object")
    return jellyfin_items(payload, archive_ids=archive_ids)


def collect_audiobookshelf(url: str, token_path: str, *, request: Request,
                           library_ids: Iterable[str]) -> Tuple[SnapshotItem, ...]:
    """Read configured Audiobookshelf libraries with a bearer token."""
    token = _secret(token_path)
    items = []
    for library_id in library_ids:
        payload, _ = request(
            url.rstrip("/") + "/api/libraries/" + str(library_id) + "/items",
            headers={"Authorization": "Bearer " + token},
        )
        items.extend(audiobookshelf_items(payload))
    return tuple(items)


def collect_optional_books(payload: Any, *, source: str) -> Tuple[SnapshotItem, ...]:
    """Normalize already-fetched book data without adding a network path."""
    if source == "calibre":
        return calibre_books(payload)
    if source == "lazylibrarian":
        return lazylibrarian_items(payload)
    raise ValueError("unsupported book source")
