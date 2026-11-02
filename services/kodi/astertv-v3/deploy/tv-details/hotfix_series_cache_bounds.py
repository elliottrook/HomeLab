#!/usr/bin/env python3
"""Reuse cached Seerr stills immediately and bound episode-list navigation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time

ROOT = Path('/storage/.kodi/addons')
HERE = Path(__file__).resolve().parent
SERIES = ROOT / 'script.asterruntime/aster-series-preview24'
DEFAULT = SERIES / 'default.py'
CACHE = SERIES / 'resources/lib/series_seerr_client.py'
EXTENSION = SERIES / 'v3_series_extension.py'
MANIFEST = SERIES / 'manifest.json'
WRAPPER = ROOT / 'skin.asterhome/tools/aster_v2_series.py'
FAMILY = ROOT / 'script.asterruntime/family-manifest.json'
EXPECTED = {
    DEFAULT: 'c690aee5cc0291a37112df752405d7db1a1c0199c6b8953ecd1de82e1145cbba',
    CACHE: 'd9e3f691f1997b69e2f5bb219b55d7ab6b8991995f0d84bf82363140e9dea9ae',
    EXTENSION: '98c128cbd2d68016b7b2d0981fb1df1fd1fd97a06395d4611975854e0e3d12a9',
    MANIFEST: '8e53c2cc8c1fdb16bc55111893a2986bb9d863e458e998cb48c356b05e6505a6',
    WRAPPER: '27c6b67e7c470924059f23fa8f8de461dc28ac799dcbd0cfc59077fe90fac0e5',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def active_players() -> None:
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + '\n').encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get('result') != []:
        raise RuntimeError('active player; repair refused')


def atomic(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-series-bounds-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def candidates(originals):
    default = originals[DEFAULT].decode()
    initial = """                loaded[number]=replace(detail,episodes=tuple(
                    replace(row,still='') for row in detail.episodes))"""
    switch = """        self.queue_catalogue_art(number,detail,local_numbers)
        detail=replace(detail,episodes=tuple(replace(row,still='') for row in detail.episodes))"""
    if default.count(initial) != 1 or default.count(switch) != 1:
        raise RuntimeError('series cache callsite drift')
    default = default.replace(initial, "                loaded[number]=cache.cached(detail,local_numbers)")
    default = default.replace(switch, """        self.queue_catalogue_art(number,detail,local_numbers)
        detail=self.catalogue_cache.cached(detail,local_numbers)""").encode()

    cache = originals[CACHE].decode()
    marker = '    def localize(self, detail, skip_numbers=()):\n'
    cached = """    def cached(self, detail, skip_numbers=()):
        \"\"\"Attach only already-rendered stills without network or image work.\"\"\"
        require(isinstance(detail, CatalogueSeasonDetail),
                'series-still-detail-invalid')
        skipped = frozenset(skip_numbers)
        require(all(type(number) is int and 1 <= number <= 9999
                    for number in skipped), 'series-still-skip-invalid')
        rows = []
        for row in detail.episodes:
            still = ''
            if row.still and row.number not in skipped:
                require(IMAGE.fullmatch(row.still), 'series-still-url-invalid')
                target = self.root / (hashlib.sha256(row.still.encode()).hexdigest() + '.png')
                if (target.is_file() and not target.is_symlink()
                        and 0 < target.stat().st_size <= 5 * 1024 * 1024):
                    still = str(target)
            rows.append(replace(row, still=still))
        return replace(detail, episodes=tuple(rows))

