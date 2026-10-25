"""HP-only completion/Stop/Home edges for the immutable joined Digest pilot."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui

ROOT = Path('/storage/.aster-staging/aster-digest-player8')
PIN = '9cb0ec4b207f1eb930b5a97494615914a0529fed2dcf271eacc709181f500887'
sys.path.insert(0, str(ROOT / 'resources/lib'))
import deploy_startup as guard


def require(value, code):
    if not value: raise RuntimeError(code)


def until(check, code, seconds=25):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise RuntimeError(code)


def prop(key): return xbmc.getInfoLabel('Window.Property(Digest.'+key+')')
def opened(): return bool(xbmc.getInfoLabel('Window(Home).Property(AsterDigest.PlayerWindow)'))
def click(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'), 'control-not-focused')
    result = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.ExecuteAction","params":{"action":"select"}}'))
    require('error' not in result, 'native-select')


result = dict(passed=False, checks_enforced=True, normal_news_changed=False, production_changed=False)
checkpoint = None
try:
    require(os.uname().nodename == 'AsterTV' and guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'hp-home-idle-only')
    raw = (ROOT/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PIN, 'stage-pin')
    for row in json.loads(raw)['files']:
        require(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256'], 'stage-drift')
    checkpoint = Path('/storage/.aster-checkpoints') / ('aster-digest-player-edges-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    before = guard.snapshot()
    (checkpoint/'before.json').write_text(json.dumps(before))
    original_focus = xbmcgui.Window(10000).getFocusId()
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+')')
    until(lambda:opened() and prop('Mode').startswith('HP PLAYER PILOT'), 'pilot-not-open')
    click(203)
    until(lambda:prop('Playing') == 'true', 'pilot-not-playing')
    # Test-only tail seek. Prove this exact private pilot file independently;
    # do not seek arbitrary user media or infer ownership from playerid alone.
    player = xbmc.Player()
    expected = player.getPlayingFile()
    target = Path(expected)
    require(target.parent.parent == Path('/storage/.aster-checkpoints')
        and target.parent.name.startswith('aster-digest-player-')
        and target.name.startswith('session-') and target.suffix == '.mp3', 'private-pilot-file-required')
    require(hashlib.sha256((target.parent/'manifest.json').read_bytes()).hexdigest() == PIN
        and prop('StartEvents') == '1', 'exact-pilot-session-required')
    duration = player.getTotalTime()
    require(2 < duration < 14400 and player.isPlayingAudio() and player.getPlayingFile() == expected, 'tail-seek-ownership')
    player.seekTime(duration-2)
    until(lambda:prop('Status') == 'Briefing complete' and prop('Playing') == 'false' and guard.idle(), 'natural-completion')
    require(prop('ActiveId') == '', 'completed-highlight-retained')
    result['natural_completion'] = True
    click(203)
    until(lambda:prop('Playing') == 'true', 'explicit-restart')
    click(204)
    until(lambda:prop('Status') == 'Stopped' and guard.idle(), 'explicit-stop')
    result['explicit_stop'] = True
    click(203)
    until(lambda:prop('Playing') == 'true', 'restart-before-home')
    reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply, 'native-home')
    until(lambda:not opened() and guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'home-exit-owned-stop')
    require(xbmcgui.Window(10000).getFocusId() == original_focus, 'home-exit-focus')
    require(guard.snapshot() == before, 'settings-navigation-preservation')
    result.update(passed=True, home_exit_stop=True, source_focus_restored=True,
        settings_navigation_unchanged=True, idle_empty=True)
except Exception as error:
    message = str(error)
    result['code'] = message if re.fullmatch('[a-z0-9-]{1,100}', message) else type(error).__name__
    result['status'] = prop('Status')[:120]
    result['error_code'] = prop('ErrorCode')[:100]
    result['callbacks'] = prop('Callbacks')[:100]
finally:
    if opened() and xbmcgui.getCurrentWindowId() != 10000:
        xbmc.executebuiltin('Action(Back)')
        until(lambda:not opened(), 'pilot-cleanup', 15)
    result['idle_empty'] = guard.idle()
    if checkpoint is not None: (checkpoint/'native.json').write_text(json.dumps(result, indent=2))
