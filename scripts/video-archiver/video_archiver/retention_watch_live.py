"""Read-only, all-user Jellyfin watch observations for bounded item sets."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlencode

from .retention_policy import UserWatch
from .retention_reconcile import CompleteUserView
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
