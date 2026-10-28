"""Save the exact parked production video item privately before a playback test."""
import json
from pathlib import Path
import time
import xbmc

TARGET=Path('/storage/.aster-checkpoints/astertv-series-queue-20261028.json')
def rpc(method,params=None):
    response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in response:raise RuntimeError('rpc:'+method)
    return response['result']
def read():
    players=rpc('Player.GetActivePlayers')
    audio=rpc('Playlist.GetItems',dict(playlistid=0,limits=dict(start=0,end=1)))
    video=rpc('Playlist.GetItems',dict(playlistid=1,limits=dict(start=0,end=2),properties=['file','title','showtitle']))
    if players or audio['limits']['total']!=0 or video['limits']['total']!=1 or len(video.get('items',[]))!=1:
        raise RuntimeError('queue-boundary-changed')
    return video
first=read();time.sleep(.2)
if read()!=first:raise RuntimeError('queue-changed')
if TARGET.exists():raise RuntimeError('checkpoint-exists')
TARGET.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
with TARGET.open('x') as stream:
    stream.write(json.dumps(dict(kind='parked-video-playback-test',playlist=first),sort_keys=True)+'\n')
TARGET.chmod(0o600)
Path('/tmp/astertv-series-queue-checkpoint-result.json').write_text(json.dumps(dict(checkpoint=str(TARGET),count=1)))
