"""Sanitized requestable-discovery feed for AsterTV's Acquisition Hub.

The feed is deliberately read-only and credential-free. Acquisition services
remain authoritative for requests; the television receives only bounded display
metadata and a canonical identity it can return to the appropriate broker.
"""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable, Mapping


DOMAINS = {
    "media": frozenset(("movie", "tv")),
    "music": frozenset(("album",)),
    "books": frozenset(("ebook", "audiobook")),
}
AUTHORITIES = {
    "movie": "seerr",
    "tv": "seerr",
    "album": "musicbrainz",
    "ebook": "openlibrary",
    "audiobook": "openlibrary",
}
MBID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
OPENLIBRARY = re.compile(r"/(?:works/OL[1-9][0-9]{0,12}W|books/OL[1-9][0-9]{0,12}M)")
MAX_SOURCE_ITEMS = 60
MAX_DOMAIN_ITEMS = 12
MAX_FEED_BYTES = 256 * 1024
ITEM_KEYS = frozenset((
    "identity", "media_type", "title", "year", "overview", "poster",
    "backdrop", "explanation", "owned", "archived", "request_state",
    "primary_action", "progress",
))


class DiscoveryFeedError(ValueError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise DiscoveryFeedError(code)


def _text(value: Any, maximum: int, *, required: bool = False) -> str:
    _require(isinstance(value, str), "aster-tv-feed-text")
    value = value.strip()
    _require(len(value) <= maximum and (not required or bool(value)),
             "aster-tv-feed-text")
    return value


def _generated_at(value: Any) -> str:
    value = _text(value, 40, required=True)
    _require(value.endswith("Z"), "aster-tv-feed-time")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise DiscoveryFeedError("aster-tv-feed-time") from error
    _require(parsed.utcoffset() is not None, "aster-tv-feed-time")
    return value


def _identity(media_type: str, authority: Any, authority_id: Any) -> str:
    expected = AUTHORITIES[media_type]
    _require(authority == expected and isinstance(authority_id, str),
             "aster-tv-feed-identity")
    authority_id = authority_id.strip()
    if authority == "seerr":
        _require(re.fullmatch(r"[1-9][0-9]{0,15}", authority_id) is not None,
                 "aster-tv-feed-identity")
        return f"seerr:{media_type}:{authority_id}"
    if authority == "musicbrainz":
        _require(MBID.fullmatch(authority_id) is not None,
                 "aster-tv-feed-identity")
        return f"musicbrainz:release-group:{authority_id.lower()}"
    _require(OPENLIBRARY.fullmatch(authority_id) is not None,
             "aster-tv-feed-identity")
    return "openlibrary:" + authority_id


def _image(value: Any, *, kind: str, authority: str) -> str:
    value = _text(value or "", 500)
    if not value:
        return ""
    if authority == "seerr" and value.startswith("/"):
        width = "w1280" if kind == "backdrop" else "w500"
        return f"https://image.tmdb.org/t/p/{width}{value}"
    _require(value.startswith("https://"), "aster-tv-feed-image")
    return value


def _item(value: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, Mapping), "aster-tv-feed-item")
    media_type = value.get("media_type")
    _require(media_type in AUTHORITIES, "aster-tv-feed-item")
    authority = value.get("authority")
    owned = value.get("owned", False)
    archived = value.get("archived", False)
    _require(type(owned) is bool and type(archived) is bool
             and not owned and not archived, "aster-tv-feed-state")
    year = _text(value.get("year") or "", 4)
    _require(not year or re.fullmatch(r"[12][0-9]{3}", year) is not None,
             "aster-tv-feed-year")
    return {
        "identity": _identity(media_type, authority, value.get("authority_id")),
        "media_type": media_type,
        "title": _text(value.get("title"), 200, required=True),
        "year": year,
        "overview": _text(value.get("overview") or "", 3000),
        "poster": _image(value.get("poster_path"), kind="poster", authority=authority),
        "backdrop": _image(value.get("backdrop_path"), kind="backdrop", authority=authority),
        "explanation": _text(value.get("explanation") or "", 600),
        "owned": False,
        "archived": False,
        "request_state": "none",
        "primary_action": "request",
        "progress": 0.0,
    }


