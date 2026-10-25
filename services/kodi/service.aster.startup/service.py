"""One GUI sound per Kodi process; no playback, queue, volume or server writes."""
import hashlib
import json
import os
import time
from pathlib import Path

import xbmc
import xbmcvfs

MASTER_SHA = 'f41cc896c664e234986330799bc3b75c460ab6eb87c3883df338b0353a06b7e2'
RUNTIME_SHA = 'cd873b68a8e3b4cbc4f848c2c581c25565fb0aed55bee5a24507b694928110c5'


def rpc(method, params=None):
    if method not in ('Player.GetActivePlayers', 'Playlist.GetItems', 'Settings.GetSettingValue'):
        raise ValueError('read-only-rpc')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(
        jsonrpc='2.0', id=1, method=method, params=params or {}))))
    if 'error' in reply:
        raise RuntimeError('native-read-failed')
    return reply['result']


def idle():
    return not rpc('Player.GetActivePlayers') and all(
        rpc('Playlist.GetItems', dict(playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0
        for i in (0, 1))


def session_key():
    start = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
    return str(os.getpid()) + '-' + start


def run():
    # A process-local exclusive file also fences concurrent/re-enabled invocations.
    # /proc starttime prevents PID reuse from suppressing a later Kodi session.
    key = session_key()
    lock = Path(xbmcvfs.translatePath('special://temp/')) / ('aster-startup-' + key + '.lock')
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return 'already-attempted'
    os.close(fd)
    profile = Path(xbmcvfs.translatePath('special://profile/addon_data/service.aster.startup'))
    profile.mkdir(mode=0o700, parents=True, exist_ok=True)
    report = dict(process=key, attempted_at=time.time(), outcome='not-ready')
    monitor = xbmc.Monitor()
    try:
        sound = Path(__file__).resolve().parent / 'startup.wav'
        if hashlib.sha256(sound.read_bytes()).hexdigest() != RUNTIME_SHA:
            raise ValueError('runtime-asset-drift')
        for _ in range(120):
            if monitor.waitForAbort(.5):
                report['outcome'] = 'shutdown'
                break
            if not idle():
                report['outcome'] = 'playback-or-queue-skipped'
                break
            if rpc('Settings.GetSettingValue', dict(setting='lookandfeel.skin'))['value'] != 'skin.asterhome':
                continue
            if xbmc.getCondVisibility('Window.IsActive(home)') and not xbmc.getCondVisibility('System.HasModalDialog'):
                # Let HDMI/audio settle, but do not delay the interface.
                if monitor.waitForAbort(2):
                    report['outcome'] = 'shutdown'
                    break
                if not idle() or not xbmc.getCondVisibility('Window.IsActive(home)') or xbmc.getCondVisibility('System.HasModalDialog'):
                    report['outcome'] = 'readiness-changed-skipped'
                    break
                xbmc.playSFX(str(sound), useCached=False)
                report['outcome'] = 'gui-sound-requested'
                break
    except Exception as error:
        report['outcome'] = 'failed-' + type(error).__name__
    path = profile / 'last-startup.json'
    path.write_text(json.dumps(report, indent=2))
    path.chmod(0o600)
    xbmc.log('Aster startup: ' + report['outcome'], xbmc.LOGINFO)
    return report['outcome']


if __name__ == '__main__':
    run()
