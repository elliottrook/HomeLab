"""Native HP saved-result checks for two already journalled approvals."""
import hashlib
import json
import os
from pathlib import Path
import time

import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
HOME = xbmcgui.Window(10000)
MONITOR = xbmc.Monitor()
SPECS = (
    ('music', 'musicbrainz:release-group:810272e0-aef1-3d85-b2d3-e512e87fc38c'),
    ('books', 'openlibrary:/works/OL893502W'),
)


def require(value, code):
    if not value:
        raise RuntimeError(code)


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Input.Home'), 'saved-ui-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    require('error' not in reply, 'saved-ui-rpc-failed')
    return reply['result']


def until(check, code):
    end = time.monotonic()+35
    while time.monotonic() < end:
        if check():
            return
        require(not MONITOR.waitForAbort(.1), 'saved-ui-aborted')
    raise RuntimeError(code)


def journal():
    root = Path('/storage/.aster-private/acquisition-journal')
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.json')}


result = {'passed': False, 'checks': []}
admitted = False
try:
    require(os.uname().nodename == 'AsterTV' and not rpc('Player.GetActivePlayers'),
            'saved-ui-hp-idle-required')
    before = journal()
    for _domain, identity in SPECS:
        path = Path('/storage/.aster-private/acquisition-journal')/(
            hashlib.sha256(identity.encode()).hexdigest()+'.json')
        require(json.loads(path.read_text())['status'] == 'committed',
                'saved-ui-needs-committed-record')
    admitted = True
    rpc('Input.Home')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000, 'saved-ui-home')
    MONITOR.waitForAbort(.5)
    xbmc.executebuiltin('RunScript(script.asteracquisition)')
    until(lambda: xbmcgui.getCurrentWindowId() == 11133, 'saved-ui-entry')
    window = xbmcgui.Window(11133)
    for domain, identity in SPECS:
        HOME.setProperty('AsterAcquisition.Command', 'tab:'+domain)
        until(lambda: HOME.getProperty('AsterAcquisition.Domain') == domain,
              'saved-ui-domain')
        def matches_for_identity():
            count = int(xbmc.getInfoLabel('Container(30).NumItems') or '0')
            require(0 <= count <= 12, 'saved-ui-list-bound')
            return [i for i in range(count) if xbmc.getInfoLabel(
                'Container(30).ListItemAbsolute(%d).Property(Identity)' % i) == identity]
        until(lambda: bool(matches_for_identity()), 'saved-ui-native-list-ready')
        matches = matches_for_identity()
        require(len(matches) == 1, 'saved-ui-approved-item-not-in-feed')
        xbmc.executebuiltin('Control.SetFocus(30,%d,absolute)' % matches[0])
        until(lambda: HOME.getProperty('AsterAcquisition.Status') ==
              'Request accepted · waiting for library import'
              and HOME.getProperty('AsterAcquisition.Title') ==
              ('Homogenic' if domain == 'music' else 'Heretics of Dune'), 'saved-ui-status')
        require(not HOME.getProperty('AsterAcquisition.PrimaryAction'), 'saved-ui-action-not-hidden')
        for _ in range(2):
            HOME.setProperty('AsterAcquisition.Command', 'action')
            until(lambda: not HOME.getProperty('AsterAcquisition.Command'), 'saved-ui-action-handled')
            require(journal() == before, 'saved-ui-journal-mutated')
        require(not MONITOR.waitForAbort(1), 'saved-ui-aborted')
        xbmc.executebuiltin('TakeScreenshot('+str(ROOT/(domain+'-saved.png'))+',false)')
        require(not MONITOR.waitForAbort(.5), 'saved-ui-aborted')
        result['checks'].append(domain+'-saved-outcome-and-repeat')
    require(not rpc('Player.GetActivePlayers'), 'saved-ui-player-started')
    require(journal() == before, 'saved-ui-journal-mutated')
    result.update(passed=True, journal_unchanged=True)
except Exception as error:
    text = str(error)
    result['code'] = text if text.isascii() and len(text) < 100 else type(error).__name__
finally:
    if admitted and not rpc('Player.GetActivePlayers'):
        rpc('Input.Home')
        until(lambda: xbmcgui.getCurrentWindowId() == 10000, 'saved-ui-home-cleanup')
    result.update(home=xbmcgui.getCurrentWindowId() == 10000,
                  idle=not rpc('Player.GetActivePlayers'))
    path = ROOT/('saved-ui-result-%d.json' % time.time_ns())
    path.write_text(json.dumps(result, sort_keys=True))
    path.chmod(0o600)
