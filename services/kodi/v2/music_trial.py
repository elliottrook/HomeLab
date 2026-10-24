"""Capability-bounded HP trial player; never a general-purpose Kodi writer.

First trial requires an idle empty queue. Cooperative single-client operation,
not a transaction: unexpected queue/player state stops mutation and keeps the
checkpoint for investigation. Listening-history side effects are not rolled back.
"""
import json
from functools import wraps
from pathlib import Path
import threading
import time
import math

from music_queue import identities, propose
from queue_reader import QueueUnavailable, read_queue


class TrialUnavailable(ValueError):
    pass


def normal_playback_capability(path,*,host):
    if host!='AsterTV':return False
    try:
        value=json.loads(Path(path).read_text())
        return (isinstance(value,dict) and set(value)=={'enabled','queue_limit','host'}
                and value['enabled'] is True and type(value['queue_limit']) is int
                and value['queue_limit']==20000 and value['host']=='AsterTV')
    except (OSError,ValueError,TypeError):return False


def serialized(method):
    @wraps(method)
    def guarded(self,*args,**kwargs):
        with self.lock:return method(self,*args,**kwargs)
    return guarded


def capability(path, *, host, now):
    if host!='AsterTV':return ()
    try:
        data=json.loads(Path(path).read_text())
        if set(data)!={'song_ids','expires_at'}:return ()
        ids=identities(data['song_ids'],allow_empty=False)
        expiry=data['expires_at']
        if (len(ids)>3 or len(set(ids))!=len(ids) or type(expiry) is not int
                or not now<expiry<=now+1800):return ()
        return ids
    except (OSError,ValueError,TypeError):return ()


def save_empty_checkpoint(path, snapshot):
    if snapshot.song_ids or snapshot.current_index is not None:
        raise TrialUnavailable('idle-empty-queue-required')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    data=json.dumps({'song_ids':[],'current_index':None},sort_keys=True).encode()
    with path.open('xb') as output:output.write(data)
    path.chmod(0o600)
    if path.read_bytes()!=data:raise TrialUnavailable('checkpoint-verification-failed')
    return True


def validate_write(method, params, allowed, *, queue_limit=3):
    """Reject paths, unrelated playlists/players, extra options and >3 items."""
    if type(queue_limit) is not int or not 1<=queue_limit<=20000:
        raise TrialUnavailable('trial-write-denied')
    if not isinstance(params,dict):raise TrialUnavailable('trial-write-denied')
    if method in ('Playlist.Add','Playlist.Insert'):
        keys={'playlistid','item'} | ({'position'} if method=='Playlist.Insert' else set())
        if set(params)!=keys or type(params['playlistid']) is not int or params['playlistid']!=0:
            raise TrialUnavailable('trial-write-denied')
        if method=='Playlist.Insert' and (type(params['position']) is not int or not 0<=params['position']<=queue_limit):
            raise TrialUnavailable('trial-write-denied')
        items=params['item']
        if (not isinstance(items,list) or not 1<=len(items)<=min(queue_limit,200) or
                any(not isinstance(row,dict) or set(row)!={'songid'} or
                    type(row['songid']) is not int or row['songid'] not in allowed for row in items)):
            raise TrialUnavailable('trial-write-denied')
    elif method=='Playlist.Clear':
        if set(params)!={'playlistid'} or type(params['playlistid']) is not int or params['playlistid']!=0:
            raise TrialUnavailable('trial-write-denied')
    elif method=='Playlist.Remove':
        if (set(params)!={'playlistid','position'} or type(params['playlistid']) is not int
                or params['playlistid']!=0 or type(params['position']) is not int
                or not 0<=params['position']<queue_limit):
            raise TrialUnavailable('trial-write-denied')
    elif method=='Player.Open':
        item=params.get('item')
        if (set(params)!={'item'} or not isinstance(item,dict) or set(item)!={'playlistid','position'}
                or type(item['playlistid']) is not int or item['playlistid']!=0
                or type(item['position']) is not int or not 0<=item['position']<queue_limit):
            raise TrialUnavailable('trial-write-denied')
    elif method in ('Player.Stop','Player.PlayPause'):
        keys={'playerid','play'} if method=='Player.PlayPause' else {'playerid'}
        if (set(params)!=keys or type(params['playerid']) is not int or params['playerid']!=0
                or (method=='Player.PlayPause' and type(params['play']) is not bool)):
            raise TrialUnavailable('trial-write-denied')
    elif method=='Player.Seek':
        value=params.get('value')
        if (set(params)!={'playerid','value'} or type(params['playerid']) is not int
                or params['playerid']!=0 or not isinstance(value,dict)):
            raise TrialUnavailable('trial-write-denied')
        if set(value)=={'seconds'}:
            valid=type(value['seconds']) is int and 1<=abs(value['seconds'])<=10
        elif set(value)=={'percentage'}:
            percent=value['percentage']
            valid=type(percent) in (int,float) and math.isfinite(percent) and 0<=percent<100
        else:valid=False
        if not valid:
            raise TrialUnavailable('trial-write-denied')
    elif method=='Player.SetShuffle':
        if (set(params)!={'playerid','shuffle'} or type(params['playerid']) is not int
                or params['playerid']!=0 or type(params['shuffle']) is not bool):
            raise TrialUnavailable('trial-write-denied')
    else:raise TrialUnavailable('trial-write-denied')


