"""One pinned HP test rollback after a clock-verification refusal; no retry."""
import json,os,sys,time
from collections import Counter
from pathlib import Path
import xbmc
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from queue_reader import read_queue
from music_trial import validate_write
run=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024/shuffle-mode-1792863630620787184')
target=run/'explicit-recovery.json'
if target.exists():raise RuntimeError('recovery-already-attempted-do-not-retry')
intent=json.loads((run/'intent.json').read_text())
if intent['status']!='shuffle-on-requested' or intent['current_index']!=2:raise RuntimeError('unexpected-intent')
expected=tuple(intent['song_ids'])
if len(expected)!=5 or expected[0]!=expected[2] or expected[1]!=expected[4] or len(set(expected))!=3:
    raise RuntimeError('unexpected-test-selection')
def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in result:raise RuntimeError('native-rpc-failed')
    return result['result']
def require(condition,message):
    if not condition:raise RuntimeError(message)
before=read_queue(rpc)
props=rpc('Player.GetProperties',dict(playerid=0,properties=['speed','time','shuffled']))
require(before.current_index is not None and Counter(before.song_ids)==Counter(expected),'foreign-queue')
require(before.song_ids[before.current_index]==expected[2] and props['speed']==0 and props['shuffled'] is True,'unexpected-player')
require(not any(rpc('XBMC.GetInfoLabels',dict(labels=[
    'Window(Home).Property(AsterV2Lab.'+name+')' for name in ('Window','AlbumWindow')])).values()),'open-pilot')
record=dict(status='restore-requested',before=dict(song_ids=before.song_ids,current_index=before.current_index,properties=props))
with target.open('x') as output:json.dump(record,output)
target.chmod(0o600)
def write(method,params):
    validate_write(method,params,set(expected),queue_limit=20000)
    return rpc(method,params)
write('Player.SetShuffle',dict(playerid=0,shuffle=False))
restored=read_queue(rpc);after=rpc('Player.GetProperties',dict(playerid=0,properties=['speed','time','shuffled']))
require(restored.song_ids==expected and restored.current_index==2,'original-order-not-restored')
require(after['speed']==0 and after['shuffled'] is False and after['time']==props['time'],'paused-player-not-restored')
write('Player.Stop',dict(playerid=0))
deadline=time.monotonic()+10;started=time.monotonic()
while True:
    state=read_queue(rpc)
    require(state.song_ids in (expected,()),'foreign-queue-after-owned-stop')
    if state.current_index is None and time.monotonic()-started>=3.5:break
    require(time.monotonic()<deadline,'stop-timeout');xbmc.sleep(100)
if state.song_ids:write('Playlist.Clear',dict(playlistid=0))
require(not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids,'cleanup-not-verified')
record.update(status='recovered',original_order_and_occurrence=True,paused_clock_preserved=True,
    mode_off_before_stop=True,empty_queue_restored=True,checks_enforced=True)
target.write_text(json.dumps(record,sort_keys=True))
