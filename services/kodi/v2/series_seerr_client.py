"""Restricted Seerr episode transport, private grayscale cache and write fence."""
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

from series_catalogue import (IMAGE, CatalogueSeasonDetail, parse_catalogue,
                              parse_season, season_result)


class CatalogueUnavailable(RuntimeError):
    pass


def require(value, code):
    if not value:
        raise CatalogueUnavailable(code)


def _atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    with open(temporary, 'wb') as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(raw); output.flush(); os.fsync(output.fileno())
    os.replace(temporary, path)


class CatalogueClient:
    def __init__(self, base, token_path, opener=urllib.request.urlopen):
        require(base == 'http://192.168.20.40:8788',
                'series-catalogue-broker-invalid')
        self.base = base; self.token_path = Path(token_path); self.opener = opener

    def _call(self, method, path, body=None):
        require(path.startswith('/v1/') and '?' not in path.split('?', 1)[0],
                'series-catalogue-path-invalid')
        token = self.token_path.read_text().strip()
        require(32 <= len(token) <= 512, 'series-catalogue-token-invalid')
        encoded = None if body is None else json.dumps(
            body, separators=(',', ':')).encode()
        headers = {'Authorization': 'Bearer ' + token,
                   'Accept': 'application/json'}
        if encoded is not None:
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.base + path, data=encoded,
                                         method=method, headers=headers)
        try:
            with self.opener(request, timeout=15) as response:
                raw = response.read(1024 * 1024 + 1)
                require(response.status == 200 and len(raw) <= 1024 * 1024,
                        'series-catalogue-response-invalid')
                value = json.loads(raw)
                require(type(value) is dict, 'series-catalogue-response-invalid')
                return value
        except CatalogueUnavailable:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, ValueError) as error:
            raise CatalogueUnavailable('series-catalogue-unavailable') from error

    def resolve(self, tvdb_id, title):
        require(type(tvdb_id) is int and 0 < tvdb_id <= 9_999_999_999
                and isinstance(title, str) and 0 < len(title) <= 200,
                'series-catalogue-resolve-invalid')
        path = '/v1/tv/resolve?' + urllib.parse.urlencode(
            {'tvdb': tvdb_id, 'title': title}, quote_via=urllib.parse.quote)
        return parse_catalogue(self._call('GET', path))

    def season(self, catalogue, number):
        require(type(number) is int and 0 <= number <= 999,
                'series-catalogue-season-invalid')
        value = self._call('GET', '/v1/tv/' + str(catalogue.media_id) +
                           '/season/' + str(number))
        return parse_season(value, catalogue, number)

    def request_season(self, payload):
        return self._call('POST', '/v1/season-request', payload)


class SeasonRequestWriter:
    def __init__(self, root, send):
        self.root = Path(root); self.send = send

    def submit(self, payload, catalogue):
        require(type(payload) is dict and payload.get('candidate_id') == catalogue.candidate_id
                and type(payload.get('season')) is int,
                'series-season-write-invalid')
        number = payload['season']
        identity = catalogue.candidate_id.replace(':', '-') + '-season-' + str(number)
        require(re.fullmatch(r'seerr-tv-[1-9][0-9]{0,9}-season-[1-9][0-9]{0,2}', identity),
                'series-season-write-identity')
        path = self.root / (identity + '.json')
        digest = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if path.exists():
            try:
                prior = json.loads(path.read_text())
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise CatalogueUnavailable('series-season-journal-invalid') from error
            require(prior.get('payload_sha256') == digest,
                    'series-season-journal-identity-reused')
            if prior.get('status') == 'committed':
                return season_result(prior.get('result'), catalogue, number)
            raise CatalogueUnavailable('series-season-write-recovery-required')
        record = {'schema': 1, 'candidate_id': catalogue.candidate_id,
                  'season': number, 'payload_sha256': digest,
                  'status': 'prepared', 'result': None}
        _atomic_json(path, record)
        try:
            accepted = season_result(self.send(dict(payload)), catalogue, number)
        except Exception as error:
            record['status'] = 'uncertain'; _atomic_json(path, record)
            raise CatalogueUnavailable('series-season-write-outcome-uncertain') from error
        record.update(status='committed', result=accepted)
        _atomic_json(path, record)
        return dict(accepted)


class GrayscaleCache:
    def __init__(self, root, opener=urllib.request.urlopen):
        self.root = Path(root); self.opener = opener

    def fetch(self, url):
        require(isinstance(url, str) and IMAGE.fullmatch(url),
                'series-still-url-invalid')
        self.root.mkdir(parents=True, exist_ok=True)
        require(not self.root.is_symlink(), 'series-still-cache-linked')
        target = self.root / (hashlib.sha256(url.encode()).hexdigest() + '.png')
        require(not target.is_symlink(), 'series-still-cache-linked')
        if target.is_file() and not target.is_symlink() and 0 < target.stat().st_size <= 5 * 1024 * 1024:
            return str(target)
        request = urllib.request.Request(url, headers={'Accept': 'image/jpeg,image/png'})
        try:
            with self.opener(request, timeout=15) as response:
                raw = response.read(5 * 1024 * 1024 + 1)
                require(response.status == 200 and response.geturl() == url
                        and 0 < len(raw) <= 5 * 1024 * 1024,
                        'series-still-response-invalid')
            from PIL import Image, ImageOps
            with Image.open(BytesIO(raw)) as image:
                image.load()
                require(0 < image.width <= 4096 and 0 < image.height <= 4096
                        and image.width * image.height <= 16_000_000,
                        'series-still-dimensions-invalid')
                rendered = ImageOps.grayscale(image).convert('RGB')
                temporary = target.with_name(target.name + '.tmp')
                rendered.save(temporary, format='PNG', optimize=True)
                os.chmod(temporary, 0o600); os.replace(temporary, target)
            return str(target)
        except CatalogueUnavailable:
            raise
        except Exception as error:
            raise CatalogueUnavailable('series-still-unavailable') from error

    def localize(self, detail, skip_numbers=()):
        require(isinstance(detail, CatalogueSeasonDetail),
                'series-still-detail-invalid')
        skipped = frozenset(skip_numbers)
        require(all(type(number) is int and 1 <= number <= 9999
                    for number in skipped), 'series-still-skip-invalid')
        wanted = tuple(dict.fromkeys(row.still for row in detail.episodes
            if row.still and row.number not in skipped))
        def render(url):
            try:
                return self.fetch(url)
            except CatalogueUnavailable:
                return ''
        if wanted:
            with ThreadPoolExecutor(max_workers=min(4, len(wanted)),
                                    thread_name_prefix='aster-series-art') as pool:
                rendered = dict(zip(wanted, pool.map(render, wanted)))
        else:
            rendered = {}
        rows = []
        for row in detail.episodes:
            still = rendered.get(row.still, '')
            rows.append(replace(row, still=still))
        return replace(detail, episodes=tuple(rows))