class TrialPlayer:
    def __init__(self,rpc,allowed,checkpoint,*,sleep=time.sleep,queue_limit=3,queue_page_size=500):
        self.lock=threading.RLock()
        self.rpc=rpc;self.allowed=frozenset(identities(allowed,allow_empty=False));self.sleep=sleep
        self.queue_limit=queue_limit
        self.queue_page_size=queue_page_size
        if (type(queue_limit) is not int or not 1<=queue_limit<=20000
                or len(allowed)>queue_limit or len(self.allowed)!=len(allowed)):
            raise TrialUnavailable('three-song-capability-required')
        self.baseline=self.snapshot()
        if self.baseline.song_ids or self.baseline.current_index is not None:
            raise TrialUnavailable('idle-empty-queue-required')
        if checkpoint(self.baseline) is not True:raise TrialUnavailable('checkpoint-verification-failed')
        self.last=self.baseline;self.started=False;self.closed=False

    def snapshot(self):
        for attempt in range(3):
            try:return read_queue(self.rpc,page_size=self.queue_page_size)
            except QueueUnavailable as error:
                # A natural track boundary can fall between the two complete
                # reads. Retry only the read, never an Add/Open/other write.
                if str(error)!='queue-changed-during-read' or attempt==2:raise
                self.sleep(.05)

    @serialized
    def observe(self):
        if self.closed:raise TrialUnavailable('trial-closed')
        for attempt in range(3):
            state=self.snapshot()
            if state.song_ids!=self.last.song_ids:raise TrialUnavailable('external-queue-change')
            if state.current_index is not None:
                if not self.started:raise TrialUnavailable('unrelated-playback')
                item=self.rpc('Player.GetItem',{'playerid':0,'properties':[]}).get('item',{})
                identity=item.get('id')
                if (item.get('type')=='song' and (identity is None or
                        type(identity) is int and identity in self.allowed)
                        and identity!=state.song_ids[state.current_index] and attempt<2):
                    # Metadata can lag the position at a track boundary. Read
                    # again; never retry a write or accept mismatched identity.
                    self.sleep(.05);continue
                if (item.get('type')!='song' or type(identity) is not int
                        or identity!=state.song_ids[state.current_index]
                        or identity not in self.allowed):raise TrialUnavailable('unrelated-playback')
            self.last=state
            return state

    def write(self,method,params):
        validate_write(method,params,self.allowed,queue_limit=self.queue_limit)
        try:return self.rpc(method,params)
        except Exception:raise TrialUnavailable('trial-write-outcome-uncertain') from None

    @serialized
    def edit(self,action,selected,*,confirmed=False):
        selected=identities(selected,allow_empty=False)
        if any(i not in self.allowed for i in selected):raise TrialUnavailable('song-outside-trial')
        state=self.observe()
        if action=='replace' and not confirmed:raise TrialUnavailable('replacement-confirmation-required')
        if action=='replace' and state.current_index is not None:raise TrialUnavailable('stop-before-replace')
        plan=propose(state,selected,action=action)
        if len(plan.song_ids)>3:raise TrialUnavailable('three-item-trial-limit')
        if action=='replace':
            if state.song_ids:
                self.write('Playlist.Clear',{'playlistid':0})
                self.last=type(state)((),None)
                self.observe()
            self.write('Playlist.Add',{'playlistid':0,'item':[{'songid':i} for i in selected]})
        elif action=='append':
            self.write('Playlist.Add',{'playlistid':0,'item':[{'songid':i} for i in selected]})
        elif action=='next':
            self.write('Playlist.Insert',{'playlistid':0,'position':state.current_index+1,
                                         'item':[{'songid':i} for i in selected]})
        self.last=type(state)(plan.song_ids,state.current_index if action!='replace' else None)
        self.observe()

    def wait_for(self,predicate):
        for _ in range(40):
            try:
                if predicate():return
            except QueueUnavailable:pass  # Kodi can be between player states.
            self.sleep(.1)
        raise TrialUnavailable('player-transition-timeout')

    @serialized
    def play(self,selected,*,confirmed=False):
        self.edit('replace',selected,confirmed=confirmed)
        self.started=True
        self.write('Player.Open',{'item':{'playlistid':0,'position':0}})
        self.wait_for(lambda:self.observe().current_index is not None)
        modes=self.rpc('Player.GetProperties',{'playerid':0,'properties':['shuffled','repeat']})
        if modes.get('shuffled') is not False or modes.get('repeat')!='off':
            self.stop();raise TrialUnavailable('player-modes-not-supported-in-trial')

    @serialized
    def pause(self,play):
        if type(play) is not bool:raise TrialUnavailable('explicit-pause-state-required')
        if self.observe().current_index is None:raise TrialUnavailable('no-trial-playback')
        self.write('Player.PlayPause',{'playerid':0,'play':play})
        self.wait_for(lambda:self.rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')==(1 if play else 0))

    @serialized
    def stop(self):
        if self.observe().current_index is not None:
            expected=self.last.song_ids
            self.write('Player.Stop',{'playerid':0})
            def stopped():
                state=self.snapshot()
                if state.song_ids not in (expected,()):raise TrialUnavailable('external-queue-change')
                if state.current_index is not None:return False
                self.last=state;return True
            self.wait_for(stopped)
            # Existing Jellyfin monitor.py clears the queue 3s after OnStop.
            # Accept only that exact empty outcome of our own Stop, not a new
            # queue/stream. Do not fight it by silently re-adding the songs.
            settling=time.monotonic()
            for _ in range(40):
                try:state=self.snapshot()
                except QueueUnavailable as error:
                    if str(error)!='queue-changed-during-read':raise
                    self.sleep(.1);continue
                if state.current_index is not None:raise TrialUnavailable('unrelated-playback')
                if state.song_ids not in (expected,()):raise TrialUnavailable('external-queue-change')
                self.last=state
                # Track changes can have an earlier OnStop timer too. Don't
                # return on its first Clear while our latest Stop's 3s timer
                # could still clear a newly started idle queue afterwards.
                if not state.song_ids and time.monotonic()-settling>=3.2:break
                self.sleep(.1)
        self.started=False

    @serialized
    def close(self):
        if self.closed:return
        self.stop()
        if self.observe().song_ids:
            self.write('Playlist.Clear',{'playlistid':0});self.last=self.baseline
        self.observe();self.closed=True
