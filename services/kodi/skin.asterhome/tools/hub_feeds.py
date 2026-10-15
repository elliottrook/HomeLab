"""Bounded, credential-free presentation contracts for optional Aster feeds."""

import json
import stat
import math
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
    """Render reviewed aliases and bounded read-only values, never controls."""
    _fresh(payload, 10 * 60)
    snapshot = payload.get('snapshot')
    if not isinstance(snapshot, dict) or snapshot.get('schema_version') not in (1, 2):
        raise ValueError('Invalid Home Assistant snapshot')
    rows = []
    if snapshot['schema_version'] == 2:
        lights = snapshot.get('lights', [])
        temperatures = snapshot.get('temperatures', [])
        cameras = snapshot.get('cameras', [])
        if (not isinstance(lights, list) or not isinstance(temperatures, list)
                or not isinstance(cameras, list) or len(lights) > 40
                or len(temperatures) > 40 or len(cameras) > 4):
            raise ValueError('Invalid Home Assistant values')
        for light in lights:
            if not isinstance(light, dict) or light.get('state') not in ('on', 'off'):
                raise ValueError('Invalid light state')
            rows.append((_label(light.get('alias')), 'Light · ' + light['state'].title(), None))
        for sensor in temperatures:
            if not isinstance(sensor, dict) or sensor.get('unit') not in ('°C', '°F'):
                raise ValueError('Invalid temperature unit')
            value = sensor.get('value')
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Invalid temperature value')
            minimum, maximum = (-50, 60) if sensor['unit'] == '°C' else (-58, 140)
            if not minimum <= value <= maximum:
                raise ValueError('Temperature out of range')
            rows.append((_label(sensor.get('alias')), f'Temperature · {value:g}{sensor["unit"]}', None))
        for camera in cameras:
            if (not isinstance(camera, dict) or camera.get('status') not in ('online', 'offline')):
                raise ValueError('Invalid camera status')
            rows.append((_label(camera.get('alias')),
                         f'Camera · {camera["status"].title()} · Live view in Frigate app', None))
    groups = (('rooms', 'Room'), ('timers', 'Active or paused timer'),
              ('media_providers', 'Available media device'))
    if snapshot['schema_version'] == 1:
        groups += (('entities', 'Available light or switch'),)
    for key, noun in groups:
        aliases = snapshot.get(key)
        if not isinstance(aliases, list) or len(aliases) > 40:
            raise ValueError('Invalid Home Assistant aliases')
        rows.extend((_label(alias), noun, None) for alias in aliases)
    return rows[:80]
