"""Bind exact ARR and Jellyfin scope IDs to read-only activity evidence."""

from __future__ import annotations

from .retention_activity_live import scope_has_active_playback
from .retention_queue_live import QueueEvidence, scope_has_queued_download


def scope_has_active_work(*, kind: str, arr_id: int,
                          jellyfin_item_ids: tuple[str, ...],
                          active_jellyfin_item_ids: frozenset[str],
                          queue: QueueEvidence) -> bool:
    """Unknown queue identities or exact-scope playback protect the unit."""
    expected_queue = {"movie": "radarr", "season": "sonarr"}.get(kind)
    if expected_queue is None or queue.kind != expected_queue:
        raise ValueError("ARR queue kind does not match retention scope")
    return (scope_has_queued_download(arr_id, queue)
            or scope_has_active_playback(jellyfin_item_ids,
                                         active_jellyfin_item_ids))
