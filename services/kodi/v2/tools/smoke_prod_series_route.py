"""Production Home TV-show selection must open the v2 series preview."""
import json
import os
from pathlib import Path
import time

import xbmc
import xbmcgui


result = {'passed': False, 'production_changed': False}
home = xbmcgui.Window(10000)
try:
    if os.uname().nodename != 'AsterTVProd' or xbmcgui.getCurrentWindowId() != 10000:
        raise RuntimeError('series-production-home-required')
    if home.getProperty('AsterSeries.PreviewWindow'):
        raise RuntimeError('series-production-preview-existing')
    position = None
    identity = None
    for index in range(10):
        xbmc.executebuiltin('SetFocus(110,' + str(index) + ',absolute)')
        xbmc.sleep(120)
        if xbmc.getInfoLabel('Container(110).ListItem.DBTYPE') == 'tvshow':
            candidate = xbmc.getInfoLabel('Container(110).ListItem.DBID')
            if candidate.isdecimal() and int(candidate) > 0:
                position, identity = index, candidate
                break
    if position is None:
        raise RuntimeError('series-production-tvshow-unavailable')
    started = time.monotonic()
    xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
    deadline = started + 10
    while time.monotonic() < deadline and not home.getProperty('AsterSeries.PreviewWindow'):
        xbmc.sleep(50)
    preview = home.getProperty('AsterSeries.PreviewWindow')
    if not preview.isdecimal() or xbmcgui.getCurrentWindowId() != int(preview):
        raise RuntimeError('series-production-v2-preview-not-open')
    if xbmc.getInfoLabel('Window.Property(Series.Ready)') != 'true':
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and xbmc.getInfoLabel('Window.Property(Series.Ready)') != 'true':
            xbmc.sleep(100)
    if xbmc.getInfoLabel('Window.Property(Series.Ready)') != 'true':
        raise RuntimeError('series-production-preview-not-ready')
    visible_ms = round((time.monotonic() - started) * 1000)
    xbmc.executebuiltin('Action(Back)')
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and home.getProperty('AsterSeries.PreviewWindow'):
        xbmc.sleep(50)
    players = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'))['result']
    if home.getProperty('AsterSeries.PreviewWindow') or players:
        raise RuntimeError('series-production-return-not-idle')
    result.update(passed=True, position=position, show_id=int(identity),
                  preview_window=int(preview), visible_ms=visible_ms,
                  v2_preview_ready=True, idle_empty=True)
except Exception as error:
    result['code'] = str(error)
finally:
    if home.getProperty('AsterSeries.PreviewWindow'):
        xbmc.executebuiltin('Action(Back)')
        xbmc.sleep(1000)
    xbmc.executebuiltin('ActivateWindow(Home)')
    Path('/tmp/astertv-prod-series-route.json').write_text(json.dumps(result, indent=2))
