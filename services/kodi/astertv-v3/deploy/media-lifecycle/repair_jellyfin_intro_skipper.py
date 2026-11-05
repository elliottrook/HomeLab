#!/usr/bin/env python3
"""Install the Jellyfin-12.1-compatible Intro Skipper build transactionally."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.request
import zipfile


ZIP = Path('/tmp/intro-skipper-v12.0.5.0.zip')
ZIP_MD5 = 'd3fc1c17efa61ed85e86228f3c2c940f'
ROOT = Path('/mnt/Media/appdata/jellyfin/data/plugins')
OLD = ROOT / 'Intro Skipper_12.0.6.0'
NEW = ROOT / 'Intro Skipper_12.0.5.0'
CHECKPOINTS = Path('/mnt/Media/appdata/jellyfin/.aster-checkpoints')
DATASET = 'Media/appdata/jellyfin'


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, text=True, capture_output=capture, timeout=90)


def digest(path: Path, algorithm: str = 'sha256') -> str:
    value = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def health() -> bool:
    try:
        with urllib.request.urlopen('http://127.0.0.1:8096/health', timeout=3) as response:
            return response.status == 200 and response.read(64) == b'Healthy'
    except OSError:
        return False


def wait_health() -> None:
    for _ in range(40):
        if health():
            return
        time.sleep(1)
    raise RuntimeError('jellyfin-health-timeout')


def main() -> None:
    if socket.gethostname() != 'truenas' or os.getuid() != 0:
        raise RuntimeError('truenas-root-required')
    if digest(ZIP, 'md5') != ZIP_MD5:
        raise RuntimeError('plugin-archive-checksum-mismatch')
    if NEW.exists() or not OLD.is_dir() or OLD.is_symlink():
        raise RuntimeError('unexpected-plugin-directory-state')
    meta_path = OLD / 'meta.json'
    meta = json.loads(meta_path.read_text())
    expected = {
        'name': 'Intro Skipper', 'version': '12.0.6.0',
        # This copy was installed under the earlier 12.0 catalogue metadata;
        # Jellyfin 12.1 has already classified it NotSupported. The current
        # upstream catalogue now correctly advertises 12.0.6 for ABI 12.2.
        'targetAbi': '12.0.0.0', 'status': 'NotSupported',
    }
    if any(meta.get(key) != value for key, value in expected.items()):
        raise RuntimeError('installed-plugin-baseline-drift')
    owner = OLD.stat()

    stamp = time.strftime('%Y%m%d-%H%M%S', time.gmtime())
    checkpoint = CHECKPOINTS / ('intro-skipper-12.1-' + stamp)
    checkpoint.mkdir(mode=0o700, parents=True)
    snapshot = DATASET + '@intro-skipper-12-1-' + stamp
    run('zfs', 'snapshot', snapshot)

    run('docker', 'stop', '-t', '30', 'jellyfin')
    restored = False
    try:
        shutil.move(str(OLD), str(checkpoint / OLD.name))
        NEW.mkdir(mode=0o755)
        with zipfile.ZipFile(ZIP) as archive:
            names = archive.namelist()
            if names != ['IntroSkipper.dll']:
                raise RuntimeError('unexpected-plugin-archive-members')
            dll = archive.read(names[0])
        (NEW / 'IntroSkipper.dll').write_bytes(dll)
        if (checkpoint / OLD.name / 'logo.png').is_file():
            shutil.copy2(checkpoint / OLD.name / 'logo.png', NEW / 'logo.png')
        meta.update({
            'version': '12.0.5.0', 'targetAbi': '12.1.0.0',
            'timestamp': '2026-10-09T19:44:43.0000000Z',
            'status': 'Active', 'autoUpdate': False,
            'imagePath': str(NEW / 'logo.png'),
        })
        (NEW / 'meta.json').write_text(json.dumps(meta, indent=2) + '\n')
        # Preserve the container's mapped service ownership. Jellyfin updates
        # plugin status in meta.json during startup and fails closed if it is
        # merely readable rather than service-writable.
        for path in (NEW, *NEW.iterdir()):
            os.chown(path, owner.st_uid, owner.st_gid)
        run('docker', 'start', 'jellyfin')
        wait_health()
        logs = run('docker', 'logs', '--since', '3m', 'jellyfin', capture=True)
        combined = logs.stdout + logs.stderr
        if ('Loaded assembly IntroSkipper' not in combined
                or 'Loaded plugin: Intro Skipper 12.0.5.0' not in combined
                or 'Skipping disabled plugin 12.0.5.0 of Intro Skipper' in combined):
            raise RuntimeError('plugin-load-verification-failed')
    except Exception:
        subprocess.run(['docker', 'stop', '-t', '30', 'jellyfin'], check=False, timeout=45)
        if NEW.exists():
            failed = checkpoint / (NEW.name + '.failed')
            shutil.move(str(NEW), str(failed))
        saved = checkpoint / OLD.name
        if saved.exists() and not OLD.exists():
            shutil.move(str(saved), str(OLD))
            restored = True
        subprocess.run(['docker', 'start', 'jellyfin'], check=False, timeout=45)
        raise

    report = {
        'installed': True, 'version': '12.0.5.0', 'targetAbi': '12.1.0.0',
        'autoUpdate': False, 'checkpoint': str(checkpoint), 'snapshot': snapshot,
        'dll_sha256': digest(NEW / 'IntroSkipper.dll'), 'rollback_used': restored,
    }
    (checkpoint / 'result.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
