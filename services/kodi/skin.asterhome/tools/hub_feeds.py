"""Bounded, credential-free presentation contracts for optional Aster feeds."""

import json
import stat
from datetime import datetime, timezone
from pathlib import Path


MAX_BYTES = 262144


def _fresh(payload, max_age_seconds):
    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('Unsupported feed schema')
    stamp = datetime.fromisoformat(payload['generated_at'])
    if stamp.tzinfo is None:
        raise ValueError('Feed has no time zone')
    age = (datetime.now(timezone.utc) - stamp).total_seconds()
    if age < -300 or age > max_age_seconds:
        raise ValueError('Feed is stale')


def _label(value):
    if not isinstance(value, str):
        raise ValueError('Invalid label')
    label = value.replace('[', '(').replace(']', ')').strip()
    if not label or len(label) > 160 or any(ord(char) < 32 for char in label):
        raise ValueError('Invalid label')
    return label


def read_feed(path):
    """Read only a regular, bounded local file; never follow a directory or URL."""
    source = Path(path)
    metadata = source.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_BYTES:
        raise ValueError('Feed unavailable or too large')
    with source.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Feed too large')
    return json.loads(raw)


def books_view(payload):
    """Display only approved fields from the unified-media library snapshot."""
    _fresh(payload, 24 * 3600)
    records = payload.get('items')
    if not isinstance(records, list):
        raise ValueError('Invalid library feed')
    rows = []
    seen = set()
    for record in records[:2000]:
        if not isinstance(record, dict):
            continue
        kind = (record.get('authority'), record.get('media_type'))
        if kind not in {('audiobookshelf', 'audiobook'), ('calibre', 'ebook')}:
            continue
        identity = record.get('authority_id')
        if not isinstance(identity, str) or not identity or len(identity) > 128:
            continue
        key = (kind, identity)
        if key in seen:
            continue
        title = _label(record.get('title'))
        seen.add(key)
        rows.append((title, 'Audiobook · Audiobookshelf' if kind[0] == 'audiobookshelf'
                     else 'Ebook · Calibre', None))
        if len(rows) == 80:
            break
    return rows


def home_view(payload):
    """Render the approved registry aliases as availability, never as device state."""
    _fresh(payload, 10 * 60)
    snapshot = payload.get('snapshot')
    if not isinstance(snapshot, dict) or snapshot.get('schema_version') != 1:
        raise ValueError('Invalid Home Assistant snapshot')
    rows = []
    for key, noun in (('rooms', 'Room'), ('entities', 'Available light or switch'),
                      ('timers', 'Active or paused timer'), ('media_providers', 'Available media device')):
        aliases = snapshot.get(key)
        if not isinstance(aliases, list) or len(aliases) > 40:
            raise ValueError('Invalid Home Assistant aliases')
        rows.extend((_label(alias), noun, None) for alias in aliases)
    return rows[:80]