def build_feeds(recommendations: Iterable[Mapping[str, Any]], generated_at: str,
                *, limit: int = MAX_DOMAIN_ITEMS) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    """Return domain feeds plus explicit invalid/duplicate/limit counters."""
    rows = list(recommendations)
    _require(len(rows) <= MAX_SOURCE_ITEMS and type(limit) is int
             and 1 <= limit <= MAX_DOMAIN_ITEMS, "aster-tv-feed-input")
    timestamp = _generated_at(generated_at)
    grouped = {domain: [] for domain in DOMAINS}
    seen = set()
    stats = {"invalid": 0, "duplicate": 0, "over_limit": 0}
    for value in rows:
        try:
            item = _item(value)
        except DiscoveryFeedError:
            stats["invalid"] += 1
            continue
        domain = next(name for name, types in DOMAINS.items()
                      if item["media_type"] in types)
        if item["identity"] in seen:
            stats["duplicate"] += 1
            continue
        if len(grouped[domain]) >= limit:
            stats["over_limit"] += 1
            continue
        seen.add(item["identity"])
        grouped[domain].append(item)
    return ({domain: {"schema": 1, "generated_at": timestamp, "items": items}
             for domain, items in grouped.items()}, stats)


def write_feeds(directory: Path, feeds: Mapping[str, Mapping[str, Any]]) -> None:
    directory = Path(directory)
    _require(set(feeds) == set(DOMAINS), "aster-tv-feed-domains")
    directory.mkdir(parents=True, exist_ok=True)
    for domain in sorted(DOMAINS):
        payload = (json.dumps(feeds[domain], indent=2, ensure_ascii=False) + "\n").encode()
        _require(len(payload) <= MAX_FEED_BYTES, "aster-tv-feed-size")
        descriptor, temporary = tempfile.mkstemp(prefix=f".{domain}-", dir=str(directory))
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o644)
            os.replace(temporary, directory / f"aster-tv-discovery-{domain}.json")
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def read_feed(directory: Path, domain: str) -> dict[str, Any]:
    _require(domain in DOMAINS, "aster-tv-feed-domain")
    path = Path(directory) / f"aster-tv-discovery-{domain}.json"
    try:
        raw = path.read_bytes()
        _require(0 < len(raw) <= MAX_FEED_BYTES, "aster-tv-feed-size")
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DiscoveryFeedError("aster-tv-feed-unavailable") from error
    _require(type(value) is dict and set(value) == {"schema", "generated_at", "items"}
             and value["schema"] == 1 and isinstance(value["items"], list),
             "aster-tv-feed-schema")
    # Rebuild from the stored rows to keep the broker's read path fail-closed.
    _generated_at(value["generated_at"])
    _require(len(value["items"]) <= MAX_DOMAIN_ITEMS, "aster-tv-feed-size")
    for item in value["items"]:
        _require(type(item) is dict and set(item) == ITEM_KEYS
                 and item.get("media_type") in DOMAINS[domain]
                 and item.get("owned") is False and item.get("archived") is False
                 and item.get("request_state") == "none"
                 and item.get("primary_action") == "request"
                 and item.get("progress") == 0.0,
                 "aster-tv-feed-item")
        _text(item.get("title"), 200, required=True)
        _text(item.get("year"), 4)
        _text(item.get("overview"), 3000)
        _text(item.get("poster"), 500)
        _text(item.get("backdrop"), 500)
        _text(item.get("explanation"), 600)
        media_type = item["media_type"]
        identity = item.get("identity")
        _require(isinstance(identity, str), "aster-tv-feed-identity")
        if media_type in ("movie", "tv"):
            pattern = rf"seerr:{media_type}:[1-9][0-9]{{0,15}}"
        elif media_type == "album":
            pattern = (r"musicbrainz:release-group:[0-9a-f]{8}-[0-9a-f]{4}-"
                       r"[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
        else:
            pattern = (r"openlibrary:/(?:works/OL[1-9][0-9]{0,12}W|"
                       r"books/OL[1-9][0-9]{0,12}M)")
        _require(re.fullmatch(pattern, identity, re.IGNORECASE) is not None,
                 "aster-tv-feed-identity")
    return value
