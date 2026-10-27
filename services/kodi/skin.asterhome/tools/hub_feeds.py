"""Bounded, credential-free presentation contracts for optional Aster feeds."""

import json
import stat
import math
import re
from html.parser import HTMLParser
from datetime import datetime, timezone
from pathlib import Path


MAX_BYTES = 262144
WEATHER_CONDITIONS = {
    'clear-night', 'cloudy', 'exceptional', 'fog', 'hail', 'lightning',
    'lightning-rainy', 'partlycloudy', 'pouring', 'rainy', 'snowy',
    'snowy-rainy', 'sunny', 'windy', 'windy-variant',
}


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


def item_timestamp(value):
    """Canonicalize an optional source-owned item timestamp for presentation."""
    if value in (None, ''):
        return None
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError('Invalid item timestamp')
    normalized = re.sub(r' (?=[+-][0-9]{2}:[0-9]{2}$)', '', value.strip())
    normalized = normalized.replace(' ', 'T', 1)
    try:
        parsed = datetime.fromisoformat(normalized.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Invalid item timestamp') from error
    if parsed.tzinfo is None:
        raise ValueError('Item timestamp has no time zone')
    parsed = parsed.astimezone(timezone.utc)
    if parsed > datetime.now(timezone.utc).replace(microsecond=0):
        raise ValueError('Item timestamp is in the future')
    return parsed.isoformat()


def epoch_milliseconds(value):
    """Convert an optional bounded millisecond epoch to canonical UTC."""
    if value in (None, ''):
        return None
    if type(value) not in (int, float) or type(value) is bool:
        raise ValueError('Invalid item added time')
    seconds = float(value) / 1000.0
    lower = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()
    upper = datetime.now(timezone.utc).timestamp()
    if not lower <= seconds <= upper:
        raise ValueError('Invalid item added time')
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


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
                     'synopsis': plain_synopsis(record.get('description')),
                     'added_at': item_timestamp(record.get('added_at'))})
        if len(rows) == 1000:
            break
    return rows


def home_view(payload):
    """Render reviewed aliases and bounded read-only values, never controls."""
    _fresh(payload, 10 * 60)
    snapshot = payload.get('snapshot')
    if not isinstance(snapshot, dict) or snapshot.get('schema_version') not in (1, 2, 3):
        raise ValueError('Invalid Home Assistant snapshot')
    rows = []
    if snapshot['schema_version'] in (2, 3):
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
        if snapshot['schema_version'] == 3:
            weather = snapshot.get('weather', [])
            if not isinstance(weather, list) or len(weather) > 1:
                raise ValueError('Invalid weather values')
            for current in weather:
                if (not isinstance(current, dict)
                        or current.get('condition') not in WEATHER_CONDITIONS
                        or current.get('unit') not in ('°C', '°F')):
                    raise ValueError('Invalid weather state')
                temperature = current.get('temperature')
                if (isinstance(temperature, bool)
                        or not isinstance(temperature, (int, float))
                        or not math.isfinite(temperature)):
                    raise ValueError('Invalid weather temperature')
                minimum, maximum = (-50, 60) if current['unit'] == '°C' else (-58, 140)
                if not minimum <= temperature <= maximum:
                    raise ValueError('Weather temperature out of range')
                humidity = current.get('humidity')
                if (humidity is not None and
                        (isinstance(humidity, bool)
                         or not isinstance(humidity, (int, float))
                         or not math.isfinite(humidity) or not 0 <= humidity <= 100)):
                    raise ValueError('Invalid weather humidity')
                condition = current['condition'].replace('-', ' ').replace('partlycloudy',
                                                                            'partly cloudy')
                detail = f'{condition.title()} · {temperature:g}{current["unit"]}'
                if humidity is not None:
                    detail += f' · {humidity:g}% humidity'
                rows.append((_label(current.get('alias')), detail, None))
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
    lights = snapshot.get('lights', []) if snapshot['schema_version'] in (2, 3) else []
    temperatures = snapshot.get('temperatures', []) if snapshot['schema_version'] in (2, 3) else []
    cameras = snapshot.get('cameras', []) if snapshot['schema_version'] in (2, 3) else []
    weather = snapshot.get('weather', []) if snapshot['schema_version'] == 3 else []
    timers = snapshot.get('timers', [])
    timer_label = _label(timers[0]) if timers else 'No active timer'
    if weather:
        condition = weather[0]['condition'].replace('-', ' ').replace('partlycloudy',
                                                                       'partly cloudy').title()
        weather_detail = f'{weather[0]["temperature"]:g}{weather[0]["unit"]}'
        if weather[0].get('humidity') is not None:
            weather_detail += f' · {weather[0]["humidity"]:g}% humidity'
    else:
        condition, weather_detail = 'Unavailable', 'No reviewed weather'
    values = {
        'LightLabel': _label(lights[0]['alias']).title() if lights else 'Lighting',
        'LightValue': lights[0]['state'].title() if lights else 'No reviewed lights',
        'TemperatureLabel': _label(temperatures[0]['alias']).title() if temperatures else 'Indoor comfort',
        'TemperatureValue': (f'{temperatures[0]["value"]:g}{temperatures[0]["unit"]}'
                             if temperatures else 'Unavailable'),
        'CameraLabel': _label(cameras[0]['alias']).title() if cameras else 'Cameras',
        'CameraStatus': cameras[0]['status'].title() if cameras else 'No reviewed camera',
        'WeatherLabel': _label(weather[0]['alias']).title() if weather else 'Weather',
        'WeatherValue': condition,
        'WeatherDetail': weather_detail,
        'TimerName': timer_label,
        'TimerLabel': 'Home Assistant timer' if timers else 'Not connected',
        'TimerDigital': '--:--',
        'TimerSecond': '0',
        'TimerActive': 'false',
    }
    return values
