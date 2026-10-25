"""HP-only icon-resource adoption; never change Home or Search integrity guards."""
import json
import os
from pathlib import Path
import shutil
import sys
import time
import xbmc
sys.path.insert(0, str(Path(__file__).parent))
import deploy_startup as guard

BASE = Path('/storage/.aster-staging/aster-youtube-pill2')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-youtube-pill2')
SKIN = Path('/storage/.kodi/addons/skin.asterhome')
ICON = Path('/storage/.kodi/addons/plugin.video.youtube/resources/media/icon.png')
MANIFEST = 'bbfe993cb4e09d78ba24c1043d2dab43e56070148399ed0403697258dd9e4603'
require = guard.require


def target(name): return ICON if name.endswith('512.png') else SKIN / 'media' / name


def main(mode):
    require(os.uname().nodename == 'AsterTV', 'hp-only-no-production')
    require(mode in ('deploy', 'verify', 'rollback') and guard.idle(), 'mode-and-idle-empty-required')
    require(guard.sha(BASE / 'manifest.json') == MANIFEST, 'pinned-manifest')
    manifest = json.loads((BASE / 'manifest.json').read_text())
    require(set(manifest['files']) == {'33-aster-youtube-128.png', '33-aster-youtube-512.png'}, 'exact-two-images')
    for name, digest in manifest['files'].items(): require(guard.sha(BASE / name) == digest, 'stage-drift')
    require(guard.sha(SKIN / '1080i/Home.xml') == manifest['home_sha256'], 'home-must-be-unchanged')
    before = guard.snapshot()
    if mode in ('verify', 'rollback'):
        for name, digest in manifest['files'].items(): require(guard.sha(target(name)) == digest, 'installed-drift')
        require(guard.sha(CHECKPOINT / 'youtube-icon-before.png') == manifest['original_icon_sha256'], 'checkpoint-drift')
        require(before == json.loads((CHECKPOINT / 'settings-navigation.json').read_text()), 'settings-navigation-drift')
        if mode == 'verify':
            return dict(passed=True, mode=mode, manifest_sha256=MANIFEST, home_unchanged=True, settings_navigation_unchanged=True)
        target('33-aster-youtube-128.png').rename(CHECKPOINT / 'disabled-33-aster-youtube-128.png')
        shutil.copyfile(ICON, CHECKPOINT / 'disabled-33-aster-youtube-512.png')
        temporary = ICON.with_suffix('.aster-tmp')
        shutil.copyfile(CHECKPOINT / 'youtube-icon-before.png', temporary)
        os.replace(temporary, ICON)
        (CHECKPOINT / 'verified.json').rename(CHECKPOINT / 'rolled-back.json')
        xbmc.executebuiltin('ReloadSkin')
        return dict(passed=True, mode=mode, original_icon_restored=True, files_retained=True)
    require(not CHECKPOINT.exists() and not target('33-aster-youtube-128.png').exists(), 'existing-state-refuse')
    require(not ICON.is_symlink() and guard.sha(ICON) == manifest['original_icon_sha256'], 'original-icon-drift')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copyfile(ICON, CHECKPOINT / 'youtube-icon-before.png')
    (CHECKPOINT / 'settings-navigation.json').write_text(json.dumps(before, indent=2))
    for name in ('manifest.json', 'deploy_youtube_branding.py', 'deploy_startup.py'):
        shutil.copyfile(BASE / name, CHECKPOINT / name)
    require(guard.sha(CHECKPOINT / 'youtube-icon-before.png') == manifest['original_icon_sha256'] and guard.idle(), 'checkpoint-and-idle')
    for name in manifest['files']:
        temporary = target(name).with_suffix('.aster-tmp')
        shutil.copyfile(BASE / name, temporary)
        os.replace(temporary, target(name))
    for name, digest in manifest['files'].items(): require(guard.sha(target(name)) == digest, 'installed-drift')
    require(guard.sha(SKIN / '1080i/Home.xml') == manifest['home_sha256'] and guard.snapshot() == before, 'preservation-failed')
    result = dict(passed=True, mode=mode, manifest_sha256=MANIFEST, home_unchanged=True, settings_navigation_unchanged=True)
    (CHECKPOINT / 'verified.json').write_text(json.dumps(result, indent=2))
    xbmc.executebuiltin('ReloadSkin')
    return result


if __name__ == '__main__':
    try: result = main(sys.argv[1] if len(sys.argv) == 2 else 'verify')
    except Exception as error: result = dict(passed=False, code=str(error))
    (BASE / ('result-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
