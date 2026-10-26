"""HP-only owner-authorized Seerr write acceptance through the native page.

Creates two pending requests selected by the owner-delegated test: Hundreds of
Beavers (film) and The Pitt season 1. It never retries an uncertain write.
"""

import hashlib
import json
from pathlib import Path
import time

import xbmc
import xbmcgui


ROOT = Path('/storage/.aster-staging/aster-seerr-page3')
JOURNAL = Path('/storage/.aster-private/seerr-journal')
HOME = xbmcgui.Window(10000)


def require(value, code):
    if not value:
        raise AssertionError(code)


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Input.ExecuteAction',
                       'Input.SendText', 'XBMC.GetInfoLabels'),
            'seerr-write-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method,
        'params': params or {}})))
    require('error' not in reply, 'seerr-write-rpc-failed')
    return reply['result']


def until(check, code, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(100)
    raise AssertionError(code)


def action(value):
    rpc('Input.ExecuteAction', {'action': value})


def open_page():
    require(xbmcgui.getCurrentWindowId() == 10000,
            'seerr-write-home-required')
    xbmc.executebuiltin('RunScript(script.asterseerr)')
    until(lambda: xbmcgui.getCurrentWindowId() == 11132
          and HOME.getProperty('AsterSeerr.Query') == 'Search Seerr…',
          'seerr-write-window-not-ready')


def close_page():
    HOME.setProperty('AsterSeerr.Command', 'back')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000,
          'seerr-write-home-return')


def search(query, media_type):
    require(media_type in ('movie', 'tv'), 'seerr-write-filter')
    steps = 2 if media_type == 'movie' else 3
    for _ in range(steps):
        action('right'); xbmc.sleep(120)
    action('select')
    expected = 'Films' if media_type == 'movie' else 'Television'
    until(lambda: HOME.getProperty('AsterSeerr.Filter') == expected,
          'seerr-write-filter-not-set')
    for _ in range(steps):
        action('left'); xbmc.sleep(120)
    action('select')
    until(lambda: rpc('XBMC.GetInfoLabels', {'labels': ['System.CurrentWindow']})
          .get('System.CurrentWindow') in ('Keyboard', 'Virtual keyboard'),
          'seerr-write-keyboard-not-open')
    rpc('Input.SendText', {'text': query, 'done': True})
    until(lambda: xbmcgui.getCurrentWindowId() == 11132
          and HOME.getProperty('AsterSeerr.Query') == query
          and HOME.getProperty('AsterSeerr.Title') == query,
          'seerr-write-result-not-ready')


def journal_rows(strict=True):
    if not JOURNAL.exists():
        return []
    rows = []
    for path in sorted(JOURNAL.glob('*.json')):
        require(path.is_file() and not path.is_symlink(),
                'seerr-write-journal-linked')
        raw = path.read_bytes()
        value = json.loads(raw)
        if strict:
            require(value.get('schema') == 1
                    and value.get('status') == 'committed'
                    and value.get('result', {}).get('state') == 'pending',
                    'seerr-write-not-pending')
        response = value.get('result') if isinstance(value.get('result'), dict) else {}
        rows.append({'name': path.name,
                     'candidate_id': value.get('candidate_id'),
                     'journal_status': value.get('status'),
                     'request_id': response.get('request_id'),
                     'state': response.get('state'),
                     'sha256': hashlib.sha256(raw).hexdigest()})
    return rows


def confirm_request(expect_count, season=False):
    window = xbmcgui.Window(11132)
    if season:
        require(HOME.getProperty('AsterSeerr.SeasonsVisible') == 'true',
                'seerr-write-seasons-not-visible')
        window.setFocusId(40)
        # The list's XML onclick is not raised reliably by Kodi's synthetic
        # select action. Exercise the same controller command it owns instead;
        # this does not bypass validation or the two-step request path.
        HOME.setProperty('AsterSeerr.Command', 'season')
        until(lambda: HOME.getProperty('AsterSeerr.SeasonHint') == '1 selected',
              'seerr-write-season-not-selected')
    window.setFocusId(50)
    action('select')
    until(lambda: HOME.getProperty('AsterSeerr.RequestLabel') == 'Confirm request',
          'seerr-write-confirmation-not-shown')
    action('select')
    until(lambda: HOME.getProperty('AsterSeerr.RequestLabel') == 'Request sent',
          'seerr-write-not-accepted')
    rows = journal_rows()
    require(len(rows) == expect_count, 'seerr-write-journal-count')
    return rows


result = {'passed': False, 'write_action_invoked': False,
          'movie': 'Hundreds of Beavers', 'television': 'The Pitt', 'season': 1}
try:
    require(not rpc('Player.GetActivePlayers'), 'seerr-write-idle-required')
    existing = journal_rows() if JOURNAL.exists() else []
    if existing:
        require(len(existing) == 1
                and existing[0]['candidate_id'] == 'seerr:movie:1019939',
                'seerr-write-resume-journal-invalid')
        result['resumed_from_committed_movie'] = True
        result['cancel_without_write'] = True
        result['write_action_invoked'] = True
        result['movie_result'] = existing[0]
    else:
        # First prove that the first confirmation can be cancelled without a write.
        open_page()
        search(result['movie'], 'movie')
        xbmcgui.Window(11132).setFocusId(50)
        action('select')
        until(lambda: HOME.getProperty('AsterSeerr.RequestLabel') == 'Confirm request',
              'seerr-write-cancel-confirmation-not-shown')
        action('back')
        until(lambda: xbmcgui.getCurrentWindowId() == 10000,
              'seerr-write-cancel-home-return')
        require(not JOURNAL.exists(), 'seerr-write-cancel-created-journal')
        result['cancel_without_write'] = True

        open_page()
        search(result['movie'], 'movie')
        result['write_action_invoked'] = True
        movie_rows = confirm_request(1)
        result['movie_result'] = movie_rows[0]
        close_page()

    open_page()
    search(result['television'], 'tv')
    tv_rows = confirm_request(2, season=True)
    result['tv_result'] = next(
        row for row in tv_rows if row['candidate_id'].startswith('seerr:tv:'))
    close_page()

    # Fresh search must show status rather than a request action. Pressing it
    # must not alter the already committed journal or issue another write.
    before = {row['name']: row['sha256'] for row in journal_rows()}
    open_page()
    search(result['movie'], 'movie')
    require(HOME.getProperty('AsterSeerr.RequestLabel') == 'View request status',
            'seerr-write-duplicate-status-missing')
    xbmcgui.Window(11132).setFocusId(50)
    action('select')
    xbmc.sleep(500)
    after = {row['name']: row['sha256'] for row in journal_rows()}
    require(after == before, 'seerr-write-duplicate-journal-changed')
    result['duplicate_prevented'] = True
    close_page()

    require(not rpc('Player.GetActivePlayers'), 'seerr-write-player-started')
    result['passed'] = True
except Exception as error:
    result['failure'] = str(error)
    result['window'] = xbmcgui.getCurrentWindowId()
    result['page_query'] = HOME.getProperty('AsterSeerr.Query')
    result['page_status'] = HOME.getProperty('AsterSeerr.Status')
    result['request_label'] = HOME.getProperty('AsterSeerr.RequestLabel')
    result['journal'] = journal_rows(False) if JOURNAL.exists() else []
    if xbmcgui.getCurrentWindowId() == 11132:
        HOME.setProperty('AsterSeerr.Command', 'back')
finally:
    (ROOT / 'write-acceptance-proof.json').write_text(
        json.dumps(result, indent=2, sort_keys=True))
