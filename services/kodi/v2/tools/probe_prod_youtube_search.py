"""Read-only production YouTube search-page and focus probe."""
import json
import os
from pathlib import Path
import time

import xbmc
import xbmcgui


ROOT = 'plugin://plugin.video.youtube/'
SEARCH = 'plugin://plugin.video.youtube/kodion/search/'


def require(value, code):
    if not value:
        raise RuntimeError(code)


def until(check, code, seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(100)
    raise RuntimeError(code)


def focus(identity):
    return xbmc.getCondVisibility('Control.HasFocus(%d)' % identity)


def rpc(method, params=None):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method,
        'params': params or {},
    })))
    require('error' not in reply, 'youtube-search-rpc')
    return reply.get('result')


def action(name):
    rpc('Input.ExecuteAction', {'action': name})


result = {'passed': False, 'production_changed': False, 'query': 'OpenAI'}
try:
    require(os.uname().nodename == 'AsterTVProd'
            and xbmcgui.getCurrentWindowId() == 10000,
            'youtube-search-home-required')
    xbmc.executebuiltin('Control.SetFocus(136)')
    until(lambda: focus(136), 'youtube-search-home-focus')
    action('select')
    until(lambda: xbmcgui.getCurrentWindowId() == 10025
          and xbmc.getInfoLabel('Container.FolderPath') == ROOT,
          'youtube-search-root')
    try:
        until(lambda: focus(9530), 'youtube-search-root-focus', seconds=7)
    except RuntimeError:
        xbmc.executebuiltin('Control.SetFocus(9530)')
        until(lambda: focus(9530), 'youtube-search-root-control-focus')
        result['manual_root_focus_required'] = True
    xbmc.executebuiltin('Control.SetFocus(9300)')
    until(lambda: focus(9300), 'youtube-search-button-focus')
    action('select')
    until(lambda: xbmc.getCondVisibility('Window.IsActive(virtualkeyboard)'),
          'youtube-search-keyboard')
    rpc('Input.SendText', {'text': result['query'], 'done': True})
    until(lambda: (xbmcgui.getCurrentWindowId() == 10025
                   and '/kodion/search/query/' in
                   xbmc.getInfoLabel('Container.FolderPath')),
          'youtube-search-results', 45)
    until(lambda: (focus(50)
          and int(xbmc.getInfoLabel('Container(50).NumItems') or '0') > 1
          and bool(xbmc.getInfoLabel('Container(50).ListItem.Label'))),
          'youtube-search-result-ready', 45)
    xbmc.sleep(1000)
    require('/kodion/search/query/' in
            xbmc.getInfoLabel('Container.FolderPath'),
            'youtube-search-result-stability')
    result['page'] = {
        'folder': xbmc.getInfoLabel('Container.FolderPath'),
        'category': xbmc.getInfoLabel('Container.PluginCategory'),
        'items': int(xbmc.getInfoLabel('Container(50).NumItems') or '0'),
        'label': xbmc.getInfoLabel('Container(50).ListItem.Label'),
        'has_plot': bool(xbmc.getInfoLabel('Container(50).ListItem.Plot')),
        'focus': 50,
    }
    action('firstpage')
    xbmc.sleep(300)
    action('up')
    until(lambda: focus(9400), 'youtube-search-rail')
    action('right')
    until(lambda: focus(9401), 'youtube-search-rail-right')
    action('down')
    until(lambda: focus(50), 'youtube-search-results-return')
    screenshot = Path('/tmp/astertv-prod-youtube-search.png')
    if screenshot.exists():
        screenshot.unlink()
    xbmc.executebuiltin('TakeScreenshot(%s,false)' % screenshot)
    until(screenshot.is_file, 'youtube-search-screenshot', 10)
    result['screenshot_bytes'] = screenshot.stat().st_size
    xbmc.executebuiltin('Control.SetFocus(9404)')
    until(lambda: focus(9404), 'youtube-search-back-button-focus')
    action('select')
    until(lambda: xbmc.getInfoLabel('Container.FolderPath') == ROOT,
          'youtube-search-back-root')
    try:
        until(lambda: focus(9530), 'youtube-search-back-focus', seconds=7)
    except RuntimeError:
        result['manual_back_focus_required'] = True
        xbmc.executebuiltin('Control.SetFocus(9530)')
        until(lambda: focus(9530), 'youtube-search-back-control-focus')
    xbmc.executebuiltin('Control.SetFocus(9305)')
    until(lambda: focus(9305), 'youtube-search-root-back-button-focus')
    action('select')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000,
          'youtube-search-back-home')
    require(not rpc('Player.GetActivePlayers'), 'youtube-search-autoplay')
    result['passed'] = True
    result['idle_empty'] = True
except Exception as error:
    result['code'] = str(error)
    result['window'] = xbmcgui.getCurrentWindowId()
    result['folder'] = xbmc.getInfoLabel('Container.FolderPath')
    result['focused'] = next((identity for identity in
        (9530, 9300, 9400, 9401, 9402, 9403, 9404, 50)
        if focus(identity)), None)
finally:
    xbmc.executebuiltin('ActivateWindow(Home)')
    Path('/tmp/astertv-prod-youtube-search.json').write_text(
        json.dumps(result, indent=2))
