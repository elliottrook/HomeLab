"""Read-only file-identity and household-watch reconciliation primitives.

Adapters may feed this module complete ARR/Jellyfin snapshots. An incomplete
user response or ambiguous mapped path is a hold, never an implicit unwatch.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath

from .retention_policy import UserWatch


@dataclass(frozen=True)
class PathMap:
    arr_root: str
    jellyfin_root: str

    def map(self, arr_path: str) -> str | None:
        if not arr_path.startswith("/") or not self.arr_root.startswith("/"):
            return None
        if not self.jellyfin_root.startswith("/"):
            return None
        if ".." in PurePosixPath(arr_path).parts:
            return None
        try:
            suffix = PurePosixPath(arr_path).relative_to(PurePosixPath(self.arr_root))
        except ValueError:
            return None
        return str(PurePosixPath(self.jellyfin_root) / suffix)


@dataclass(frozen=True)
class ArrFileFact:
    provider_id: str
    arr_file_id: int
    container_path: str


@dataclass(frozen=True)
class JellyfinFileFact:
    item_id: str
    path: str
    physical_present: bool


@dataclass(frozen=True)
class FileMatch:
    item_id: str
    provider_id: str | None
    arr_file_id: int | None
    reason: str | None


def match_files(
    arr_files: tuple[ArrFileFact, ...], jellyfin_files: tuple[JellyfinFileFact, ...],
    maps: tuple[PathMap, ...],
) -> tuple[FileMatch, ...]:
    """Require one ARR record, one Jellyfin item and a present physical file."""
    mapped: dict[str, list[ArrFileFact]] = {}
    for record in arr_files:
        translated = [value for path_map in maps if (value := path_map.map(record.container_path))]
        if len(translated) != 1 or record.arr_file_id <= 0 or not record.provider_id:
            continue
        mapped.setdefault(translated[0], []).append(record)
    jf_counts = Counter(item.path for item in jellyfin_files)
    results: list[FileMatch] = []
    for item in jellyfin_files:
        reason: str | None = None
        candidates = mapped.get(item.path, ())
        if (not item.item_id or not item.path.startswith("/")
                or ".." in PurePosixPath(item.path).parts or not item.physical_present):
            reason = "Jellyfin item or physical file unverified"
        elif jf_counts[item.path] != 1:
            reason = "duplicate Jellyfin path"
        elif len(candidates) != 1:
            reason = "missing or ambiguous ARR file record"
        if reason:
            results.append(FileMatch(item.item_id, None, None, reason))
        else:
            record = candidates[0]
            results.append(FileMatch(item.item_id, record.provider_id, record.arr_file_id, None))
    return tuple(results)


@dataclass(frozen=True)
class CompleteUserView:
    user_id: str
    complete: bool
    # The adapter supplies an explicit result for each item. A missing item is
    # unknown; it is never interpreted as an unwatched item.
    item_watch: dict[str, UserWatch]


def watch_for_item(
    item_id: str, views: tuple[CompleteUserView, ...],
    expected_user_ids: frozenset[str],
) -> tuple[UserWatch, ...] | None:
    if not expected_user_ids or len(views) != len(expected_user_ids):
        return None
    if {view.user_id for view in views} != expected_user_ids:
        return None
    if any(not view.complete for view in views):
        return None
    rows: list[UserWatch] = []
    for view in sorted(views, key=lambda value: value.user_id):
        row = view.item_watch.get(item_id)
        if row is None or row.user_id != view.user_id:
            return None
        rows.append(row)
    return tuple(rows)
