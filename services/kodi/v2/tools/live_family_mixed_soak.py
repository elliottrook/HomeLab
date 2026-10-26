"""HP-only private-fixture video/audio decoder and transport acceptance."""
import hashlib
import json
import os
from pathlib import Path
import re
import time

import xbmc
import xbmcgui


ROOT = Path(__file__).resolve().parent
VIDEO = Path('/storage/.aster-private/m7-fixtures/aster-m7-test.mov')
AUDIO = Path('/storage/.aster-staging/aster-readalong3/sample.wav')
HASHES = {
    VIDEO: '18d5578584490a6a7c2db8899040ae1af236aa4044c1e28c66243b231391568f',
    AUDIO: '99ae9edd408aa2fc6258d300c9d655cd4d81b88114f90fd609089a2541a5e039',
}


def require(value, code):
    if not value: raise RuntimeError(code)


def rpc(method, params=None):
    value = json.loads(xbmc.executeJSONRPC(json.dumps(dict(
        jsonrpc='2.0', id=1, method=method, params=params or {}))))
    require('error' not in value, 'mixed-soak-rpc')
    return value.get('result')


def players():
    return rpc('Player.GetActivePlayers') or []


def wait_player(kind, timeout=6):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        rows = players()
        if len(rows) == 1 and rows[0].get('type') == kind: return rows[0]['playerid']
        xbmc.sleep(100)
    raise RuntimeError('mixed-soak-'+kind+'-start')


def wait_idle(timeout=20):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        if not players(): return
        xbmc.sleep(100)
    raise RuntimeError('mixed-soak-stop-timeout')


def phase(player, speed):
    value = rpc('Player.GetProperties', dict(playerid=player, properties=['speed']))
    require(value.get('speed') == speed, 'mixed-soak-speed')


result = {}
try:
    require(os.uname().nodename == 'AsterTV', 'mixed-soak-hp-only')
    require(xbmcgui.getCurrentWindowId() == 10000 and not players(), 'mixed-soak-home-idle')
    for path, expected in HASHES.items():
        require(path.is_file() and not path.is_symlink()
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'mixed-soak-fixture-drift')

    rpc('Player.Open', dict(item=dict(file=str(VIDEO))))
    video = wait_player('video')
    xbmc.sleep(1200); phase(video, 1)
    xbmc.executebuiltin('Action(osd)'); xbmc.sleep(700)
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/m7-video-osd.png)')
    rpc('Player.PlayPause', dict(playerid=video, play=False)); phase(video, 0)
    rpc('Player.PlayPause', dict(playerid=video, play=True)); phase(video, 1)
    wait_idle(18)

    # Let asynchronous add-on stop callbacks drain before changing player type.
    xbmc.executebuiltin('ActivateWindow(Home)'); xbmc.sleep(2000)
    rpc('Player.Open', dict(item=dict(file=str(AUDIO))))
    audio = wait_player('audio')
    xbmc.sleep(800); phase(audio, 1)
    rpc('Player.PlayPause', dict(playerid=audio, play=False)); phase(audio, 0)
    rpc('Player.PlayPause', dict(playerid=audio, play=True)); phase(audio, 1)
    rpc('Player.Stop', dict(playerid=audio)); wait_idle(4)
    xbmc.executebuiltin('ActivateWindow(Home)'); xbmc.sleep(2000)
    require(xbmcgui.getCurrentWindowId() == 10000 and not players(), 'mixed-soak-home-return')
    result = dict(passed=True, private_video=True, private_audio=True,
        video_natural_end=True, pause_resume=True, explicit_audio_stop=True,
        no_library_identity=True, home=True, timestamp_ns=time.time_ns())
except (OSError, RuntimeError, ValueError, KeyError) as error:
    for row in players():
        try: rpc('Player.Stop', dict(playerid=row['playerid']))
        except Exception: pass
    xbmc.executebuiltin('ActivateWindow(Home)')
    code = str(error)
    result = dict(passed=False, code=code if re.fullmatch('[a-z0-9-]{1,100}', code)
                  else type(error).__name__)
(ROOT/('mixed-soak-'+str(time.time_ns())+'.json')).write_text(json.dumps(result, indent=2))
