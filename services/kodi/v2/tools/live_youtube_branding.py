"""HP icon/focus smoke; do not open YouTube, playback or an API setup flow."""
import json
import os
from pathlib import Path
import sys
import time
import xbmc
import xbmcgui

sys.path.insert(0, str(Path(__file__).parent))
import deploy_startup as guard


def until(check, code):
    end = time.monotonic() + 4
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(80)
    raise RuntimeError(code)


def focus(identity): return xbmc.getCondVisibility('Control.HasFocus(' + str(identity) + ')')
def press(action): xbmc.executebuiltin('Action(' + action + ')')


root = Path('/storage/.aster-checkpoints/aster-youtube-pill2')
result = dict(passed=False)
try:
    guard.require(os.uname().nodename == 'AsterTV' and guard.idle(), 'hp-idle-only')
    xbmc.executebuiltin('ActivateWindow(Home)')
    until(lambda:xbmcgui.getCurrentWindowId() == 10000, 'home-not-ready')
    xbmc.executebuiltin('Control.SetFocus(136)')
    until(lambda:focus(136), 'youtube-focus')
    xbmc.sleep(450)
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-youtube-pill2/youtube-focused.png)')
    xbmc.sleep(500)
    for action, identity in (('left', 134), ('right', 136), ('right', 135), ('left', 136)):
        press(action)
        until(lambda:focus(identity), 'header-neighbor-focus')
    guard.require(guard.idle(), 'unexpected-playback')
    result.update(passed=True, header_focus_preserved=True, route_unchanged=True,
                  no_api_setup_or_playback=True, idle_empty=True)
finally:
    if guard.idle() and xbmcgui.getCurrentWindowId() == 10000:
        xbmc.executebuiltin('Control.SetFocus(100)')
    (root / ('native-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
