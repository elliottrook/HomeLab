#!/usr/bin/env python3
"""Transactional HP installer for the explicit voice-search pilot."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT
PAYLOAD = BUNDLE / 'payload'
MANIFEST = BUNDLE / 'manifest.json'
ADDON = Path('/storage/.kodi/addons/script.astervoice.v2lab')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-voice-search1')
REMOTE_NAME = 'HAOBO Technology USB Composite Device Keyboard'
INSTALL_TARGETS = {
    Path('/storage/.config/hwdb.d/99-aster-g20-voice.hwdb'),
    Path('/storage/.config/pulse-daemon.conf.d/50-aster-g20-mic.conf'),
    Path('/storage/.config/pulse-daemon.conf.d/aster-g20-mic.pa'),
    Path('/storage/.config/system.d/eventlircd.service.d/aster-retry.conf'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=30, check=True)


def target(row):
    return Path(row['target'])


def rpc(method, params=None):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        request['params'] = params
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + '\n').encode())
        reply = json.loads(client.recv(8192))
    require('error' not in reply and 'result' in reply, 'kodi-rpc-' + method)
    return reply['result']


def remote_event_path():
    matches = []
    for block in Path('/proc/bus/input/devices').read_text().split('\n\n'):
        if 'N: Name="' + REMOTE_NAME + '"' not in block:
            continue
        handlers = []
        for line in block.splitlines():
            if line.startswith('H: Handlers='):
                handlers = [value for value in line.split('=', 1)[1].split()
                            if value.startswith('event') and value[5:].isdigit()]
        if len(handlers) == 1:
            matches.append('/dev/input/' + handlers[0])
    require(len(matches) == 1, 'voice-event-device')
    value = run('/usr/bin/udevadm', 'info', '--query=path', '--name=' + matches[0])
    path = value.stdout.strip()
    require(path.startswith('/devices/') and '..' not in path, 'voice-event-path')
    return matches[0], '/sys' + path


def refresh_hwdb(sysfs_path):
    run('/usr/bin/systemd-hwdb', 'update')
    run('/usr/bin/udevadm', 'trigger', '--action=add', sysfs_path)


def main():
    require(os.uname().nodename == 'AsterTV', 'hp-only')
    manifest = json.loads(MANIFEST.read_text())
    require(manifest.get('kind') == 'hp-voice-search-pilot.v1', 'manifest-kind')
    require(manifest.get('helper', {}).get('path') == Path(__file__).name
            and digest(Path(__file__)) == manifest['helper']['sha256'],
            'deploy-helper-drift')
    require(not ADDON.exists() and not CHECKPOINT.exists(), 'existing-voice-state')
    installs = manifest.get('installs', [])
    require(len(installs) == 4
            and {target(row) for row in installs} == INSTALL_TARGETS,
            'voice-install-set')
    for row in installs:
        path = target(row)
        source = PAYLOAD / row['path']
        require(not path.exists()
                and source.is_file() and digest(source) == row['sha256'],
                'voice-install-policy')
    event_device, sysfs_path = remote_event_path()
    # Playback must be idle. The query is read-only and does not alter queues.
    require(rpc('Player.GetActivePlayers') == [], 'active-playback')
    replacements = manifest['replacements']
    for row in replacements:
        path = target(row)
        require(path.is_file() and not path.is_symlink()
                and digest(path) == row['before_sha256'], 'predecessor-drift')
        source = PAYLOAD / row['path']
        require(source.is_file() and digest(source) == row['sha256'], 'payload-drift')
    for row in manifest['addon']['files']:
        source = PAYLOAD / manifest['addon']['id'] / row['path']
        require(source.is_file() and digest(source) == row['sha256'], 'addon-payload-drift')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for row in replacements:
        destination = CHECKPOINT / row['path']
        shutil.copy2(target(row), destination)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    try:
        run('/usr/bin/systemctl', 'stop', 'kodi')
        shutil.copytree(PAYLOAD / manifest['addon']['id'], ADDON)
        for row in installs:
            target(row).parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            shutil.copy2(PAYLOAD / row['path'], target(row))
            target(row).chmod(0o644 if target(row).suffix == '.hwdb' else 0o600)
        refresh_hwdb(sysfs_path)
        run('/usr/bin/systemctl', 'daemon-reload')
        for row in replacements:
            path = target(row); temporary = path.with_name(path.name + '.aster-voice-new')
            shutil.copy2(PAYLOAD / row['path'], temporary)
            os.replace(temporary, path)
        run('/usr/bin/systemctl', 'restart', 'pulseaudio')
        run('/usr/bin/systemctl', 'start', 'kodi')
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active':
                break
            time.sleep(.25)
        require(run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active',
                'kodi-not-active')
        end = time.monotonic() + 30
        while True:
            try:
                details = rpc('Addons.GetAddonDetails', {
                    'addonid': manifest['addon']['id'],
                    'properties': ['enabled'],
                })
                break
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
                if time.monotonic() >= end:
                    raise RuntimeError('voice-addon-not-discovered')
                time.sleep(.25)
        if not details['addon']['enabled']:
            rpc('Addons.SetAddonEnabled', {
                'addonid': manifest['addon']['id'], 'enabled': True,
            })
        details = rpc('Addons.GetAddonDetails', {
            'addonid': manifest['addon']['id'], 'properties': ['enabled'],
        })
        require(details['addon']['enabled'], 'voice-addon-disabled')
        properties = run('/usr/bin/udevadm', 'info', '--query=property',
                         '--name=' + event_device).stdout.splitlines()
        require('KEYBOARD_KEY_c00cf=search' in properties, 'voice-hwdb-inactive')
        sources = run('/usr/bin/pactl', 'list', 'short', 'sources').stdout.splitlines()
        require(sum('alsa_input.usb-HAOBO_Technology_USB_Composite_Device_'
                    '8545124150354735-00.mono-fallback' in row for row in sources) == 1,
                'voice-pulse-source-inactive')
        require(run('/usr/bin/systemctl', 'show', 'eventlircd', '-p', 'Restart',
                    '--value').stdout.strip() == 'on-failure', 'eventlircd-retry-inactive')
        require(all(digest(target(row)) == row['sha256'] for row in replacements),
                'installed-replacement-drift')
        require(all(digest(ADDON / row['path']) == row['sha256']
                    for row in manifest['addon']['files']), 'installed-addon-drift')
    except Exception:
        try:
            run('/usr/bin/systemctl', 'stop', 'kodi')
            if ADDON.exists(): shutil.rmtree(ADDON)
            for row in installs:
                path = target(row)
                if path.exists(): path.unlink()
            refresh_hwdb(sysfs_path)
            run('/usr/bin/systemctl', 'daemon-reload')
            run('/usr/bin/systemctl', 'restart', 'pulseaudio')
            for row in replacements:
                shutil.copy2(CHECKPOINT / row['path'], target(row))
            run('/usr/bin/systemctl', 'start', 'kodi')
        finally:
            raise
    print(json.dumps({'installed': True, 'addon_files': len(manifest['addon']['files']),
                      'replacements': len(replacements),
                      'checkpoint': str(CHECKPOINT)}, sort_keys=True))


if __name__ == '__main__':
    main()
