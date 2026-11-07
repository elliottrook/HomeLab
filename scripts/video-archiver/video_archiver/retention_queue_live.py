"""Read-only ARR queue evidence; unknown download identity holds all scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal
from urllib.parse import urlencode


Kind = Literal["radarr", "sonarr"]
FetchQueue = Callable[[str, dict[str, str]], tuple[int, object]]


@dataclass(frozen=True)
class QueueEvidence:
    kind: Kind
    active_arr_ids: frozenset[int]
    queue_count: int
    complete_identity: bool


def collect_queue(kind: Kind, base_url: str, api_key: str, *,
                  fetch: FetchQueue, page_size: int = 500) -> QueueEvidence:
    """Collect a bounded paged queue without logging titles or download IDs."""
    if kind not in ("radarr", "sonarr") or not base_url or not api_key:
        raise ValueError("ARR kind, URL and key are required")
    if type(page_size) is not int or not 1 <= page_size <= 1000:
        raise ValueError("invalid ARR queue page size")
    known: set[int] = set()
    queue_ids: set[int] = set()
    unknown = False
    total: int | None = None
    page = 1
    while True:
        params = {"page": page, "pageSize": page_size,
                  "includeUnknownMovieItems" if kind == "radarr" else
                  "includeUnknownSeriesItems": "true"}
        url = f"{base_url.rstrip('/')}/api/v3/queue?{urlencode(params)}"
        status, payload = fetch(url, {"X-Api-Key": api_key})
        if status != 200 or not isinstance(payload, dict):
            raise RuntimeError("ARR download queue unavailable")
        rows = payload.get("records")
        count = payload.get("totalRecords")
        if not isinstance(rows, list) or type(count) is not int or count < 0:
            raise RuntimeError("ARR download queue malformed")
        if total is None:
            total = count
            if total > 10_000:
                raise RuntimeError("ARR download queue exceeds audit bound")
        elif total != count:
            raise RuntimeError("ARR download queue changed during scan")
        for row in rows:
            if not isinstance(row, dict) or type(row.get("id")) is not int:
                raise RuntimeError("ARR download row identity malformed")
            queue_id = row["id"]
            if queue_id <= 0 or queue_id in queue_ids:
                raise RuntimeError("ARR download row duplicated")
            queue_ids.add(queue_id)
            arr_id = row.get("movieId" if kind == "radarr" else "seriesId")
            if type(arr_id) is int and arr_id > 0:
                known.add(arr_id)
            else:
                unknown = True
        if len(queue_ids) == total:
            break
        if not rows or len(queue_ids) > total or page * page_size >= total:
            raise RuntimeError("ARR download queue pages incomplete")
        page += 1
    return QueueEvidence(kind, frozenset(known), total, not unknown)


def scope_has_queued_download(arr_id: int, queue: QueueEvidence) -> bool:
    """A queue row with unknown identity protects every candidate."""
    if type(arr_id) is not int or arr_id <= 0:
        raise ValueError("invalid ARR scope identity")
    return not queue.complete_identity or arr_id in queue.active_arr_ids
