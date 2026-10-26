"""HP-only proof for a partly-owned Seerr TV result; never writes."""

import json
from pathlib import Path
import time

import xbmc
import xbmcgui


ROOT = Path('/storage/.aster-staging/aster-seerr-page3')
HOME = xbmcgui.Window(10000)


def require(value, code):
    if not value:
        raise AssertionError(code)


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Input.ExecuteAction',
                       'Input.SendText', 'XBMC.GetInfoLabels'),
            'seerr-partial-tv-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method,
        'params': params or {}})))
    require('error' not in reply, 'seerr-partial-tv-rpc-failed')
    return reply['result']


def until(check, code, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(100)
    raise AssertionError(code)


def action(value):
    rpc('Input.ExecuteAction', {'action': value})


result = {'passed': False, 'query': 'The Morning Show',
          'write_action_invoked': False}
try:
    require(not rpc('Player.GetActivePlayers')
            and xbmcgui.getCurrentWindowId() == 10000,
            'seerr-partial-tv-home-idle-required')
    xbmc.executebuiltin('RunScript(script.asterseerr)')
    until(lambda: xbmcgui.getCurrentWindowId() == 11132
          and HOME.getProperty('AsterSeerr.Query') == 'Search Seerr…',
          'seerr-partial-tv-window-not-ready')
    for _ in range(3):
        action('right'); xbmc.sleep(150)
    action('select')
    until(lambda: HOME.getProperty('AsterSeerr.Filter') == 'Television',
          'seerr-partial-tv-filter-not-set')
    for _ in range(3):
        action('left'); xbmc.sleep(150)
    action('select')
    until(lambda: rpc('XBMC.GetInfoLabels', {'labels': ['System.CurrentWindow']})
          .get('System.CurrentWindow') in ('Keyboard', 'Virtual keyboard'),
          'seerr-partial-tv-keyboard-not-open')
    rpc('Input.SendText', {'text': result['query'], 'done': True})
    until(lambda: xbmcgui.getCurrentWindowId() == 11132
          and HOME.getProperty('AsterSeerr.Query') == result['query']
          and HOME.getProperty('AsterSeerr.Title') == result['query']
          and HOME.getProperty('AsterSeerr.RequestLabel')
          == 'Partly in your library',
          'seerr-partial-tv-result-not-ready')
    require(HOME.getProperty('AsterSeerr.SeasonsVisible') == 'false',
            'seerr-partial-tv-seasons-exposed')
    result.update(title=HOME.getProperty('AsterSeerr.Title'),
                  status=HOME.getProperty('AsterSeerr.Status'),
                  filter=HOME.getProperty('AsterSeerr.Filter'),
                  request_label=HOME.getProperty('AsterSeerr.RequestLabel'),
                  seasons_visible=HOME.getProperty('AsterSeerr.SeasonsVisible'))
    xbmc.sleep(1800)
    xbmc.executebuiltin('TakeScreenshot(' + str(
        ROOT / 'requests-partial-tv.png') + ')')
    xbmc.sleep(700)
    action('back')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000,
          'seerr-partial-tv-home-return')
    require(not rpc('Player.GetActivePlayers'),
            'seerr-partial-tv-player-started')
    result['passed'] = True
except Exception as error:
    result['failure'] = str(error)
    result['window'] = xbmcgui.getCurrentWindowId()
    result['page_query'] = HOME.getProperty('AsterSeerr.Query')
    result['page_status'] = HOME.getProperty('AsterSeerr.Status')
    result['request_label'] = HOME.getProperty('AsterSeerr.RequestLabel')
    result['seasons_visible'] = HOME.getProperty('AsterSeerr.SeasonsVisible')
    if xbmcgui.getCurrentWindowId() == 11132:
        action('back')
finally:
    (ROOT / 'partial-tv-read-proof.json').write_text(
        json.dumps(result, indent=2))
