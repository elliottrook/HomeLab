"""Read-only, all-user Jellyfin watch observations for bounded item sets."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from .retention_playback import PlaybackLogEvidence, read_playback_log_evidence
from .retention_policy import UserWatch
from .retention_reconcile import CompleteUserView, watch_for_item
from .retention_years_live import FetchJson, _fetch_json, _item_id


def _timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError("invalid Jellyfin last-played field")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError("Jellyfin last-played field lacks timezone")
    return parsed


def collect_user_views(
    item_ids: tuple[str, ...], *, user_ids: frozenset[str],
    jellyfin_url: str, jellyfin_api_key: str,
    fetch: FetchJson = _fetch_json,
) -> tuple[CompleteUserView, ...]:
    """Return explicit per-item watch facts; missing items remain unknown.

    A missing user, malformed UserData or API error fails the entire scan.
    A hidden item is omitted from a complete view and therefore held by
    ``watch_for_item``; it is never assumed unwatched.
    """
    if not item_ids or not user_ids or not jellyfin_api_key:
        raise ValueError("items, users and Jellyfin key are required")
    normalized = tuple(_item_id(value) for value in item_ids)
    if len(set(normalized)) != len(normalized) or any(not value for value in normalized):
        raise ValueError("duplicate or invalid Jellyfin item IDs")
    views = []
    for user_id in sorted(user_ids):
        observed: dict[str, UserWatch] = {}
        for start in range(0, len(normalized), 50):
            batch = normalized[start:start + 50]
            query = urlencode({"Ids": ",".join(batch), "Recursive": "true",
                               "EnableUserData": "true"})
            status, payload = fetch(
                f"{jellyfin_url.rstrip('/')}/Users/{user_id}/Items?{query}",
                {"Authorization": (
                    'MediaBrowser Client="retention-watch-audit", Device="TrueNAS", '
                    'DeviceId="aster-retention-watch-audit", Version="1", '
                    f'Token="{jellyfin_api_key}"'
                )},
            )
            if status != 200 or not isinstance(payload.get("Items"), list):
                raise RuntimeError("Jellyfin household watch page failed")
            for item in payload["Items"]:
                if not isinstance(item, dict):
                    raise RuntimeError("Jellyfin household watch item malformed")
                identity = _item_id(item.get("Id"))
                if identity not in batch or identity in observed:
                    raise RuntimeError("Jellyfin watch item duplicated or unexpected")
                state = item.get("UserData")
                if not isinstance(state, dict) or not all(
                    name in state for name in ("Played", "PlayCount", "PlaybackPositionTicks", "IsFavorite")
                ):
                    raise RuntimeError("Jellyfin watch state incomplete")
                if any(type(state[name]) is not int for name in ("PlayCount", "PlaybackPositionTicks")):
                    raise RuntimeError("Jellyfin watch counters invalid")
                if any(type(state[name]) is not bool for name in ("Played", "IsFavorite")):
                    raise RuntimeError("Jellyfin watch flags invalid")
                observed[identity] = UserWatch(
                    user_id=user_id, played=state["Played"],
                    play_count=state["PlayCount"],
                    progress_ticks=state["PlaybackPositionTicks"],
                    favorite=state["IsFavorite"],
                    last_played_at=_timestamp(state.get("LastPlayedDate")),
                )
        views.append(CompleteUserView(user_id, True, observed))
    return tuple(views)


def scope_watch_evidence(
    item_ids: tuple[str, ...], views: tuple[CompleteUserView, ...],
    expected_user_ids: frozenset[str], playback: PlaybackLogEvidence,
) -> tuple[tuple[UserWatch, ...], bool] | None:
    """Merge episode, season and series protection for one movie/season scope.

    The caller supplies every relevant Jellyfin item ID, including ancestors.
    A missing user/item or an absent playback scan holds the entire scope.
    """
    if not item_ids or playback.event_count <= 0:
        return None
    normalized = tuple(_item_id(value) for value in item_ids)
    if any(not value or value == "none" for value in normalized) or len(set(normalized)) != len(normalized):
        return None
    per_item = [watch_for_item(item, views, expected_user_ids) for item in normalized]
    if any(rows is None for rows in per_item):
        return None
    merged: list[UserWatch] = []
    for index, user_id in enumerate(sorted(expected_user_ids)):
        rows = [observed[index] for observed in per_item if observed is not None]
        last_played = [row.last_played_at for row in rows if row.last_played_at is not None]
        merged.append(UserWatch(
            user_id=user_id,
            played=any(row.played for row in rows),
            play_count=max(row.play_count for row in rows),
            last_played_at=max(last_played) if last_played else None,
            progress_ticks=max(row.progress_ticks for row in rows),
            favorite=any(row.favorite for row in rows),
            keep=any(row.keep for row in rows),
        ))
    return tuple(merged), bool(set(normalized) & playback.item_ids)
