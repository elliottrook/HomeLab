"""Read-only HP local cached-cover decoder proof; no art URL/path output."""
import importlib.util,json,os,re,sys,time
from pathlib import Path
import xbmc

if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_atmosphere import sample,DEFAULT

request=dict(jsonrpc='2.0',id=1,method='AudioLibrary.GetAlbums',params=dict(properties=['thumbnail'],limits=dict(start=0,end=20)))
response=json.loads(xbmc.executeJSONRPC(json.dumps(request)))
if 'error' in response:raise RuntimeError('album-read-failed')
start=time.monotonic();colour=None
for album in response['result'].get('albums',[]):
    colour=sample(album.get('thumbnail'),'/storage/.kodi/userdata/Database/Textures13.db','/storage/.kodi/userdata/Thumbnails')
    if colour is not None:break
if colour is not None and not re.fullmatch('ff[0-9a-f]{6}',colour):raise RuntimeError('invalid-colour')
result=dict(checks_enforced=True,python_optimization=sys.flags.optimize,
    decoder_available=importlib.util.find_spec('PIL') is not None,
    cached_art_sampled=colour is not None,colour=colour or DEFAULT,
    seconds=round(time.monotonic()-start,3),cache_only=True,no_network_fetch=True,
    no_player_queue_or_server_writes=True)
path=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/('atmosphere-'+str(time.time_ns())+'.json')
with path.open('x') as f:json.dump(result,f)
path.chmod(0o600)
