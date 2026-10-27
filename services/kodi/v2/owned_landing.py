"""Pure contract for owned Music and Books landing rails and idle heroes.

Presentation code may only call a row "recent" when its source supplied a real,
timezone-aware added timestamp. Recommendation candidates likewise need an
explicit bounded reason and score from a local-library signal producer. This
module never turns acquisition suggestions into playable library content.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re


DOMAINS = {
    'music': frozenset(('album',)),
    'books': frozenset(('ebook', 'audiobook', 'podcast')),
}
AUTHORITIES = {
    'album': frozenset(('kodi', 'jellyfin')),
    'ebook': frozenset(('calibre',)),
    'audiobook': frozenset(('audiobookshelf',)),
    'podcast': frozenset(('audiobookshelf',)),
}
ACTIONS = {
    'album': 'play',
    'ebook': 'read',
    'audiobook': 'play',
    'podcast': 'play',
}
IDENTITY = re.compile(r'[a-z][a-z0-9_-]{1,31}:[A-Za-z0-9._/-]{1,160}')
MAX_ROWS = 20000


def require(value, code):
    if not value:
        raise ValueError(code)


def _text(value, maximum, code, empty=False):
    require(isinstance(value, str) and len(value) <= maximum
            and (empty or bool(value.strip())), code)
    return value.strip()


def _timestamp(value):
    if value in (None, ''):
        return None
    require(isinstance(value, str) and len(value) <= 40,
            'owned-landing-added-at')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('owned-landing-added-at') from error
    require(parsed.tzinfo is not None, 'owned-landing-added-at')
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class OwnedItem:
    identity: str
    media_type: str
    title: str
    detail: str
    synopsis: str
    artwork: str
    backdrop: str
    added_at: object
    recommendation_score: object
    recommendation_reason: str
    primary_action: str


def owned_item(value, domain):
    require(domain in DOMAINS and type(value) is dict,
            'owned-landing-schema')
    media_type = value.get('media_type')
    identity = value.get('identity')
    require(media_type in DOMAINS[domain]
            and isinstance(identity, str) and IDENTITY.fullmatch(identity)
            and identity.split(':', 1)[0] in AUTHORITIES[media_type],
            'owned-landing-identity')
    score = value.get('recommendation_score')
    if score is not None:
        require(type(score) in (int, float) and type(score) is not bool
                and math.isfinite(float(score)) and 0 <= float(score) <= 100,
                'owned-landing-score')
        score = float(score)
    reason = _text(value.get('recommendation_reason', ''), 240,
                   'owned-landing-reason', empty=True)
    require((score is None and reason == '') or
            (score is not None and reason != ''), 'owned-landing-reason')
    return OwnedItem(
        identity=identity,
        media_type=media_type,
        title=_text(value.get('title'), 200, 'owned-landing-text'),
        detail=_text(value.get('detail', ''), 300, 'owned-landing-text', empty=True),
        synopsis=_text(value.get('synopsis', ''), 3000, 'owned-landing-text', empty=True),
        artwork=_text(value.get('artwork', ''), 1000, 'owned-landing-text', empty=True),
        backdrop=_text(value.get('backdrop', ''), 1000, 'owned-landing-text', empty=True),
        added_at=_timestamp(value.get('added_at')),
        recommendation_score=score,
        recommendation_reason=reason,
        primary_action=ACTIONS[media_type],
    )


def normalize(rows, domain):
    require(isinstance(rows, (list, tuple)) and len(rows) <= MAX_ROWS,
            'owned-landing-rows')
    items = tuple(owned_item(row, domain) for row in rows)
    identities = [item.identity for item in items]
    require(len(identities) == len(set(identities)),
            'owned-landing-duplicate')
    return items


def recently_added(items, limit=12):
    require(isinstance(items, tuple) and type(limit) is int and 1 <= limit <= 50,
            'owned-landing-recent')
    dated = [item for item in items if item.added_at is not None]
    dated.sort(key=lambda item: (item.added_at, item.title.casefold(), item.identity),
               reverse=True)
    return tuple(dated[:limit])


def recommendations(items, recent=(), limit=12):
    require(isinstance(items, tuple) and isinstance(recent, tuple)
            and type(limit) is int and 1 <= limit <= 50,
            'owned-landing-recommendations')
    excluded = {item.identity for item in recent}
    candidates = [item for item in items
                  if item.identity not in excluded
                  and item.recommendation_score is not None
                  and item.recommendation_reason]
    candidates.sort(
        key=lambda item: (item.recommendation_score,
                          item.added_at or datetime.min.replace(tzinfo=timezone.utc),
                          item.title.casefold(), item.identity),
        reverse=True)
    return tuple(candidates[:limit])


class OwnedHeroState:
    """Rotate only while no real content tile owns presentation authority."""

    def __init__(self, candidates, now, interval=12.0):
        require(isinstance(candidates, tuple)
                and all(isinstance(item, OwnedItem) for item in candidates)
                and type(now) in (int, float) and type(now) is not bool
                and type(interval) in (int, float) and type(interval) is not bool
                and 5 <= interval <= 60, 'owned-hero-init')
        self.candidates = candidates
        self.index = 0
        self.focused = None
        self.changed_at = float(now)
        self.interval = float(interval)

    @property
    def visible(self):
        if self.focused is not None:
            return self.focused
        return self.candidates[self.index] if self.candidates else None

    def focus(self, item, now):
        require(isinstance(item, OwnedItem)
                and type(now) in (int, float) and type(now) is not bool,
                'owned-hero-focus')
        self.focused = item
        self.changed_at = float(now)
        return self.visible

    def clear_focus(self, now):
        require(type(now) in (int, float) and type(now) is not bool,
                'owned-hero-focus')
        self.focused = None
        self.changed_at = float(now)
        return self.visible

    def tick(self, now):
        require(type(now) in (int, float) and type(now) is not bool
                and float(now) >= self.changed_at, 'owned-hero-time')
        if self.focused is not None or len(self.candidates) < 2:
            return self.visible
        elapsed = float(now) - self.changed_at
        if elapsed >= self.interval:
            steps = int(elapsed // self.interval)
            self.index = (self.index + steps) % len(self.candidates)
            self.changed_at += steps * self.interval
        return self.visible
