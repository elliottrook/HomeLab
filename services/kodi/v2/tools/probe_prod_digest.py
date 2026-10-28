"""Bounded production News probe: open, launch, observe, stop, and return Home."""
import json
import os
from pathlib import Path
import re
import time

import xbmc
import xbmcgui


def require(value, code):
    if not value:
        raise RuntimeError(code)


def rpc(method, params=None):
    allowed = {
        'Player.GetActivePlayers', 'Player.Stop', 'Playlist.GetItems',
    }
    require(method in allowed, 'probe-rpc-boundary')
    request = dict(jsonrpc='2.0', id=1, method=method, params=params or {})
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    require('error' not in reply, 'probe-rpc-failed')
    return reply['result']


def idle():
    if rpc('Player.GetActivePlayers'):
        return False
    return all(
        rpc('Playlist.GetItems', {
            'playlistid': identity, 'limits': {'start': 0, 'end': 1},
        })['limits']['total'] == 0
        for identity in (0, 1)
    )


def until(check, code, seconds=35):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(100)
    raise RuntimeError(code)


def prop(name):
    return xbmc.getInfoLabel('Window.Property(Digest.' + name + ')')


def opened():
    return bool(xbmcgui.Window(10000).getProperty('AsterDigest.PlayerWindow'))


result = {
    'passed': False,
    'host': os.uname().nodename,
    'production_changed': False,
}
try:
    require(os.uname().nodename == 'AsterTVProd', 'production-host-required')
    require(xbmcgui.getCurrentWindowId() == 10000 and idle(), 'home-idle-required')
    xbmc.executebuiltin('ActivateWindow(1111)')
    window = xbmcgui.Window(11111)
    until(lambda: xbmcgui.getCurrentWindowId() == 11111, 'news-window-not-open')
    until(lambda: window.getProperty('AsterHub.Ready') == 'true', 'news-not-ready')
    # Ready is published before the refresh worker has fully returned.  Wait
    # for that bounded script instance to release the same hub_data entry.
    xbmc.sleep(700)
    result['page'] = {
        'generated_at': window.getProperty('AsterHub.GeneratedAt'),
        'status': window.getProperty('AsterHub.Status'),
        'rows_ready': window.getProperty('AsterHub.RowsReady'),
        'focus': window.getFocusId(),
        'list_size': xbmc.getInfoLabel('Container(500).NumItems'),
    }
    require(idle(), 'news-autoplayed')
    xbmc.executebuiltin('RunScript(special://skin/tools/hub_data.py,digest,play)')
    until(opened, 'digest-player-not-open')
    until(lambda: prop('Playing') == 'true' or bool(prop('ErrorCode')),
          'digest-player-no-result')
    result['player'] = {
        key: prop(key)
        for key in ('Playing', 'Title', 'Status', 'ErrorCode', 'ActiveId')
    }
    require(result['player']['Playing'] == 'true', 'digest-not-playing')
    xbmc.executebuiltin('Action(Back)')
    until(lambda: not opened(), 'digest-player-not-closed')
    until(lambda: xbmcgui.getCurrentWindowId() == 11111 and idle(),
          'digest-return-not-idle')
    result['passed'] = True
except Exception as error:
    code = str(error)
    result['code'] = code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__
    result['window'] = xbmcgui.getCurrentWindowId()
    result['diagnostics'] = {
        key: prop(key)
        for key in ('Playing', 'Title', 'Status', 'ErrorCode', 'ActiveId')
    }
    result['diagnostics']['PlayerWindow'] = xbmcgui.Window(10000).getProperty(
        'AsterDigest.PlayerWindow')
finally:
    players = rpc('Player.GetActivePlayers')
    for player in players:
        rpc('Player.Stop', {'playerid': player['playerid']})
    if opened():
        xbmc.executebuiltin('Action(Back)')
        try:
            until(lambda: not opened(), 'digest-cleanup-window', 10)
        except RuntimeError:
            pass
    xbmc.executebuiltin('ActivateWindow(Home)')
    try:
        until(lambda: xbmcgui.getCurrentWindowId() == 10000 and idle(),
              'digest-cleanup-home', 15)
    except RuntimeError:
        result['cleanup_failed'] = True
    result['idle_empty'] = idle()
    Path('/tmp/astertv-prod-digest-probe.json').write_text(json.dumps(result, indent=2))