"""
    if cache.count(marker) != 1:
        raise RuntimeError('grayscale cache insertion drift')
    cache_limit = '0 < target.stat().st_size <= 5 * 1024 * 1024'
    if cache.count(cache_limit) != 1:
        raise RuntimeError('grayscale cache limit drift')
    cache = cache.replace(cache_limit,
                          '0 < target.stat().st_size <= 32 * 1024 * 1024')
    cached = cached.replace('0 < target.stat().st_size <= 5 * 1024 * 1024',
                            '0 < target.stat().st_size <= 32 * 1024 * 1024')
    cache = cache.replace(marker, cached + marker).encode()

    extension = (HERE / 'aster-series-preview24/v3_series_extension.py').read_bytes()
    for required in (b'def publish(self):', b'def on_action(self, action):',
                     b'clamped = max(0, min(position, count - 1))'):
        if required not in extension:
            raise RuntimeError('episode-bound candidate drift')

    manifest = json.loads(originals[MANIFEST])
    rows = {row['path']: row for row in manifest['files']}
    changes = {
        'default.py': default,
        'resources/lib/series_seerr_client.py': cache,
        'v3_series_extension.py': extension,
    }
    for name, data in changes.items():
        rows[name].update(bytes=len(data), sha256=sha(data))
    manifest['files'] = [rows[name] for name in sorted(rows)]
    manifest_data = encoded(manifest)

    wrapper = originals[WRAPPER].decode()
    if wrapper.count(EXPECTED[MANIFEST]) != 1:
        raise RuntimeError('wrapper pin drift')
    wrapper_data = wrapper.replace(EXPECTED[MANIFEST], sha(manifest_data)).encode()
    family = json.loads(originals[FAMILY])
    family['components']['aster-series-preview24'] = {
        'files': 9, 'manifest_sha256': sha(manifest_data)}
    family['skin']['tools/aster_v2_series.py'] = sha(wrapper_data)
    return {
        DEFAULT: default,
        CACHE: cache,
        EXTENSION: extension,
        MANIFEST: manifest_data,
        WRAPPER: wrapper_data,
        FAMILY: encoded(family),
    }


def main() -> None:
    hostname = socket.gethostname()
    if hostname not in ('AsterTV-Bedroom', 'AsterTV-Family'):
        raise RuntimeError('unexpected target: ' + hostname)
    if Path('/storage/.aster-recovery-required').exists():
        raise RuntimeError('recovery marker present')
    active_players()
    originals = {path: path.read_bytes() for path in set(EXPECTED) | {FAMILY}}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError('baseline drift: ' + str(path))
    changed = candidates(originals)
    stamp = time.strftime('%Y%m%d-%H%M%S', time.gmtime())
    checkpoint = Path('/storage/.aster-checkpoints') / (
        'astertv-v3-series-cache-bounds-' + hostname + '-' + stamp)
    checkpoint.mkdir(mode=0o700)
    for path in changed:
        saved = checkpoint / str(path.relative_to(ROOT)).replace('/', '__')
        saved.write_bytes(originals[path]); saved.chmod(0o600)

    try:
        subprocess.run(['systemctl', 'stop', 'kodi'], check=True, timeout=30)
    except Exception:
        subprocess.run(['systemctl', 'reset-failed', 'kodi'], check=False, timeout=10)
        subprocess.run(['systemctl', 'start', 'kodi'], check=False, timeout=30)
        raise
    try:
        for path, data in changed.items():
            atomic(path, data)
        for path, data in changed.items():
            if sha(path.read_bytes()) != sha(data):
                raise RuntimeError('post-write mismatch: ' + str(path))
    except Exception:
        for path, data in originals.items():
            atomic(path, data)
        Path('/storage/.aster-recovery-required').write_text(str(checkpoint) + '\n')
        raise
    finally:
        subprocess.run(['systemctl', 'start', 'kodi'], check=True, timeout=30)
    print(json.dumps({
        'installed': True,
        'host': hostname,
        'checkpoint': str(checkpoint),
        'manifest_sha256': sha(changed[MANIFEST]),
        'default_sha256': sha(changed[DEFAULT]),
        'cache_sha256': sha(changed[CACHE]),
        'extension_sha256': sha(changed[EXTENSION]),
    }, sort_keys=True))


if __name__ == '__main__':
    main()
