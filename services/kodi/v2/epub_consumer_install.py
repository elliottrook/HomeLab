#!/usr/bin/env python3
"""Install or verify the pinned HP-only compiled EPUB consumer bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess


HOST = 'AsterTV'
STAGE = Path('/storage/.aster-staging/aster-epub-consumer1')
READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')
STATE = Path('/storage/.aster-state/aster-books-compiler-reader-v1')
OUTPUT = Path('/storage/aster-reader')
BOOKS = Path('/storage/.kodi/addons/skin.asterhome/tools/books_data.py')
UNIT_ROOT = Path('/storage/.config/system.d')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-epub-consumer1-20261026')
LEAVES = ('ready', 'generations')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def regular(path):
    metadata = path.lstat()
    return stat.S_ISREG(metadata.st_mode) and not path.is_symlink()


def atomic(path, raw, mode=0o600):
    temporary = path.with_name('.' + path.name + '.aster-new')
    with temporary.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(mode)
    os.replace(temporary, path)


def command(*parts):
    return subprocess.run(parts, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, timeout=30).stdout


def manifest():
    raw = (STAGE / 'manifest.json').read_bytes()
    data = json.loads(raw)
    if (data.get('schema') != 1 or data.get('kind') != 'aster-hp-compiled-epub-consumer-v1'
            or data.get('hp_only') is not True or data.get('active') is not True
            or not re.fullmatch('[a-f0-9]{64}', data.get('reader_pin', ''))):
        raise ValueError('consumer-manifest-boundary')
    expected = set(data.get('files', {}))
    actual = {str(path.relative_to(STAGE)) for path in STAGE.rglob('*')
              if path.is_file() and path.name != 'manifest.json'}
    if actual != expected:
        raise ValueError('consumer-manifest-members')
    for relative, wanted in data['files'].items():
        path = STAGE / relative
        if not regular(path) or sha(path) != wanted:
            raise ValueError('consumer-manifest-drift')
    if hashlib.sha256((STAGE / 'reader/bundle.json').read_bytes()).hexdigest() != data['reader_pin']:
        raise ValueError('consumer-reader-pin')
    return data


def mounted():
    rows = {}
    for line in Path('/proc/mounts').read_text().splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[1] in {str(OUTPUT / leaf) for leaf in LEAVES}:
            rows[fields[1]] = fields
    return rows


def verify(data):
    if os.uname().nodename != HOST:
        raise ValueError('consumer-host')
    if not regular(BOOKS) or sha(BOOKS) != data['installed_books_sha256']:
        raise ValueError('consumer-books-drift')
    activation = json.loads((STATE / 'activation.json').read_text())
    if activation != {'active': True, 'bundle': str(READER),
                       'bundle_sha256': data['reader_pin'], 'output': str(OUTPUT),
                       'schema': 1}:
        raise ValueError('consumer-activation-drift')
    if not READER.is_dir() or READER.is_symlink() or not (READER / 'data').is_symlink():
        raise ValueError('consumer-reader-layout')
    if (READER / 'data').resolve() != OUTPUT.resolve():
        raise ValueError('consumer-reader-data')
    if hashlib.sha256((READER / 'bundle.json').read_bytes()).hexdigest() != data['reader_pin']:
        raise ValueError('consumer-reader-installed-pin')
    rows = mounted()
    for leaf in LEAVES:
        target = str(OUTPUT / leaf)
        row = rows.get(target)
        if not row or row[0] != '192.168.20.40:/mnt/Media/AsterReader/' + leaf:
            raise ValueError('consumer-mount-' + leaf)
        if 'ro' not in row[3].split(','):
            raise ValueError('consumer-mount-writeable-' + leaf)
    return True


def rollback(data):
    if CHECKPOINT.is_dir() and (CHECKPOINT / 'books_data.py').is_file():
        atomic(BOOKS, (CHECKPOINT / 'books_data.py').read_bytes())
    activation = STATE / 'activation.json'
    if activation.exists() and regular(activation):
        activation.unlink()
    for leaf in LEAVES:
        escaped = 'storage-aster\\x2dreader-' + leaf
        subprocess.run(['systemctl', 'disable', '--now', escaped + '.automount'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        subprocess.run(['systemctl', 'stop', escaped + '.mount'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    for name, wanted in data.get('unit_sha256', {}).items():
        target = UNIT_ROOT / name
        if target.is_file() and not target.is_symlink() and sha(target) == wanted:
            target.unlink()
    subprocess.run(['systemctl', 'daemon-reload'], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=30)
    if READER.is_dir() and not READER.is_symlink():
        pin = READER / 'bundle.json'
        if pin.is_file() and hashlib.sha256(pin.read_bytes()).hexdigest() == data['reader_pin']:
            shutil.rmtree(READER)
    for leaf in LEAVES:
        target = OUTPUT / leaf
        if target.is_dir() and not target.is_symlink():
            try:
                target.rmdir()
            except OSError:
                pass
    try:
        OUTPUT.rmdir()
    except OSError:
        pass


def install(data):
    if os.uname().nodename != HOST:
        raise ValueError('consumer-host')
    if not regular(BOOKS) or sha(BOOKS) != data['predecessor_books_sha256']:
        raise ValueError('consumer-books-predecessor')
    for name in data['unit_sha256']:
        if (UNIT_ROOT / name).exists():
            raise ValueError('consumer-unit-predecessor')
    expected_state = {
        'schema': 1, 'reader_absent': True, 'state_absent': True,
        'output_absent': True, 'books_sha256': data['predecessor_books_sha256'],
    }
    fresh = not any(path.exists() for path in (CHECKPOINT, READER, STATE, OUTPUT))
    retry = False
    if not fresh:
        progress = STATE / 'progress'
        retry = (CHECKPOINT.is_dir() and not CHECKPOINT.is_symlink()
                 and regular(CHECKPOINT / 'books_data.py')
                 and sha(CHECKPOINT / 'books_data.py') == data['predecessor_books_sha256']
                 and json.loads((CHECKPOINT / 'state.json').read_text()) == expected_state
                 and not READER.exists() and not OUTPUT.exists()
                 and STATE.is_dir() and not STATE.is_symlink()
                 and progress.is_dir() and not progress.is_symlink()
                 and not any(progress.iterdir()) and not (STATE / 'activation.json').exists())
        if not retry:
            raise ValueError('consumer-predecessor-present')
    if fresh:
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        shutil.copyfile(BOOKS, CHECKPOINT / 'books_data.py')
        (CHECKPOINT / 'books_data.py').chmod(0o600)
        atomic(CHECKPOINT / 'state.json',
               (json.dumps(expected_state, sort_keys=True) + '\n').encode())
    try:
        shutil.copytree(STAGE / 'reader', READER)
        (READER / 'data').symlink_to(OUTPUT, target_is_directory=True)
        (STATE / 'progress').mkdir(mode=0o700, parents=True, exist_ok=retry)
        for leaf in LEAVES:
            (OUTPUT / leaf).mkdir(mode=0o700, parents=True)
        for name, wanted in data['unit_sha256'].items():
            source = STAGE / 'units' / name
            if sha(source) != wanted:
                raise ValueError('consumer-unit-package-drift')
            atomic(UNIT_ROOT / name, source.read_bytes())
        command('systemctl', 'daemon-reload')
        for leaf in LEAVES:
            escaped = 'storage-aster\\x2dreader-' + leaf
            command('systemctl', 'enable', '--now', escaped + '.automount')
            os.listdir(OUTPUT / leaf)
        rows = mounted()
        if set(rows) != {str(OUTPUT / leaf) for leaf in LEAVES}:
            raise ValueError('consumer-mount-incomplete')
        activation = {'schema': 1, 'active': True, 'bundle': str(READER),
                      'bundle_sha256': data['reader_pin'], 'output': str(OUTPUT)}
        atomic(STATE / 'activation.json',
               (json.dumps(activation, sort_keys=True) + '\n').encode())
        atomic(BOOKS, (STAGE / 'books_data.py').read_bytes())
        verify(data)
    except Exception:
        rollback(data)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('apply', 'verify', 'rollback'))
    arguments = parser.parse_args()
    if Path(__file__).resolve() != (STAGE / 'install.py').resolve():
        raise ValueError('consumer-stage')
    data = manifest()
    if arguments.mode == 'apply':
        install(data)
    elif arguments.mode == 'verify':
        if not CHECKPOINT.is_dir():
            raise ValueError('consumer-checkpoint')
        verify(data)
    else:
        rollback(data)
    print(json.dumps({'mode': arguments.mode, 'passed': True,
                      'reader_pin': data['reader_pin'], 'hp_only': True}, sort_keys=True))


if __name__ == '__main__':
    main()
