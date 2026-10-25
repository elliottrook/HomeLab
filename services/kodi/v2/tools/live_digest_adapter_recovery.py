"""Retire only the unique local audio file from the first adapter trial."""
import hashlib
import json
import os
from pathlib import Path
import time
import xbmc

if os.uname().nodename != 'AsterTV': raise RuntimeError('hp-only')
root = Path('/storage/.aster-checkpoints/aster-digest-adapter-1792968714628089086')
files = list(root.glob('session-*.mp3'))
if len(files) != 1: raise RuntimeError('exact-trial-copy-required')
expected = str(files[0])
player = xbmc.Player()
owned = lambda:player.isPlayingAudio() and player.getPlayingFile() == expected
reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'))
result = dict(unique_trial_file_playing=owned(), player_schema=[sorted(row) for row in reply.get('result', [])], stopped=False)
if owned():
    player.stop()
    end = time.monotonic()+3
    while owned() and time.monotonic() < end: xbmc.sleep(50)
    result['stopped'] = not owned()
result['active_players'] = len(json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result', []))
queue = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Playlist.GetItems","params":{"playlistid":0,"properties":["file"]}}')).get('result', {})
result['audio_queue_count'] = queue.get('limits', {}).get('total')
if result['active_players'] == 0 and queue.get('limits', {}).get('total') == 1 and [row.get('file') for row in queue.get('items', [])] == [expected]:
    cleared = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Playlist.Clear","params":{"playlistid":0}}'))
    result['exact_private_trial_queue_cleared'] = 'error' not in cleared
(root / 'recovery.json').write_text(json.dumps(result, indent=2))
