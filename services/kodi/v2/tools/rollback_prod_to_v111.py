#!/usr/bin/env python3
"""One-shot, guarded AsterTVProd UI rollback; preserve all Kodi user data."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

STORAGE = Path('/storage')
ADDONS = STORAGE / '.kodi/addons'
KEYMAP = STORAGE / '.kodi/userdata/keymaps/g20s-pro-plus.xml'
ARCHIVE = STORAGE / 'backup/astertv-v2-preproduction-20261027/profile-config-v1.1.1.tar.gz'
ARCHIVE_SHA = 'd077c42505824856be88d9b65c78fcbb5f0d7bffc7203fe64164465da7d9aa5d'
CHECKPOINT = STORAGE / '.aster-checkpoints/astertv-v2-pull-20261028'
V1 = ('plugin.audio.asterbooks', 'plugin.video.asterhome',
      'resource.uisounds.asterhome', 'skin.asterhome')


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def rpc(method):
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as sock:
        sock.settimeout(3)
        sock.sendall((json.dumps(dict(jsonrpc='2.0', id=1, method=method)) + '\r\n').encode())
        response = b''
        while True:
            response += sock.recv(4096)
            try:
                result = json.loads(response)
                break
            except json.JSONDecodeError:
                continue
    require('error' not in result, 'kodi-rpc-error')
    return result['result']


def service(action):
    subprocess.run(['systemctl', action, 'kodi'], check=True)


def active():
    return subprocess.run(['systemctl', 'is-active', '--quiet', 'kodi']).returncode == 0


def write_state(state):
    (CHECKPOINT / 'state.json').write_text(json.dumps({'state': state}) + '\n')


def main():
    require(os.uname().nodename == 'AsterTVProd', 'wrong-host')
    require(not CHECKPOINT.exists(), 'checkpoint-already-exists')
    require(active(), 'kodi-not-active')
    require(rpc('Player.GetActivePlayers') == [], 'playback-active')
    require(ET.parse(ADDONS / 'skin.asterhome/addon.xml').getroot().attrib['version'] == '2.0.0', 'not-v2')
    require(ARCHIVE.is_file() and sha256(ARCHIVE) == ARCHIVE_SHA, 'v1-archive-drift')

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    os.chmod(CHECKPOINT, 0o700)
    staged = CHECKPOINT / 'staged'
    parked = CHECKPOINT / 'parked-addons'
    staged.mkdir()
    parked.mkdir()
    prefixes = {'.kodi/addons/' + name + '/' for name in V1}
    key_name = '.kodi/userdata/keymaps/g20s-pro-plus.xml'
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        members = [m for m in archive if any(m.name.startswith(p) for p in prefixes) or m.name == key_name]
        require(all(m.isfile() or m.isdir() for m in members), 'unsafe-member-type')
        require(all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members), 'unsafe-member-path')
        for member in members:
            target = staged / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open('wb') as output:
                    shutil.copyfileobj(source, output)
    require(all((staged / '.kodi/addons' / name / 'addon.xml').is_file() for name in V1), 'incomplete-v1-addons')
    require(ET.parse(staged / '.kodi/addons/skin.asterhome/addon.xml').getroot().attrib['version'] == '1.1.1', 'wrong-v1-version')
    require((staged / key_name).is_file(), 'missing-v1-keymap')
    write_state('prepared')

    # Kodi is stopped before any live file is replaced. No database, addon_data,
    # watch state, YouTube account, display or audio setting is restored.
    require(rpc('Player.GetActivePlayers') == [], 'playback-started')
    service('stop')
    require(not active(), 'kodi-stop-failed')
    moved = []
    installed = []
    key_parked = CHECKPOINT / 'g20s-pro-plus.xml.before'
    try:
        for path in sorted(ADDONS.iterdir()):
            if 'aster' in path.name and path.is_dir() and not path.is_symlink():
                path.rename(parked / path.name)
                moved.append(path.name)
        for name in V1:
            (staged / '.kodi/addons' / name).rename(ADDONS / name)
            installed.append(name)
        KEYMAP.rename(key_parked)
        (staged / key_name).rename(KEYMAP)
        write_state('installed')
        service('start')
        require(active(), 'kodi-start-failed')
        require(ET.parse(ADDONS / 'skin.asterhome/addon.xml').getroot().attrib['version'] == '1.1.1', 'v1-verify-failed')
        write_state('v1.1.1-active')
    except Exception:
        if active():
            service('stop')
        if key_parked.exists():
            if KEYMAP.exists():
                KEYMAP.unlink()
            key_parked.rename(KEYMAP)
        for name in installed:
            shutil.rmtree(ADDONS / name)
        for name in moved:
            (parked / name).rename(ADDONS / name)
        write_state('rolled-back-to-v2-after-error')
        service('start')
        raise
    print(json.dumps({'release': '1.1.1', 'checkpoint': str(CHECKPOINT),
                      'parked_v2_addons': len(moved), 'userdata_preserved': True}))


if __name__ == '__main__':
    main()
