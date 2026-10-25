"""HP-only new-addon installation and exact, non-destructive recovery in Kodi."""
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

import xbmc

BASE = Path('/storage/.aster-staging/aster-startup-20261025')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-startup-20261025')
LIVE = Path('/storage/.kodi/addons/service.aster.startup')
NAV = Path('/storage/.kodi/addons/resource.uisounds.asterhome/resources')
ADDON = 'service.aster.startup'


def require(value, code):
    if not value: raise RuntimeError(code)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Playlist.GetItems', 'Settings.GetSettings',
                       'Addons.GetAddonDetails', 'Addons.SetAddonEnabled'), 'rpc-boundary')
    if method == 'Addons.SetAddonEnabled':
        require(params['addonid'] == ADDON and type(params['enabled']) is bool, 'startup-only')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    require('error' not in reply, 'rpc-' + method)
    return reply['result']


def idle():
    return not rpc('Player.GetActivePlayers') and all(
        rpc('Playlist.GetItems', dict(playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0
        for i in (0, 1))


def snapshot():
    settings = rpc('Settings.GetSettings')['settings']
    # Record only a digest, never secret-bearing settings values.
    digest = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    return dict(settings_sha256=digest, navigation={p.name:sha(p) for p in NAV.iterdir() if p.suffix in ('.xml', '.wav')})


def exact_files(manifest, folder):
    require(all(sha(folder / name) == digest for name, digest in manifest['files'].items()), 'addon-file-drift')


def enabled():
    return rpc('Addons.GetAddonDetails', dict(addonid=ADDON, properties=['enabled']))['addon']['enabled']


def main(mode):
    require(os.uname().nodename == 'AsterTV', 'hp-only-no-production')
    require(mode in ('deploy', 'verify', 'rollback'), 'mode')
    require(idle(), 'idle-empty-required')
    manifest = json.loads((BASE / 'manifest.json').read_text())
    require(set(manifest['files']) == {'addon.xml', 'service.py', 'startup.wav'}, 'bounded-three-files')
    require(manifest['files']['startup.wav'] == 'cd873b68a8e3b4cbc4f848c2c581c25565fb0aed55bee5a24507b694928110c5', 'runtime-pin')
    exact_files(manifest, BASE / ADDON)
    before = snapshot()
    if mode == 'verify':
        exact_files(manifest, LIVE)
        require(enabled(), 'startup-disabled')
        require(before == json.loads((CHECKPOINT / 'before.json').read_text()), 'settings-or-navigation-drift')
        state = json.loads(Path('/storage/.kodi/userdata/addon_data/service.aster.startup/last-startup.json').read_text())
        require(state['outcome'] == 'gui-sound-requested', 'sound-not-requested')
        return dict(ok=True, mode=mode, settings_and_navigation_unchanged=True, startup=state, addon_enabled=True)
    if mode == 'rollback':
        exact_files(manifest, LIVE)
        require(not (CHECKPOINT / 'disabled-addon').exists(), 'recovery-already-used')
        rpc('Addons.SetAddonEnabled', dict(addonid=ADDON, enabled=False))
        require(not enabled(), 'disable-failed')
        shutil.move(str(LIVE), str(CHECKPOINT / 'disabled-addon'))
        xbmc.executebuiltin('UpdateLocalAddons')
        require(snapshot() == before, 'preservation-failed')
        return dict(ok=True, mode=mode, retained_disabled_addon=True)
    require(not LIVE.exists() and not CHECKPOINT.exists(), 'existing-state-refuse')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'before.json').write_text(json.dumps(before, indent=2))
    shutil.copyfile(BASE / 'manifest.json', CHECKPOINT / 'manifest.json')
    shutil.copyfile(__file__, CHECKPOINT / 'deploy_startup.py')
    require(idle(), 'playback-started-no-change')
    shutil.copytree(BASE / ADDON, LIVE)
    exact_files(manifest, LIVE)
    xbmc.executebuiltin('UpdateLocalAddons')
    for _ in range(20):
        xbmc.sleep(500)
        try:
            is_enabled = enabled()
            break
        except RuntimeError:
            continue
    else: raise RuntimeError('addon-not-discovered-use-checkpoint-recovery')
    if not is_enabled:
        rpc('Addons.SetAddonEnabled', dict(addonid=ADDON, enabled=True))
    require(enabled(), 'enable-failed')
    require(snapshot() == before and idle(), 'preservation-failed')
    return dict(ok=True, mode=mode, checkpoint=str(CHECKPOINT), addon_enabled=True,
                settings_and_navigation_unchanged=True, restart_required_for_lifecycle_test=True)


if __name__ == '__main__':
    try: result = main(sys.argv[1] if len(sys.argv) == 2 else 'verify')
    except Exception as error: result = dict(ok=False, code=str(error))
    (BASE / ('result-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
