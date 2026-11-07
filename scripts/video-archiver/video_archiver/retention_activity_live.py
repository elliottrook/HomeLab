"""Read-only Jellyfin active-playback observation for retention holds."""

from __future__ import annotations

from collections.abc import Callable
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
import json

from .retention_years_live import _item_id


FetchSessions = Callable[[str, dict[str, str]], tuple[int, object]]


def _fetch_sessions(url: str, headers: dict[str, str]) -> tuple[int, object]:
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(Request(url, headers=headers), timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, None


def collect_active_item_ids(jellyfin_url: str, jellyfin_api_key: str, *,
                            fetch: FetchSessions = _fetch_sessions) -> frozenset[str]:
    """Return every session's current item, including paused sessions.

    API failure or malformed session data raises so the caller holds every
    candidate; a successful empty list means no observed playback.
    """
    if not jellyfin_url or not jellyfin_api_key:
        raise ValueError("Jellyfin URL and key are required")
    status, payload = fetch(
        f"{jellyfin_url.rstrip('/')}/Sessions",
        {"Authorization": (
            'MediaBrowser Client="retention-activity-audit", Device="TrueNAS", '
            'DeviceId="aster-retention-activity-audit", Version="1", '
            f'Token="{jellyfin_api_key}"'
        )},
    )
    if status != 200 or not isinstance(payload, list):
        raise RuntimeError("Jellyfin active sessions unavailable")
    active: set[str] = set()
    for session in payload:
        if not isinstance(session, dict):
            raise RuntimeError("Jellyfin active session malformed")
        item = session.get("NowPlayingItem")
        if item is None:
            continue
        if not isinstance(item, dict) or not isinstance(item.get("Id"), str) or not item["Id"]:
            raise RuntimeError("Jellyfin active item identity unavailable")
        identity = _item_id(item["Id"])
        if not identity or identity == "none":
            raise RuntimeError("Jellyfin active item identity invalid")
        active.add(identity)
    return frozenset(active)


def scope_has_active_playback(item_ids: tuple[str, ...],
                              active_item_ids: frozenset[str]) -> bool:
    """The caller supplies movie or all episode/ancestor IDs in the scope."""
    if not item_ids:
        raise ValueError("scope item IDs are required")
    normalized = tuple(_item_id(item) for item in item_ids)
    if any(not item or item == "none" for item in normalized):
        raise ValueError("invalid scope item ID")
    return bool(set(normalized) & active_item_ids)
