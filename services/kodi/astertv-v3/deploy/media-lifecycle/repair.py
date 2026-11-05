#!/usr/bin/env python3
"""Repair Family Continue Watching, Up Next and manual next-episode selection."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time


ADDONS = Path('/storage/.kodi/addons')
LIBRARY = ADDONS / 'plugin.video.asterhome/library.py'
NEXT = ADDONS / 'skin.asterhome/tools/next_episode.py'
SEARCH = ADDONS / 'script.asterruntime/aster-global-search-ui22'
PLAYER = SEARCH / 'resources/lib/movie_player.py'
MANIFEST = SEARCH / 'manifest.json'
FAMILY = ADDONS / 'script.asterruntime/family-manifest.json'
GUARD = Path('/storage/.aster-release/release_guard.py')
EXPECTED = {
    LIBRARY: '597cea83131a452a049a69cd2a98a9ed82af8f009018c9176819cbd08ec0aa5c',
    NEXT: '909a321aee7e6e68121e7149c26086c56faa314c303d4843510d11e05ed7e3ba',
    PLAYER: 'b5f02209429d066964d747084b5e5f07b9ada32b123be377113becfa1ae41d14',
    MANIFEST: '04c6f0936512ac764e8d63b4987469d0c6369ecba496d410014fd1938be7af5c',
    FAMILY: 'e3654e05d76a06dd680e92f935a1ea3283a37d2e4eb600e1df1aac866e8a8c8a',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def patch_library(source: str) -> str:
    old = """            if not isinstance(source, dict):
                continue
            resume = source.get('resume')
"""
    new = """            if not isinstance(source, dict):
                continue
            # Jellyfin can retain a stale bookmark after marking an item played.
            # A completed item is not Continue Watching, even when that stale
            # position remains in Kodi's local projection.
            playcount = source.get('playcount', 0)
            if type(playcount) is not int or playcount > 0:
                continue
            resume = source.get('resume')
"""
    if source.count(old) != 1:
        raise ValueError('continue-watching-baseline-drift')
    return source.replace(old, new)


def patch_next(source: str) -> str:
    old_filter = """    rows = sorted((row for row in episodes if row.get('season', 0) > 0
                   and row.get('episode', 0) > 0 and order(row) > order(current)), key=order)
"""
    new_filter = """    rows = sorted((row for row in episodes if row.get('season', 0) > 0
                   and row.get('episode', 0) > 0 and order(row) > order(current)
                   and type(row.get('playcount', 0)) is int
                   and row.get('playcount', 0) == 0), key=order)
"""
    old_properties = "properties=['season','episode','file','firstaired','showtitle'],"
    new_properties = "properties=['season','episode','file','firstaired','showtitle','playcount'],"
    if source.count(old_filter) != 1 or source.count(old_properties) != 1:
        raise ValueError('next-episode-baseline-drift')
    return source.replace(old_filter, new_filter).replace(old_properties, new_properties)


def candidates(originals: dict[Path, bytes]) -> dict[Path, bytes]:
    library = patch_library(originals[LIBRARY].decode()).encode()
    next_source = patch_next(originals[NEXT].decode()).encode()

    player = originals[PLAYER].decode()
    old_next = EXPECTED[NEXT]
    if player.count(old_next) != 1:
        raise ValueError('movie-player-next-pin-drift')
    player_data = player.replace(old_next, sha(next_source)).encode()

    manifest = json.loads(originals[MANIFEST])
    rows = [row for row in manifest['files']
            if row['path'] == 'resources/lib/movie_player.py']
    if len(rows) != 1 or rows[0]['sha256'] != EXPECTED[PLAYER]:
        raise ValueError('movie-player-manifest-drift')
    rows[0].update(bytes=len(player_data), sha256=sha(player_data))
    manifest_data = encoded(manifest)

    family = json.loads(originals[FAMILY])
    component = family['components']['aster-global-search-ui22']
    if component['manifest_sha256'] != EXPECTED[MANIFEST]:
        raise ValueError('family-search-pin-drift')
    component['manifest_sha256'] = sha(manifest_data)
    family_data = encoded(family)
    return {
        LIBRARY: library,
        NEXT: next_source,
        PLAYER: player_data,
        MANIFEST: manifest_data,
        FAMILY: family_data,
    }


def active_players() -> None:
    import socket as socket_module
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'}
    with socket_module.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall(json.dumps(request).encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get('result') != []:
        raise RuntimeError('active-player-repair-refused')


def atomic(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix='.media-lifecycle-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    if socket.gethostname() != 'AsterTV-Family':
        raise RuntimeError('family-target-required')
    if Path('/storage/.aster-recovery-required').exists():
        raise RuntimeError('recovery-marker-present')
    kodi_was_active = subprocess.run(
        ['systemctl', 'is-active', '--quiet', 'kodi'], check=False).returncode == 0
    if kodi_was_active:
        active_players()
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError('baseline-drift:' + str(path))
    changed = candidates(originals)
    stamp = time.strftime('%Y%m%d-%H%M%S', time.gmtime())
    checkpoint = Path('/storage/.aster-checkpoints') / (
        'astertv-media-lifecycle-AsterTV-Family-' + stamp)
    checkpoint.mkdir(mode=0o700)
    for path, data in originals.items():
        target = checkpoint / str(path.relative_to(ADDONS)).replace('/', '__')
        target.write_bytes(data); target.chmod(0o600)

    # LibreELEC may report a timeout after it has already killed and fully
    # stopped Kodi. Accept that exact stopped state, but never continue while
    # kodi.bin remains alive.
    if kodi_was_active:
        subprocess.run(['systemctl', 'stop', 'kodi'], check=False, timeout=40)
    process = subprocess.run(['pgrep', '-x', 'kodi.bin'], check=False,
                             capture_output=True, text=True)
    if process.returncode == 0:
        raise RuntimeError('kodi-process-remains-after-stop')
    subprocess.run(['systemctl', 'reset-failed', 'kodi'], check=False, timeout=10)
    try:
        for path, data in changed.items():
            atomic(path, data)
        for path, data in changed.items():
            if sha(path.read_bytes()) != sha(data):
                raise RuntimeError('post-write-mismatch:' + str(path))
        accepted = subprocess.run(
            [str(GUARD), 'snapshot', '--host', 'AsterTV-Family'], check=True,
            capture_output=True, text=True, timeout=60)
        verified = subprocess.run(
            [str(GUARD), 'verify', '--host', 'AsterTV-Family'], check=True,
            capture_output=True, text=True, timeout=60)
    except Exception:
        for path, data in originals.items():
            atomic(path, data)
        Path('/storage/.aster-recovery-required').write_text(str(checkpoint) + '\n')
        raise
    finally:
        subprocess.run(['systemctl', 'start', 'kodi'], check=True, timeout=30)
    print(json.dumps({
        'installed': True, 'checkpoint': str(checkpoint),
        'files': {str(path): sha(data) for path, data in changed.items()},
        'accepted': json.loads(accepted.stdout),
        'verified': json.loads(verified.stdout),
    }, sort_keys=True))


if __name__ == '__main__':
    main()
