"""One bounded sound-only production trial. Run inside Kodi; never controls media."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import wave

import xbmc

BASE = Path('/storage/.aster-staging/aster-soft-puff-20261024')
LIVE = Path('/storage/.kodi/addons/resource.uisounds.asterhome/resources')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-soft-puff-20261024')
EXPECTED = {
    'back.wav': '1afe1ce5b910832b41af976a78298f7253a56810581ef614b84a987dacf449d8',
    'nav-down.wav': 'cc517c2401a0889befd031e6d21608b448805f3272d454e8f7d94ff1bc93a224',
    'nav-left.wav': '1e0ef44a936bf304907e83a88347318924444ed111e64db82c7e732aa3476329',
    'nav-right.wav': '4f916f4049a0d849eaca39f6315206b9c858c24d208bdb29f966e8ebe5176741',
    'nav-up.wav': '79750a0533a86c828eb9d284e911b2bef4295270bea3fdc9a49f59a51059ae75',
    'notify.wav': '8fa5141a4bc70478a969e927539b560fda930976821a0d7a4c140d4b665352b6',
    'select.wav': '5b9c7b4348ca1df78c7e86b4b3484b68777f2ee28ea7bec0d268da58de0dfa69',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def rpc(method, params=None):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(
        jsonrpc='2.0', id=1, method=method, params=params or {}))))
    require('error' not in reply, 'RPC failed: ' + method)
    return reply['result']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settings():
    return {s['id']: s.get('value') for s in rpc('Settings.GetSettings')['settings']}


def idle():
    require(not rpc('Player.GetActivePlayers'), 'Playback active; no changes made')


def replace(source, destination):
    temporary = destination.with_suffix('.wav.aster-tmp')
    shutil.copyfile(source, temporary)
    os.replace(str(temporary), str(destination))


def main():
    require(os.uname().nodename == 'AsterTVProd', 'Production host mismatch')
    before = settings()
    theme = before.get('lookandfeel.soundskin')
    report = dict(theme=theme, idle=not rpc('Player.GetActivePlayers'))
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        require(theme == 'resource.uisounds.asterhome', 'Unexpected sound theme')
        idle()
        evidence = json.loads((CHECKPOINT / 'verified.json').read_text())
        for name, digest in EXPECTED.items():
            require(sha(CHECKPOINT / name) == digest, 'Checkpoint drift')
            require(sha(LIVE / name) == evidence['assets'][name], 'Installed sound drift')
        for name in EXPECTED:
            replace(CHECKPOINT / name, LIVE / name)
        require(rpc('Settings.SetSettingValue', dict(setting='lookandfeel.soundskin', value='')) is True,
                'Could not unload UI sounds')
        require(rpc('Settings.SetSettingValue', dict(setting='lookandfeel.soundskin', value=theme)) is True,
                'Could not reload UI sounds')
        require(settings() == before, 'Rollback settings mismatch')
        require(all(sha(LIVE / name) == digest for name, digest in EXPECTED.items()),
                'Rollback file verification failed')
        report.update(rolled_back=True, settings_unchanged=True)
        return report
    if len(sys.argv) < 2 or sys.argv[1] != 'deploy':
        return report
    require(theme == 'resource.uisounds.asterhome', 'Unexpected sound theme')
    idle()
    require(not CHECKPOINT.exists(), 'Checkpoint already exists; do not repeat blindly')
    for name, digest in EXPECTED.items():
        require(sha(LIVE / name) == digest, 'Original sound drift: ' + name)
        with wave.open(str(BASE / 'resources' / name), 'rb') as source:
            require(source.getparams()[:3] == (2, 3, 48000), 'Wrong audio format')
            require(source.getnframes() < 24000, 'Sound too long')
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    for name in EXPECTED:
        shutil.copyfile(LIVE / name, CHECKPOINT / name)
        require(sha(CHECKPOINT / name) == EXPECTED[name], 'Checkpoint verify failed')
    # Retain source-local setting digests only, not potentially secret settings.
    settings_digest = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    mapping_digest = sha(LIVE / 'sounds.xml')
    idle()
    try:
        for name in EXPECTED:
            replace(BASE / 'resources' / name, LIVE / name)
        # Changing away and back asks Kodi to reload its cached WAV resources.
        require(rpc('Settings.SetSettingValue', dict(setting='lookandfeel.soundskin', value='')) is True,
                'Could not unload UI sounds')
        require(rpc('Settings.SetSettingValue', dict(setting='lookandfeel.soundskin', value=theme)) is True,
                'Could not reload UI sounds')
        require(settings() == before, 'Settings changed unexpectedly')
        require(sha(LIVE / 'sounds.xml') == mapping_digest, 'Sound mapping changed')
        for name in EXPECTED:
            require(sha(LIVE / name) == sha(BASE / 'resources' / name), 'Install verify failed')
    except Exception:
        for name in EXPECTED:
            replace(CHECKPOINT / name, LIVE / name)
        rpc('Settings.SetSettingValue', dict(setting='lookandfeel.soundskin', value=''))
        rpc('Settings.SetSettingValue', dict(setting='lookandfeel.soundskin', value=theme))
        raise
    report.update(installed=True, settings_unchanged=True, mapping_unchanged=True,
                  settings_digest=settings_digest,
                  assets={name: sha(LIVE / name) for name in EXPECTED},
                  checkpoint=str(CHECKPOINT), restart_required=False)
    (CHECKPOINT / 'verified.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    try:
        result = main()
    except Exception as error:
        result = dict(ok=False, error=str(error))
    else:
        result['ok'] = True
    (BASE / ('result-%s.json' % time.time_ns())).write_text(json.dumps(result, indent=2))
