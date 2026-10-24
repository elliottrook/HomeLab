"""Explicit HP-only expanded trial. No automatic recovery or background replay."""
import json
import os
from pathlib import Path
import tempfile
import threading

from music_queue import identities, propose, propose_remove, propose_clear, QueueSnapshot
from music_trial import TrialPlayer, TrialUnavailable, serialized


class TrialCancelled(TrialUnavailable):
    pass


def expanded_capability(path, *, host, now):
    if host!='AsterTV':return (),3
    try:
        data=json.loads(Path(path).read_text())
        if set(data) not in ({'song_ids','expires_at'},{'song_ids','expires_at','queue_limit'}):return (),3
        ids=identities(data['song_ids'],allow_empty=False)
        limit=data.get('queue_limit',3);expiry=data['expires_at']
        if (type(limit) is not int or not 1<=limit<=20000 or len(ids)>limit
                or len(set(ids))!=len(ids) or type(expiry) is not int
                or not now<expiry<=now+1800):return (),3
        return ids,limit
    except (OSError,ValueError,TypeError):return (),3


def save_intent(path, snapshot, *, status):
    """Atomic private journal: song IDs/order only, never paths or credentials."""
    path=Path(path)
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    data=json.dumps({'song_ids':snapshot.song_ids,'current_index':snapshot.current_index,
                     'status':status},sort_keys=True).encode()
    fd,name=tempfile.mkstemp(prefix='.intent-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as output:
            output.write(data);output.flush();os.fsync(output.fileno())
        if Path(name).read_bytes()!=data:raise TrialUnavailable('intent-verification-failed')
        os.replace(name,path)
    finally:
        if Path(name).exists():Path(name).unlink()


class ExpandedTrial(TrialPlayer):
    def __init__(self,*args,intent,cancel=None,progress=None,**kwargs):
        # GetItems copies Kodi's whole playlist before applying page limits.
        # Read the bounded trial queue in one page, still twice, rather than
        # paying that full-copy cost once for every 500-item slice.
        kwargs.setdefault('queue_page_size',min(kwargs.get('queue_limit',3),20000))
        super().__init__(*args,**kwargs)
        self.intent=intent
        self.cancel=cancel if cancel is not None else threading.Event()
        self.progress=progress or (lambda done,total:None)
        self.saved=self.baseline

    def check_cancel(self):
        if self.cancel.is_set():raise TrialCancelled('startup-cancelled')

    @serialized
    def remove(self,position,*,expected_queue):
        self.check_cancel();state=self.observe()
        if state.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
        try:plan=propose_remove(state,position)
        except ValueError:
            raise TrialUnavailable('queue-remove-refused') from None
        speed=None
        if state.current_index is not None:
            speed=self.rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')
            if type(speed) is not int or speed not in (0,1):raise TrialUnavailable('player-state-unavailable')
        self.intent(QueueSnapshot(plan.song_ids,plan.current_index),status='remove-requested')
        self.check_cancel()
        if self.observe().fingerprint!=state.fingerprint:raise TrialUnavailable('queue-preview-stale')
        self.write('Playlist.Remove',{'playlistid':0,'position':position})
        self.last=QueueSnapshot(plan.song_ids,plan.current_index)
        actual=self.observe()
        if actual.current_index!=plan.current_index:raise TrialUnavailable('queue-remove-state-changed')
        if speed is not None and self.rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')!=speed:
            raise TrialUnavailable('queue-remove-state-changed')
        self.saved=actual;self.intent(actual,status='edited')
        return actual

    @serialized
    def clear(self,*,expected_queue,confirmed=False):
        self.check_cancel();state=self.observe()
        if state.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
        try:plan=propose_clear(state,confirmed=confirmed)
        except ValueError:raise TrialUnavailable('queue-clear-refused') from None
        self.intent(QueueSnapshot((),None),status='clear-requested')
        self.check_cancel()
        if state.song_ids:self.write('Playlist.Clear',{'playlistid':0})
        self.last=QueueSnapshot(plan.song_ids,None)
        actual=self.observe();self.saved=actual;self.intent(actual,status='cleared')
        return actual

    @serialized
    def edit(self,action,selected,*,confirmed=False):
        selected=identities(selected,allow_empty=False)
        if any(i not in self.allowed for i in selected):raise TrialUnavailable('song-outside-trial')
        state=self.observe()
        if action=='replace' and not confirmed:raise TrialUnavailable('replacement-confirmation-required')
        if action=='replace' and state.current_index is not None:raise TrialUnavailable('stop-before-replace')
        plan=propose(state,selected,action=action)
        if len(plan.song_ids)>self.queue_limit:raise TrialUnavailable('expanded-queue-limit')
        self.check_cancel()
        # Durable requested order exists before the first write, including a
        # cancelled or uncertain write. Never silently replay it on restart.
        self.saved=type(state)(plan.song_ids,plan.current_index)
        self.intent(self.saved,status='staging')
        if action=='replace' and state.song_ids:
            self.write('Playlist.Clear',{'playlistid':0})
            self.last=type(state)((),None);self.observe()
        for offset in range(0,len(selected),200):
            self.check_cancel()
            chunk=selected[offset:offset+200]
            before=self.observe()
            params={'playlistid':0,'item':[{'songid':i} for i in chunk]}
            if action=='next':
                position=state.current_index+1+offset
                params['position']=position
                expected=before.song_ids[:position]+chunk+before.song_ids[position:]
                method='Playlist.Insert'
            else:
                expected=before.song_ids+chunk;method='Playlist.Add'
            self.write(method,params)
            self.last=type(state)(expected,before.current_index)
            self.observe()  # Two exact, complete reads after every bounded write.
            self.progress(offset+len(chunk),len(selected))
        if self.last.song_ids!=plan.song_ids:raise TrialUnavailable('staging-verification-failed')
        self.saved=type(state)(plan.song_ids,plan.current_index)
        self.intent(self.saved,status='staged')

    @serialized
    def play(self,selected,*,confirmed=False):
        try:
            self.edit('replace',selected,confirmed=confirmed)
            self.check_cancel()
            self.started=True
            self.write('Player.Open',{'item':{'playlistid':0,'position':0}})
            # A request may already be in flight when Cancel arrives. Resolve
            # its owned player before cleanup; don't abandon an RPC worker.
            self.wait_for(lambda:self.observe().current_index is not None)
            self.check_cancel()
            modes=self.rpc('Player.GetProperties',{'playerid':0,'properties':['shuffled','repeat']})
            if modes.get('shuffled') is not False or modes.get('repeat')!='off':
                self.stop();raise TrialUnavailable('player-modes-not-supported-in-trial')
            self.intent(self.observe(),status='playing')
        except TrialCancelled:
            self.stop()
            if self.observe().song_ids:
                self.write('Playlist.Clear',{'playlistid':0});self.last=self.baseline
            self.observe()
            self.intent(self.saved,status='cancelled')
            raise

    @serialized
    def stop(self):
        state=self.observe()
        if state.song_ids:
            # A cancelled partial stage must not replace the durable full
            # requested order with only the already inserted prefix.
            if state.song_ids==self.saved.song_ids:self.saved=state
            self.intent(self.saved,status='stopping')
        super().stop()
        self.intent(self.saved,status='stopped')

    @serialized
    def replay(self,*,confirmed=False):
        """Explicit start of saved intent; never called automatically on Stop."""
        selected=self.saved.song_ids
        if not selected:raise TrialUnavailable('no-saved-queue-intent')
        self.play(selected,confirmed=confirmed)
