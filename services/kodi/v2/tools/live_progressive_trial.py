"""HP-only in-process progressive trial; samples briefly, pauses during fill."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import hashlib,json,os,sys,time
from pathlib import Path
import xbmc
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_catalogue import read_catalogue
from music_queue import nonholiday_shuffle
from music_expanded_trial import ExpandedTrial,save_intent
from music_progressive import ProgressiveSession
from music_trial import save_empty_checkpoint,validate_write
from queue_reader import read_queue


def rpc(method,params=None):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})))
    if 'error' in reply:raise RuntimeError('native-rpc-failed')
    return reply['result']


def snapshot():return read_queue(rpc,page_size=20000)
def private(path,data):
    with path.open('x') as output:json.dump(data,output,sort_keys=True)
    path.chmod(0o600)
def resource_check():
    n=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))
    if n<512*1024:raise RuntimeError('low-memory-stop')
def seconds():
    t=rpc('Player.GetProperties',{'playerid':0,'properties':['time']})['time']
    return t['hours']*3600+t['minutes']*60+t['seconds']+t['milliseconds']/1000


_require((not rpc('Player.GetActivePlayers') and not snapshot().song_ids), ('native-check-failed'))
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
root.mkdir(mode=0o700,exist_ok=True)
run=root/('run-'+str(time.time_ns()));run.mkdir(mode=0o700)
baseline=snapshot();save_empty_checkpoint(run/'baseline.json',baseline)
catalogue=read_catalogue(rpc);allowed=frozenset(catalogue.songs)
ids=nonholiday_shuffle(list(catalogue.songs.values()),list(catalogue.albums.values()),expected_total=len(allowed),seed=20261023)
_require((25<len(ids)<=20000 and set(ids)==set(catalogue.shuffle_summary['eligible_ids'])), ('native-check-failed'))
expiry=time.monotonic()+1800
private(run/'grant.json',{'song_ids':sorted(allowed),'queue_limit':20000,'expires_at':int(time.time())+1800})
def transport(method,params):
    if method.startswith('Playlist.') and method!='Playlist.GetItems' or method in ('Player.Open','Player.Stop','Player.PlayPause'):
        if method not in ('Player.Stop','Playlist.Clear') and time.monotonic()>=expiry:raise RuntimeError('expired')
        validate_write(method,params,allowed,queue_limit=20000)
    return rpc(method,params)
def make(name):
    engine=ExpandedTrial(transport,sorted(allowed),lambda s:save_empty_checkpoint(run/(name+'-baseline.json'),s),
        queue_limit=20000,intent=lambda s,**kw:save_intent(run/(name+'-intent.json'),s,**kw))
    return ProgressiveSession(engine,resource_check=resource_check)
def sample():
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if seconds()>=1:return
        xbmc.sleep(50)
    raise AssertionError('clock-not-advancing')

results=[]
for name in ('exit-during-fill','complete-fill'):
    session=make(name)
    try:
        start=time.monotonic();session.start(ids,confirmed=True)
        first=time.monotonic()-start
        sample();session.pause(False)
        if name=='exit-during-fill':
            _require((session.status()['loaded']<len(ids) and session.status()['writer_active']), ('native-check-failed'))
            exit_start=time.monotonic();session.close()
            _require((not session.status()['writer_active'] and snapshot()==baseline and not rpc('Player.GetActivePlayers')), ('native-check-failed'))
            results.append({'test':name,'first_player_seconds':round(first,3),'exit_seconds':round(time.monotonic()-exit_start,3),'passed':True})
        else:
            marker=0;deadline=time.monotonic()+900
            while session.status()['writer_active']:
                if time.monotonic()>deadline:raise AssertionError('fill-timeout')
                state=session.status();bucket=state['loaded']//2000
                if bucket>marker:
                    marker=bucket;private(run/('progress-'+str(state['loaded'])+'.json'),state)
                xbmc.sleep(100)
            _require((session.status()['phase']=='ready'), (session.status()['error']))
            _require((snapshot().song_ids==ids), ('native-check-failed'))
            old=seconds();session.pause(True)
            deadline=time.monotonic()+10
            while seconds()<old+1:
                _require((time.monotonic()<deadline), ('native-check-failed'));xbmc.sleep(50)
            results.append({'test':name,'first_player_seconds':round(first,3),'fill_seconds':round(time.monotonic()-start,3),
                'tracks':len(ids),'excluded':catalogue.shuffle_summary['excluded'],
                'order_sha256':hashlib.sha256(json.dumps(ids).encode()).hexdigest(),'passed':True})
    finally:
        session.close()
        _require((not rpc('Player.GetActivePlayers') and snapshot()==baseline), ('native-check-failed'))
private(run/'results.json',{'results':results,'original_queue_restored':True,'transport':'in-process',
    'checks_enforced':True,'python_optimization':sys.flags.optimize})
