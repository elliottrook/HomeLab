"""Bounded, credential-free presentation contracts for optional Aster feeds."""

import json
import stat
import math
import re
from html.parser import HTMLParser
from datetime import datetime, timezone
from pathlib import Path


MAX_BYTES = 262144


class _PlainSynopsis(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        elif tag in ('p', 'br', 'div', 'li'):
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.hidden:
            self.hidden -= 1
        elif tag in ('p', 'div', 'li'):
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_synopsis(value):
    """Bounded display text; never pass HTML or Kodi markup into the skin."""
    if not isinstance(value, str) or len(value) > 20000:
        return ''
    parser = _PlainSynopsis()
    parser.feed(value)
    text = ' '.join(''.join(parser.parts).split())
    text = re.sub(r'https?://\S+', '', text)
    text = ' '.join(text.replace('[', '(').replace(']', ')').split())
    text = ''.join(char for char in text if ord(char) >= 32)
    return text[:997] + '…' if len(text) > 1000 else text


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
    return [(record['title'], record['detail'], None)
            for record in book_catalogue(payload)[:80]]


def book_catalogue(payload):
    """Bounded, sanitized records for the three read-only Books sections.

    The current one-shot producer supplies audiobooks and Calibre ebook titles.
    Subscribed podcast records can appear after Audiobookshelf has a Podcast
    library and the one-shot feed is refreshed.
    """
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
        if kind not in {('audiobookshelf', 'audiobook'), ('calibre', 'ebook'),
                        ('audiobookshelf', 'podcast')}:
            continue
        identity = record.get('authority_id')
        if not isinstance(identity, str) or not identity or len(identity) > 128:
            continue
        key = (kind, identity)
        if key in seen:
            continue
        title = _label(record.get('title'))
        seen.add(key)
        detail = {('audiobookshelf', 'audiobook'): 'Audiobook · Audiobookshelf',
                  ('calibre', 'ebook'): 'Ebook · Calibre',
                  ('audiobookshelf', 'podcast'): 'Podcast · Audiobookshelf'}[kind]
        rows.append({'title': title, 'detail': detail,
                     'kind': kind[1], 'id': identity,
                     'synopsis': plain_synopsis(record.get('description'))})
        if len(rows) == 1000:
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


def home_dashboard(payload):
    """Project the validated Home snapshot into fixed dashboard cards."""
    home_view(payload)
    snapshot = payload['snapshot']
    lights = snapshot.get('lights', []) if snapshot['schema_version'] == 2 else []
    temperatures = snapshot.get('temperatures', []) if snapshot['schema_version'] == 2 else []
    cameras = snapshot.get('cameras', []) if snapshot['schema_version'] == 2 else []
    timers = snapshot.get('timers', [])
    timer_label = _label(timers[0]) if timers else 'No active timer'
    values = {
        'LightLabel': _label(lights[0]['alias']).title() if lights else 'Lighting',
        'LightValue': lights[0]['state'].title() if lights else 'No reviewed lights',
        'TemperatureLabel': _label(temperatures[0]['alias']).title() if temperatures else 'Indoor comfort',
        'TemperatureValue': (f'{temperatures[0]["value"]:g}{temperatures[0]["unit"]}'
                             if temperatures else 'Unavailable'),
        'CameraLabel': _label(cameras[0]['alias']).title() if cameras else 'Cameras',
        'CameraStatus': cameras[0]['status'].title() if cameras else 'No reviewed camera',
        'TimerName': timer_label,
        'TimerLabel': 'Home Assistant timer' if timers else 'Not connected',
        'TimerDigital': '--:--',
        'TimerSecond': '0',
        'TimerActive': 'false',
    }
    return values
