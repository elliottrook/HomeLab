"""HP startup proof: sound-engine errors, no repeats, no media state changes."""
import json
import os
import re
import time
from pathlib import Path
import xbmc

if os.uname().nodename != 'AsterTV': raise RuntimeError('hp-only')
BASE = Path('/storage/.aster-checkpoints/aster-startup-20261025')
STATE = Path('/storage/.kodi/userdata/addon_data/service.aster.startup/last-startup.json')


def require(value, code):
    if not value: raise RuntimeError(code)


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Playlist.GetItems'), 'read-only-rpc')
    response = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    require('error' not in response, 'native-read-failed')
    return response['result']


try:
    before = STATE.read_bytes()
    state = json.loads(before)
    require(state['outcome'] == 'gui-sound-requested', 'startup-outcome')
    xbmc.executebuiltin('RunScript(/storage/.kodi/addons/service.aster.startup/service.py)')
    xbmc.sleep(1000)
    require(STATE.read_bytes() == before, 'duplicate-request')
    require(not rpc('Player.GetActivePlayers'), 'unexpected-player')
    require(all(rpc('Playlist.GetItems', dict(playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1)), 'unexpected-queue')
    log = Path('/storage/.kodi/temp/kodi.log').read_text(errors='replace').splitlines()
    errors = sum(bool(re.search(r'\b(ERROR|FATAL)\b', line)) and any(term in line for term in ('ActiveAESound', 'startup.wav', 'service.aster.startup')) for line in log)
    require(errors == 0, 'startup-sound-engine-error')
    require(sum('Aster startup: gui-sound-requested' in line for line in log) == 1, 'unexpected-startup-count')
    proof = dict(ok=True, startup=state, duplicate_invocation_suppressed=True, sound_engine_errors=errors,
                 players_empty=True, queues_empty=True, gui_sound_requests_this_log=1,
                 audible_confirmation=False)
except Exception as error:
    proof = dict(ok=False, code=str(error))
(BASE / ('native-' + str(time.time_ns()) + '.json')).write_text(json.dumps(proof, indent=2))
