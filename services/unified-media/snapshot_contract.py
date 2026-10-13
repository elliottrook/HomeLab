"""Sanitized snapshot types shared by M3 service readers and ranking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Tuple

from recommendation_model import Recommendation


@dataclass(frozen=True)
class SnapshotItem:
    media_type: str
    authority: str
    authority_id: str
    title: str
    owned: bool = False
    archived: bool = False
    match_count: int = 1
    signals: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LibrarySnapshot:
    source: str
    captured_at: str
    items: Tuple[SnapshotItem, ...]
    history_ids: Tuple[str, ...] = field(default_factory=tuple)


def merge_snapshots(snapshots: Iterable[LibrarySnapshot]) -> Tuple[SnapshotItem, ...]:
    """Merge records by authority identity without trusting raw service data."""
    merged = {}
    for snapshot in snapshots:
        for item in snapshot.items:
            key = (item.authority, item.authority_id)
            if key not in merged:
                merged[key] = item
            else:
                old = merged[key]
                merged[key] = SnapshotItem(
                    media_type=old.media_type,
                    authority=old.authority,
                    authority_id=old.authority_id,
                    title=old.title,
                    owned=old.owned or item.owned,
                    archived=old.archived or item.archived,
                    match_count=max(old.match_count, item.match_count),
                    signals=tuple(dict.fromkeys(old.signals + item.signals)),
                )
    return tuple(sorted(merged.values(), key=lambda item: (item.media_type, item.title.casefold(), item.authority_id)))


def to_recommendations(items: Iterable[SnapshotItem]) -> Tuple[Recommendation, ...]:
    """Convert sanitized snapshot records to rankable candidates."""
    return tuple(
        Recommendation(
            media_type=item.media_type,
            authority=item.authority,
            authority_id=item.authority_id,
            title=item.title,
            score=0.0,
            signals=item.signals,
            owned=item.owned,
            archived=item.archived,
            match_count=item.match_count,
        )
        for item in items
    )
