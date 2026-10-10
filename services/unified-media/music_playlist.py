"""Pure music playlist lifecycle primitives shared by portal integrations.

This module plans work only.  The existing playlist bridge remains the
mutation authority; callers provide an API function when they deliberately
run an execute path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class PlaylistTrack:
    title: str
    artist: str
    album: str = ""


def normalize(value: str) -> str:
    return " ".join(str(value).casefold().replace("-", " ").split())


def match_tracks(tracks: Iterable[PlaylistTrack], jellyfin_items: Iterable[Mapping[str, Any]]):
    """Return ordered matches and missing tracks; never silently drops tracks."""
    items = list(jellyfin_items)
    matched, missing = [], []
    for track in tracks:
        candidates = []
        for item in items:
            if normalize(item.get("Name", "")) != normalize(track.title):
                continue
            names = list(item.get("Artists", [])) + [item.get("AlbumArtist", "")]
            if not any(normalize(track.artist) == normalize(name) for name in names if name):
                continue
            if track.album and normalize(item.get("Album", "")) != normalize(track.album):
                continue
            candidates.append(item)
        if len(candidates) == 1:
            matched.append((track, candidates[0]))
        else:
            missing.append(track)
    return matched, missing


def retry(operation: Callable[[], Any], *, attempts: int = 3,
          retryable: tuple[type[BaseException], ...] = (Exception,)) -> Any:
    """Retry only the caller's bounded operation; no sleeps in unit tests."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    last = None
    for _ in range(attempts):
        try:
            return operation()
        except retryable as exc:
            last = exc
    assert last is not None
    raise last


def playlist_plan(name: str, tracks: Iterable[PlaylistTrack], jellyfin_items: Iterable[Mapping[str, Any]]):
    matched, missing = match_tracks(tracks, jellyfin_items)
    return {
        "name": name,
        "complete": not missing,
        "matched_ids": [item["Id"] for _, item in matched],
        "missing": [track.__dict__ for track in missing],
        "source_count": len(matched) + len(missing),
    }
