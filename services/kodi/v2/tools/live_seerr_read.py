"""HP-only read/search proof for Aster Requests; never invokes request action."""

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
            'seerr-read-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    require('error' not in reply, 'seerr-read-rpc-failed')
    return reply['result']


def until(check, code, seconds=12):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(100)
    raise AssertionError(code)


def action(value):
    rpc('Input.ExecuteAction', {'action': value})


result = {'passed': False, 'query': 'Arrival', 'write_action_invoked': False}
try:
    require(not rpc('Player.GetActivePlayers') and xbmcgui.getCurrentWindowId() == 10000,
            'seerr-read-home-idle-required')
    xbmc.executebuiltin('RunScript(script.asterseerr)')
    until(lambda: xbmcgui.getCurrentWindowId() == 11132
          and HOME.getProperty('AsterSeerr.Query') == 'Search Seerr…',
          'seerr-read-window-not-ready')
    action('select')
    until(lambda: rpc('XBMC.GetInfoLabels', {'labels': ['System.CurrentWindow']})
          .get('System.CurrentWindow') in ('Keyboard', 'Virtual keyboard'),
          'seerr-read-keyboard-not-open')
    rpc('Input.SendText', {'text': result['query'], 'done': True})
    until(lambda: xbmcgui.getCurrentWindowId() == 11132,
          'seerr-read-keyboard-not-confirmed')
    until(lambda: HOME.getProperty('AsterSeerr.Query') == result['query']
          and HOME.getProperty('AsterSeerr.Status').endswith(' results')
          and HOME.getProperty('AsterSeerr.Title'),
          'seerr-read-results-not-ready', 20)
    status = HOME.getProperty('AsterSeerr.Status')
    result.update(count=int(status.split()[0]),
                  selected=HOME.getProperty('AsterSeerr.Title'),
                  status=status, title=HOME.getProperty('AsterSeerr.Title'),
                  page_query=HOME.getProperty('AsterSeerr.Query'))
    require(result['selected'] and result['title'] and result['count'] <= 24
            and result['page_query'] == result['query'],
            'seerr-read-result-invalid')
    xbmc.executebuiltin('TakeScreenshot(' + str(ROOT / 'requests-arrival.png') + ')')
    xbmc.sleep(700)
    action('back')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000,
          'seerr-read-home-return')
    require(not rpc('Player.GetActivePlayers'), 'seerr-read-player-started')
    result['passed'] = True
except Exception as error:
    result['failure'] = str(error)
    result['window'] = xbmcgui.getCurrentWindowId()
    result['page_query'] = HOME.getProperty('AsterSeerr.Query')
    result['page_status'] = HOME.getProperty('AsterSeerr.Status')
    if xbmcgui.getCurrentWindowId() == 11132:
        action('back')
finally:
    (ROOT / 'read-proof.json').write_text(json.dumps(result, indent=2))
