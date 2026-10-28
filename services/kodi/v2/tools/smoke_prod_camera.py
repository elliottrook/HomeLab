"""Production native Home-camera lifecycle smoke with owned cleanup."""
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import urlopen

import xbmc
import xbmcgui

sys.path.insert(0, '/storage/.kodi/addons/script.asterruntime/shared')
import runtime_guard as guard


def require(value, code):
    if not value:
        raise RuntimeError(code)


def until(check, code, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(100)
    raise RuntimeError(code)


def status():
    with urlopen('http://127.0.0.1:15102/status', timeout=3) as reply:
        return json.loads(reply.read(4097))


def select(identity):
    xbmc.executebuiltin('Control.SetFocus(' + str(identity) + ')')
    until(lambda: xbmc.getCondVisibility('Control.HasFocus(' + str(identity) + ')'),
          'camera-production-focus')
    request = dict(jsonrpc='2.0', id=1, method='Input.ExecuteAction',
                   params={'action': 'select'})
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    require('error' not in reply, 'camera-production-select')


result = {'passed': False, 'production_changed': False}
try:
    require(os.uname().nodename == 'AsterTVProd' and guard.idle()
            and xbmcgui.getCurrentWindowId() == 10000, 'camera-production-idle-home')
    before = guard.snapshot()
    require(status()['active'] is False, 'camera-production-existing-view')
    xbmc.executebuiltin('ActivateWindow(1112)')
    until(lambda: xbmcgui.getCurrentWindowId() == 11112, 'camera-production-window')
    window = xbmcgui.Window(11112)
    until(lambda: window.getProperty('AsterHub.HomeCameraStatus') ==
          'Ready · images on request', 'camera-production-not-ready')
    select(302)
    until(lambda: status()['active'], 'camera-production-not-active')
    until(lambda: status()['frames'] >= 2, 'camera-production-no-frames')
    require(window.getProperty('AsterHub.CameraPlaying') == 'true'
            and window.getProperty('AsterHub.CameraButtonLabel') == 'Stop view',
            'camera-production-properties')
    first = status()['frame_sha256']
    select(302)
    until(lambda: not status()['active'], 'camera-production-toggle-stop')
    until(lambda: window.getProperty('AsterHub.CameraPlaying') == 'false'
          and not window.getProperty('AsterHub.CameraImage'),
          'camera-production-image-not-cleared')
    select(302)
    until(lambda: status()['frames'] >= 2, 'camera-production-second-view')
    second = status()['frame_sha256']
    xbmc.executebuiltin('ActivateWindow(Home)')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000, 'camera-production-home')
    until(lambda: not status()['active'], 'camera-production-exit-stop')
    require(guard.idle() and guard.snapshot() == before, 'camera-production-preservation')
    result.update(passed=True, native_image_fetch=True, two_sessions=True,
                  toggle_stop=True, exit_stop=True, no_player_opened=True,
                  first_frame_sha256=first, second_frame_sha256=second,
                  idle_empty=True)
except Exception as error:
    code = str(error)
    result['code'] = code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__
finally:
    if xbmcgui.getCurrentWindowId() == 11112:
        xbmc.executebuiltin('ActivateWindow(Home)')
    result['idle_empty'] = guard.idle()
    Path('/tmp/astertv-prod-camera-smoke.json').write_text(json.dumps(result, indent=2))
