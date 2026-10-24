"""Approved HP-only full-album/shuffle test. Run over SSH, never production.

Starts idle/empty, checkpoints before writes, plays brief samples, restores the
empty queue. No titles, song IDs, URLs or credentials are printed to stdout.
"""
import codecs
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import sys
import threading
import time

assert os.uname().nodename=='AsterTV','HP only'
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_album import read_album
from music_catalogue import read_catalogue
from music_expanded_trial import ExpandedTrial,TrialCancelled,save_intent
from music_queue import nonholiday_shuffle
from music_trial import save_empty_checkpoint,validate_write
from queue_reader import read_queue

READS={'AudioLibrary.GetAlbums','AudioLibrary.GetArtists','AudioLibrary.GetSongs',
       'Player.GetActivePlayers','Player.GetProperties','Player.GetItem','Playlist.GetItems'}


def rpc(method,params=None):
    with socket.create_connection(('127.0.0.1',9090),timeout=30) as connection:
        connection.sendall((json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})+'\n').encode())
        raw='';decoder=codecs.getincrementaldecoder('utf-8')()
        while True:
            part=connection.recv(65536)
            if not part:raise RuntimeError('RPC closed')
            raw+=decoder.decode(part)
            while raw.strip():
                raw=raw.lstrip()
                try:reply,end=json.JSONDecoder().raw_decode(raw)
                except ValueError:break
                raw=raw[end:]
                if reply.get('id')==1:
                    if 'error' in reply:raise RuntimeError('RPC failed')
                    return reply['result']


def available():
    data=Path('/proc/meminfo').read_text().splitlines()
    return int(next(s.split()[1] for s in data if s.startswith('MemAvailable:')))


def private(path,data):
    with path.open('xb') as output:output.write(json.dumps(data,sort_keys=True).encode())
    path.chmod(0o600)
    assert json.loads(path.read_text())==json.loads(json.dumps(data))


root=Path('/storage/.aster-checkpoints/aster-music-expanded-trial-20261023')
root.mkdir(mode=0o700,exist_ok=True)
run=root/('run-'+str(time.time_ns()));run.mkdir(mode=0o700)
assert not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids
assert available()>=512*1024
baseline=read_queue(rpc)
save_empty_checkpoint(run/'queue-baseline.json',baseline)
started=time.monotonic();catalogue=read_catalogue(rpc)
allowed=tuple(catalogue.songs);expiry=time.monotonic()+1800
assert len(allowed)<=20000
private(run/'approval.json',{'song_ids':allowed,'queue_limit':20000,'expires_at':int(time.time())+1800})
print('Catalogue verified:',len(allowed),'songs; seconds:',round(time.monotonic()-started,2),flush=True)
allowed_set=frozenset(allowed)


def transport(method,params):
    if method not in READS:
        # Cleanup remains possible after expiry; new queue/play requests do not.
        if method not in ('Player.Stop','Playlist.Clear') and time.monotonic()>=expiry:
            raise RuntimeError('trial-expired')
        validate_write(method,params,allowed_set,queue_limit=20000)
    return rpc(method,params)


def trial(name,**kwargs):
    return ExpandedTrial(transport,allowed,lambda snapshot:save_empty_checkpoint(run/(name+'-baseline.json'),snapshot),
        queue_limit=20000,intent=lambda snapshot,**kw:save_intent(run/(name+'-intent.json'),snapshot,**kw),**kwargs)


def sample(player):
    first=rpc('Player.GetItem',{'playerid':0,'properties':[]})['item'].get('id')
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        props=rpc('Player.GetProperties',{'playerid':0,'properties':['time','speed']})
        t=props['time']
        if t['hours'] or t['minutes'] or t['seconds']>=1:
            assert props['speed']==1 and first in allowed_set
            return
        time.sleep(.1)
    raise AssertionError('player clock did not advance')


