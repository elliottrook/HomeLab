"""Read-only production YouTube landing focus/navigation probe."""
import json
import os
from pathlib import Path
import time

import xbmc
import xbmcgui


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


def focus(identity):
    return xbmc.getCondVisibility('Control.HasFocus(' + str(identity) + ')')


def action(name):
    request = dict(jsonrpc='2.0', id=1, method='Input.ExecuteAction',
                   params={'action': name})
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    require('error' not in response, 'youtube-production-input')


result = {'passed': False, 'production_changed': False, 'checks': []}
try:
    require(os.uname().nodename == 'AsterTVProd'
            and xbmcgui.getCurrentWindowId() == 10000,
            'youtube-production-home-required')
    xbmc.sleep(700)
    xbmc.executebuiltin('Control.SetFocus(136)')
    until(lambda: focus(136), 'youtube-production-home-focus')
    action('select')
    until(lambda: xbmcgui.getCurrentWindowId() == 10025
          and xbmc.getInfoLabel('Container.FolderPath') ==
          'plugin://plugin.video.youtube/', 'youtube-production-root')
    try:
        until(lambda: focus(9530), 'youtube-production-root-focus', seconds=7)
    except RuntimeError:
        xbmc.executebuiltin('Control.SetFocus(9530)')
        until(lambda: focus(9530), 'youtube-production-control-focus', seconds=3)
        result['manual_control_focus_required'] = True
    result['checks'].append('root-focus')
    action('down')
    until(lambda: focus(9531), 'youtube-production-row-down')
    action('down')
    until(lambda: focus(9532), 'youtube-production-second-row-down')
    action('up')
    until(lambda: focus(9531), 'youtube-production-row-up')
    action('up')
    until(lambda: focus(9530), 'youtube-production-first-row-up')
    action('up')
    until(lambda: focus(9301), 'youtube-production-top-rail')
    action('right')
    until(lambda: focus(9302), 'youtube-production-top-right')
    action('left')
    until(lambda: focus(9301), 'youtube-production-top-left')
    action('down')
    until(lambda: focus(9530), 'youtube-production-top-return')
    result['checks'].extend(['vertical-rows', 'top-rail', 'top-return'])
    action('up')
    until(lambda: focus(9301), 'youtube-production-browse-rail')
    action('right')
    until(lambda: focus(9302), 'youtube-production-browse-choice')
    action('select')
    until(lambda: 'special/recommendations' in xbmc.getInfoLabel('Container.FolderPath'),
          'youtube-production-browse-route')
    until(lambda: focus(50), 'youtube-production-browse-focus')
    result['checks'].append('browse-focus')
    xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/youtube_back.py)')
    until(lambda: xbmc.getInfoLabel('Container.FolderPath') ==
          'plugin://plugin.video.youtube/' and focus(9530),
          'youtube-production-browse-back')
    result['checks'].append('browse-back-root-focus')
    xbmc.executebuiltin('Control.SetFocus(9305)')
    until(lambda: focus(9305), 'youtube-production-back-button-focus')
    action('select')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000,
          'youtube-production-back-home')
    players = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'))['result']
    require(not players, 'youtube-production-autoplay')
    result.update(passed=True, idle_empty=True)
except Exception as error:
    result['code'] = str(error)
    result['window'] = xbmcgui.getCurrentWindowId()
    result['folder'] = xbmc.getInfoLabel('Container.FolderPath')
    result['focused'] = next((identity for identity in
        (9530, 9531, 9532, 9300, 9301, 9302, 9303, 9304, 9305, 50)
        if focus(identity)), None)
finally:
    xbmc.executebuiltin('ActivateWindow(Home)')
    Path('/tmp/astertv-prod-youtube-navigation.json').write_text(
        json.dumps(result, indent=2))
