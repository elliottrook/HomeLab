"""Pure cross-media landing-page recommendation and hero state contract.

The television consumes a purpose-built sanitized feed. It never reads portal,
ARR, downloader or library credentials and performs no network or Kodi I/O here.
Automatic recommendation rotation may change the hero, never remote focus.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re


DOMAINS = {
    "media": frozenset(("movie", "tv")),
    "music": frozenset(("album",)),
    "books": frozenset(("ebook", "audiobook")),
}
AUTHORITIES = frozenset(("seerr", "musicbrainz", "openlibrary"))
MEDIA_AUTHORITIES = {
    "movie": "seerr",
    "tv": "seerr",
    "album": "musicbrainz",
    "ebook": "openlibrary",
    "audiobook": "openlibrary",
}
REQUEST_STATES = frozenset(("none", "pending", "approved", "processing",
                            "available", "declined", "failed"))
ACTIONS = frozenset(("play", "resume", "details", "request", "none"))
IDENTITY = re.compile(r"(seerr|musicbrainz|openlibrary):(.{1,160})")
IDENTITY_PATHS = {
    "seerr": re.compile(r"(?:movie|tv):[1-9][0-9]{0,15}"),
    "musicbrainz": re.compile(
        r"(?:release|release-group):[0-9a-f]{8}-[0-9a-f]{4}-"
        r"[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE),
    "openlibrary": re.compile(r"/(?:works/OL[1-9][0-9]{0,12}W|books/OL[1-9][0-9]{0,12}M)"),
}
MAX_BYTES = 256 * 1024
MAX_ITEMS = 60
MAX_AGE_SECONDS = 6 * 60 * 60


def require(value, code):
    if not value:
        raise ValueError(code)


def _utc(value):
    require(isinstance(value, str) and len(value) <= 40,
            "landing-feed-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("landing-feed-time") from exc
    require(parsed.tzinfo is not None, "landing-feed-time")
    return parsed.astimezone(timezone.utc)


def _text(value, maximum, code, empty=False):
    require(isinstance(value, str) and len(value) <= maximum
            and (empty or bool(value.strip())), code)
    return value.strip()


@dataclass(frozen=True)
class HeroItem:
    identity: str
    media_type: str
    title: str
    year: str
    overview: str
    poster: str
    backdrop: str
    explanation: str
    owned: bool
    archived: bool
    request_state: str
    primary_action: str
    progress: float


@dataclass(frozen=True)
class Feed:
    generated_at: datetime
    domain: str
    items: tuple


def hero_item(value, domain):
    required = {
        "identity", "media_type", "title", "year", "overview", "poster",
        "backdrop", "explanation", "owned", "archived", "request_state",
        "primary_action", "progress",
    }
    require(domain in DOMAINS and type(value) is dict and set(value) == required,
            "landing-item-schema")
    identity = value["identity"]
    match = IDENTITY.fullmatch(identity) if isinstance(identity, str) else None
    media_type = value["media_type"]
    require(match is not None and match.group(1) in AUTHORITIES
            and media_type in DOMAINS[domain]
            and MEDIA_AUTHORITIES.get(media_type) == match.group(1)
            and IDENTITY_PATHS[match.group(1)].fullmatch(match.group(2)),
            "landing-item-identity")
    if match.group(1) == "seerr":
        require(match.group(2).startswith(media_type + ":"),
                "landing-item-identity")
    title = _text(value["title"], 200, "landing-item-text")
    year = _text(value["year"], 4, "landing-item-text", empty=True)
    require(year == "" or re.fullmatch(r"[12][0-9]{3}", year),
            "landing-item-text")
    overview = _text(value["overview"], 3000, "landing-item-text", empty=True)
    poster = _text(value["poster"], 500, "landing-item-text", empty=True)
    backdrop = _text(value["backdrop"], 500, "landing-item-text", empty=True)
    explanation = _text(value["explanation"], 600, "landing-item-text",
                        empty=True)
    require(type(value["owned"]) is bool and type(value["archived"]) is bool
            and not (value["owned"] and value["archived"]),
            "landing-item-state")
    state = value["request_state"]
    action = value["primary_action"]
    progress = value["progress"]
    require(state in REQUEST_STATES and action in ACTIONS
            and type(progress) in (int, float) and type(progress) is not bool
            and 0.0 <= float(progress) <= 1.0,
            "landing-item-state")
    if value["owned"]:
        require(action in ("play", "resume", "details")
                and state in ("none", "available")
                and (action == "resume") == (float(progress) > 0.0),
                "landing-item-action")
    else:
        require(float(progress) == 0.0, "landing-item-action")
        if state == "none":
            require(action in ("request", "details"), "landing-item-action")
        else:
            require(action in ("details", "none"), "landing-item-action")
    return HeroItem(identity, media_type, title, year, overview, poster,
                    backdrop, explanation, value["owned"], value["archived"],
                    state, action, float(progress))


def parse_feed(raw, domain, now=None):
    require(domain in DOMAINS and isinstance(raw, bytes)
            and 0 < len(raw) <= MAX_BYTES, "landing-feed-input")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("landing-feed-json") from exc
    require(type(value) is dict and set(value) == {"schema", "generated_at", "items"}
            and value["schema"] == 1 and type(value["items"]) is list
            and len(value["items"]) <= MAX_ITEMS, "landing-feed-schema")
    generated = _utc(value["generated_at"])
    current = now or datetime.now(timezone.utc)
    require(isinstance(current, datetime) and current.tzinfo is not None,
            "landing-feed-now")
    age = (current.astimezone(timezone.utc) - generated).total_seconds()
    require(-60 <= age <= MAX_AGE_SECONDS, "landing-feed-stale")
    items = tuple(hero_item(item, domain) for item in value["items"])
    identities = [item.identity for item in items]
    require(len(identities) == len(set(identities)), "landing-feed-duplicate")
    return Feed(generated, domain, items)


class HeroState:
    """Deterministic focus/rotation state; no timers or GUI I/O."""

    def __init__(self, feed, now, interval=12.0):
        require(isinstance(feed, Feed) and type(now) in (int, float)
                and type(now) is not bool and type(interval) in (int, float)
                and type(interval) is not bool and 5.0 <= interval <= 60.0,
                "landing-hero-init")
        self.feed = feed
        self.index = 0
        self.focused = None
        self.changed_at = float(now)
        self.interval = float(interval)

    @property
    def visible(self):
        if self.focused is not None:
            return self.focused
        return self.feed.items[self.index] if self.feed.items else None

    def focus(self, item, now):
        require(isinstance(item, HeroItem) and type(now) in (int, float)
                and type(now) is not bool, "landing-hero-focus")
        self.focused = item
        self.changed_at = float(now)
        return self.visible
    def clear_focus(self, now):
        require(type(now) in (int, float) and type(now) is not bool,
                "landing-hero-focus")
        self.focused = None
        self.changed_at = float(now)
        return self.visible

    def tick(self, now):
        require(type(now) in (int, float) and type(now) is not bool
                and float(now) >= self.changed_at, "landing-hero-time")
        if self.focused is not None or len(self.feed.items) < 2:
            return self.visible
        elapsed = float(now) - self.changed_at
        if elapsed >= self.interval:
            steps = int(elapsed // self.interval)
            self.index = (self.index + steps) % len(self.feed.items)
            self.changed_at += steps * self.interval
        return self.visible
