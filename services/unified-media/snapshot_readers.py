"""Pure parsers for service-reader responses.

HTTP clients remain outside this module. These functions deliberately retain
only stable media identity, title, ownership/archive state and safe signals.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Tuple

from snapshot_contract import SnapshotItem


def jellyfin_items(payload: Mapping[str, Any], *, archive_ids: Iterable[str] = ()) -> Tuple[SnapshotItem, ...]:
    archived = set(str(value) for value in archive_ids)
    items = []
    for raw in payload.get("Items", []):
        if not isinstance(raw, Mapping):
            continue
        item_id = raw.get("Id")
        title = raw.get("Name")
        kind = _jellyfin_type(raw.get("Type"))
        if not item_id or not title or not kind:
            continue
        items.append(SnapshotItem(
            media_type=kind,
            authority="jellyfin",
            authority_id=str(item_id),
            title=str(title),
            owned=True,
            archived=str(item_id) in archived,
            signals=("in Jellyfin",),
        ))
    return tuple(items)


def seerr_requests(payload: Mapping[str, Any]) -> Tuple[SnapshotItem, ...]:
    items = []
    for raw in payload.get("results", []):
        if not isinstance(raw, Mapping):
            continue
        media = raw.get("media") or {}
        media_id = media.get("tmdbId") or media.get("tvdbId") or raw.get("id")
        title = _first(raw, "title", "name") or _first(media, "title", "name")
        media_type = raw.get("mediaType") or media.get("mediaType")
        if not media_id or not title or media_type not in {"movie", "tv"}:
            continue
        items.append(SnapshotItem(
            media_type=str(media_type),
            authority="seerr",
            authority_id=str(media_id),
            title=str(title),
            signals=("already requested",),
        ))
    return tuple(items)


def lidarr_albums(payload: Iterable[Mapping[str, Any]]) -> Tuple[SnapshotItem, ...]:
    items = []
    for raw in payload:
        album_id = raw.get("foreignAlbumId") or raw.get("id")
        title = raw.get("title")
        if not album_id or not title:
            continue
        monitored = bool(raw.get("monitored"))
        stats = raw.get("statistics") or {}
        owned = int(stats.get("trackFileCount", 0) or 0) > 0
        items.append(SnapshotItem(
            media_type="album",
            authority="lidarr",
            authority_id=str(album_id),
            title=str(title),
            owned=owned,
            signals=(("monitored in Lidarr" if monitored else "in Lidarr"),),
        ))
    return tuple(items)


def _jellyfin_type(value: Optional[str]) -> Optional[str]:
    return {"Movie": "movie", "Series": "tv", "MusicAlbum": "album", "Book": "ebook"}.get(value)


def _first(mapping: Mapping[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        if mapping.get(key):
            return mapping[key]
    return None
