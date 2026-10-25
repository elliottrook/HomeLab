"""Offline published-edition timeline. No fetch, synthesis, playback or writes."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math


def seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 14400:
        raise ValueError('invalid-time')
    return float(value)


@dataclass(frozen=True)
class Chapter:
    identity: str
    title: str
    start: float
    end: float


@dataclass(frozen=True)
class Timeline:
    identity: str
    duration: float
    chapters: tuple

    def chapter_at(self, elapsed, observed_edition):
        if observed_edition != self.identity:
            raise ValueError('edition-changed')
        elapsed = seconds(elapsed)
        if elapsed >= self.duration:
            return None
        return next((i for i, row in enumerate(self.chapters) if row.start <= elapsed < row.end), None)

    def neighbor(self, index, direction):
        if type(index) is not int or not 0 <= index < len(self.chapters) or type(direction) is not int or direction not in (-1, 1):
            raise ValueError('invalid-navigation')
        target = index + direction
        return target if 0 <= target < len(self.chapters) else None

    def seek_proposal(self, index, observed_edition):
        if observed_edition != self.identity:
            raise ValueError('edition-changed')
        if type(index) is not int or not 0 <= index < len(self.chapters):
            raise ValueError('invalid-chapter')
        row = self.chapters[index]
        return dict(edition=self.identity, chapter=row.identity, start=row.start)


def build(payload, observed_duration, now):
    """Require a real media duration; never guess a last-story/outro boundary."""
    duration = seconds(observed_duration)
    if duration <= 0 or not isinstance(payload, dict) or not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('invalid-snapshot')
    stamp = payload.get('generated_at')
    if not isinstance(stamp, str) or len(stamp) > 64:
        raise ValueError('invalid-generation')
    generated = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if generated.tzinfo is None:
        raise ValueError('missing-timezone')
    age = (now.astimezone(timezone.utc) - generated).total_seconds()
    if not -300 <= age <= 36*3600:
        raise ValueError('stale-edition')
    run = payload.get('digest_run')
    if type(run) not in (int, str) or not str(run) or len(str(run)) > 128:
        raise ValueError('missing-source-run')
    published_duration = payload.get('duration_seconds')
    if published_duration is not None and abs(seconds(published_duration)-duration) > 2:
        raise ValueError('media-duration-mismatch')
    rows = payload.get('chapters')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 40:
        raise ValueError('invalid-chapter-count')
    if type(payload.get('story_count')) is not int or payload['story_count'] != len(rows):
        raise ValueError('incomplete-edition')
    cleaned = []
    previous = -1
    indices = set()
    for row in rows:
        if not isinstance(row, dict): raise ValueError('invalid-chapter')
        start = seconds(row.get('start'))
        index = row.get('index')
        title = row.get('title')
        if not previous < start < duration or type(index) is not int or not 0 <= index <= 1000 or index in indices:
            raise ValueError('invalid-chapter-order')
        if not isinstance(title, str) or not title.strip() or len(title) > 1000:
            raise ValueError('invalid-title')
        # Kodi formatting must not be executable through feed text.
        title = ' '.join(title.replace('[', '(').replace(']', ')').split())[:240]
        cleaned.append((index, title, start))
        indices.add(index)
        previous = start
    identity_data = json.dumps([str(run), stamp, duration, cleaned], ensure_ascii=True, separators=(',', ':'))
    identity = hashlib.sha256(identity_data.encode()).hexdigest()
    chapters = tuple(Chapter(identity + ':' + str(index), title, start,
        cleaned[i+1][2] if i+1 < len(cleaned) else duration)
        for i, (index, title, start) in enumerate(cleaned))
    return Timeline(identity, duration, chapters)
