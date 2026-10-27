"""HP-only explicit press-to-talk controller; no retained audio or transcript."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'resources/lib'))
from voice_native_policy import PULSE_SOURCE, resolve
from voice_release import ReleaseSignal
from voice_search import VoiceUnavailable
from voice_search_attempt import attempt
from voice_search_transport import credential, transport


PREFIX = 'AsterSearch.'
STATE = Path('/storage/.aster-checkpoints/aster-voice-search1')
SEARCH_WINDOW = 11127


def require(value, reason):
    if not value:
        raise VoiceUnavailable(reason)


def rpc(method, params=None):
    require(method == 'Player.GetActivePlayers', 'voice-rpc-boundary')
    result = json.loads(xbmc.executeJSONRPC(json.dumps(
        {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    require('error' not in result, 'voice-rpc-unavailable')
    return result.get('result', {})


def inventory():
    inputs = Path('/proc/bus/input/devices').read_text()
    pcms = Path('/proc/asound/pcm').read_text()
    value = subprocess.run(['/usr/bin/pactl', 'list', 'short', 'sources'],
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=3, check=True)
    return resolve(inputs, pcms, value.stdout)


def main():
    if os.uname().nodename != 'AsterTV':
        return
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(STATE / 'entry.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    release = None
    home = xbmcgui.Window(10000)
    monitor = xbmc.Monitor()
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        require(not rpc('Player.GetActivePlayers'), 'voice-active-playback')
        capability, sources = inventory()
        release = ReleaseSignal(capability.policy.event_handler,
                                capability.policy.event_code)
        require(xbmcgui.getCurrentWindowId() in (10000, SEARCH_WINDOW),
                'voice-foreground-context')
        if xbmcgui.getCurrentWindowId() != SEARCH_WINDOW:
            xbmc.executebuiltin('ActivateWindow(Home)')
            xbmc.executebuiltin('RunScript(script.asterruntime,aster-global-search-ui22,default)')
            end = time.monotonic() + 10
            while not (xbmcgui.getCurrentWindowId() == SEARCH_WINDOW
                       and home.getProperty(PREFIX + 'Ready') == 'true'):
                require(time.monotonic() < end and not monitor.waitForAbort(.05),
                        'voice-search-window-unavailable')
        home.clearProperty(PREFIX + 'VoiceCancel')
        home.setProperty(PREFIX + 'VoiceBusy', 'true')

        def cancelled():
            return (monitor.abortRequested()
                    or xbmcgui.getCurrentWindowId() != SEARCH_WINDOW
                    or home.getProperty(PREFIX + 'VoiceCancel') == 'true')

        def changed(view):
            home.setProperty(PREFIX + 'Status', view.status)
            home.setProperty(PREFIX + 'VoiceState',
                             'busy' if view.busy else view.action)

        result = attempt(capability, sources, PULSE_SOURCE,
                         cancelled=cancelled, released=release.released,
                         token=credential, transport=transport, changed=changed)
        if result.state == 'results' and not cancelled():
            home.setProperty(PREFIX + 'VoiceQuery', result.query)
            home.setProperty(PREFIX + 'Command', 'voice')
        elif result.state == 'error' and not cancelled():
            xbmcgui.Dialog().notification('Voice search', result.reason,
                                          xbmcgui.NOTIFICATION_INFO, 3500)
    except (VoiceUnavailable, OSError, subprocess.SubprocessError,
            ValueError, KeyError, json.JSONDecodeError):
        if xbmcgui.getCurrentWindowId() == SEARCH_WINDOW:
            home.setProperty(PREFIX + 'Status',
                             'Voice search unavailable · use the keyboard or try again')
        else:
            xbmcgui.Dialog().notification('Voice search unavailable',
                                          'Open Search and use the keyboard.')
    finally:
        home.clearProperty(PREFIX + 'VoiceBusy')
        home.clearProperty(PREFIX + 'VoiceCancel')
        if release is not None:
            release.close()
        os.close(descriptor)


if __name__ == '__main__':
    main()
