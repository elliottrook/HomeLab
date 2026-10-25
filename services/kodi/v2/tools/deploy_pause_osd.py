"""HP-only create-new player UI add-on; paired checkpoint recovery."""
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deploy_startup as engine
import xbmc

engine.ADDON = 'service.aster.playerui'
BASE = Path('/storage/.aster-staging/aster-pause-osd1')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-pause-osd1')
LIVE = Path('/storage/.kodi/addons') / engine.ADDON
require = engine.require


def main(mode):
    require(os.uname().nodename == 'AsterTV', 'hp-only-no-production')
    require(mode in ('deploy', 'verify', 'rollback'), 'mode')
    require(engine.idle(), 'idle-empty-required')
    manifest = json.loads((BASE / 'manifest.json').read_text())
    require(manifest.get('kind') == 'hp-pause-osd.v1' and manifest.get('addon') == engine.ADDON
            and set(manifest['files']) == {'addon.xml', 'service.py'}, 'bounded-pause-service')
    engine.exact_files(manifest, BASE / engine.ADDON)
    before = engine.snapshot()
    if mode == 'verify':
        engine.exact_files(manifest, LIVE)
        require(engine.enabled(), 'service-disabled')
        require(before == json.loads((CHECKPOINT / 'before.json').read_text()), 'settings-navigation-drift')
        return dict(ok=True, verified_files=2, enabled=True, settings_navigation_unchanged=True)
    if mode == 'rollback':
        engine.exact_files(manifest, LIVE)
        require(not (CHECKPOINT / 'disabled-addon').exists(), 'already-restored')
        engine.rpc('Addons.SetAddonEnabled', dict(addonid=engine.ADDON, enabled=False))
        require(not engine.enabled(), 'disable-failed')
        xbmc.sleep(500)
        shutil.move(str(LIVE), str(CHECKPOINT / 'disabled-addon'))
        xbmc.executebuiltin('UpdateLocalAddons')
        require(engine.snapshot() == before, 'preservation-failed')
        return dict(ok=True, rolled_back=True, files_retained=True)
    require(not LIVE.exists() and not CHECKPOINT.exists(), 'existing-state-refuse')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'before.json').write_text(json.dumps(before, indent=2))
    for name in ('manifest.json', 'deploy_pause_osd.py', 'deploy_startup.py'):
        shutil.copyfile(BASE / name, CHECKPOINT / name)
    require(engine.idle(), 'playback-started-no-change')
    shutil.copytree(BASE / engine.ADDON, LIVE)
    engine.exact_files(manifest, LIVE)
    xbmc.executebuiltin('UpdateLocalAddons')
    for _ in range(20):
        xbmc.sleep(500)
        try:
            active = engine.enabled()
            break
        except RuntimeError:
            continue
    else: raise RuntimeError('addon-not-discovered')
    if not active: engine.rpc('Addons.SetAddonEnabled', dict(addonid=engine.ADDON, enabled=True))
    require(engine.enabled() and engine.idle() and engine.snapshot() == before, 'preservation-failed')
    return dict(ok=True, installed_files=2, enabled=True, settings_navigation_unchanged=True, restart_required=False)


if __name__ == '__main__':
    try: result = main(sys.argv[1] if len(sys.argv) == 2 else 'verify')
    except Exception as error: result = dict(ok=False, code=str(error))
    (BASE / ('result-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