results=[]
try:
    # The already verified native trial album: find by title, not unstable ID.
    album=next(row for row in catalogue.albums.values() if row['label']=='20th Century Masters: The Millennium Collection: The Best of The Cranberries')
    expected=[i for i,s in catalogue.songs.items() if s.get('albumid')==album['albumid']]
    selection=read_album(rpc,album['albumid'],expected)
    player=trial('album')
    try:
        player.play(selection.song_ids,confirmed=True);sample(player)
        assert read_queue(rpc).song_ids==selection.song_ids
        results.append({'test':'full_album','tracks':len(selection.song_ids),'passed':True})
        print('PASS full album order, playback and advancing clock:',len(selection.song_ids),'tracks',flush=True)
        player.stop()
        assert player.saved.song_ids==selection.song_ids
        assert json.loads((run/'album-intent.json').read_text())['song_ids']==list(selection.song_ids)
        player.replay(confirmed=True);sample(player)
        assert read_queue(rpc).song_ids==selection.song_ids
        print('PASS explicit saved-intent replay after Jellyfin Stop cleanup',flush=True)
    finally:player.close()
    # Cancellation between queue batches must never issue Player.Open.
    cancel=threading.Event()
    def cancel_progress(done,total):cancel.set()
    player=trial('cancel-before',cancel=cancel,progress=cancel_progress)
    try:
        # Repeated, already proven playable album IDs exercise cancellation
        # across batches without treating orphan catalogue IDs as playable.
        cancel_ids=(selection.song_ids*40)[:430]
        try:player.play(cancel_ids,confirmed=True)
        except TrialCancelled:pass
        else:raise AssertionError('cancel ignored')
        assert not rpc('Player.GetActivePlayers') and read_queue(rpc)==baseline
        results.append({'test':'cancel_before_open','passed':True})
        print('PASS cancellation during batched staging restores original empty queue',flush=True)
    finally:player.close()
    # A cancellation immediately after an accepted Open must resolve its owned
    # player and stop; never return with an unresolved startup writer.
    cancel=threading.Event()
    def cancel_transport(method,params):
        result=transport(method,params)
        if method=='Player.Open':cancel.set()
        return result
    player=ExpandedTrial(cancel_transport,allowed,lambda s:save_empty_checkpoint(run/'cancel-after-baseline.json',s),
        queue_limit=20000,cancel=cancel,intent=lambda s,**kw:save_intent(run/'cancel-after-intent.json',s,**kw))
    try:
        try:player.play(selection.song_ids,confirmed=True)
        except TrialCancelled:pass
        else:raise AssertionError('cancel ignored')
        assert not rpc('Player.GetActivePlayers') and read_queue(rpc)==baseline
        results.append({'test':'cancel_after_open','passed':True})
        print('PASS cancellation after accepted Open resolves and stops owned playback',flush=True)
    finally:player.close()
    ids=nonholiday_shuffle(list(catalogue.songs.values()),list(catalogue.albums.values()),expected_total=len(allowed),seed=20261023)
    assert set(ids)==set(catalogue.shuffle_summary['eligible_ids']) and len(set(ids))==len(ids)
    missing_credits=sum(not catalogue.songs[i].get('artistid') for i in ids)
    if '--startup-only' in sys.argv or missing_credits:
        print('Full shuffle deferred: missing artist links require a separate library repair decision;',
              len(ids),'eligible;',missing_credits,'eligible tracks have unavailable artist links',flush=True)
        results.append({'test':'full_nonholiday_shuffle','passed':False,'blocked':'library-artist-link-integrity',
                        'eligible':len(ids),'excluded':len(allowed)-len(ids),'eligible_artist_link_unavailable':missing_credits})
        sys.exit(0)
    count=[0];minimum=[available()]
    def progress(done,total):
        minimum[0]=min(minimum[0],available());assert minimum[0]>=512*1024,'low-memory-stop'
        if done//2000>count[0]:
            count[0]=done//2000;print('Shuffle staged:',done,'/',total,flush=True)
    player=trial('shuffle',progress=progress);start=time.monotonic()
    try:
        player.play(ids,confirmed=True);sample(player)
        assert read_queue(rpc).song_ids==ids
        elapsed=round(time.monotonic()-start,2)
        results.append({'test':'full_nonholiday_shuffle','tracks':len(ids),'excluded':len(allowed)-len(ids),
                        'seconds':elapsed,'minimum_available_kib':minimum[0],
                        'harness_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                        'order_sha256':hashlib.sha256(json.dumps(ids).encode()).hexdigest(),'passed':True})
        print('PASS full shuffle exact membership/order, exclusions and brief playback:',len(ids),'tracks;',elapsed,'seconds',flush=True)
    finally:player.close()
finally:
    assert not rpc('Player.GetActivePlayers') and read_queue(rpc)==baseline,'recovery required'
    private(run/'results.json',{'results':results,'original_queue_restored':True})
    print('Verified: HP idle, original empty queue restored; private intent and evidence retained',flush=True)
