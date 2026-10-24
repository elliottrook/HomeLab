"""Explicit HP-only expanded trial. No automatic recovery or background replay."""
import json
import os
from pathlib import Path
import tempfile
import threading
from collections import Counter

from music_queue import identities, propose, propose_remove, propose_clear, QueueSnapshot
from music_trial import TrialPlayer, TrialUnavailable, serialized
from music_scrub import clock_milliseconds


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
        self.shuffled=False;self.shuffle_original=None;self.shuffle_origin_index=None
        self.shuffle_native_index=None
        self.shuffle_uncertain=False;self.shuffle_request_sent=False

    def check_cancel(self):
        if self.shuffle_uncertain:raise TrialUnavailable('shuffle-recovery-required')
        if self.cancel.is_set():raise TrialCancelled('startup-cancelled')

    @serialized
    def pause(self,play):
        self.check_cancel();super().pause(play)

    @serialized
    def select(self,position,*,expected_queue):
        """Navigate an existing owned occurrence, not open/replace a playlist."""
        self.check_cancel();state=self.observe()
        if state.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
        if (type(position) is not int or not 0<=position<len(state.song_ids)
                or state.current_index is None):raise TrialUnavailable('invalid-queue-position')
        if position==state.current_index:
            self.pause(True);return self.observe()
        if self.observe().fingerprint!=state.fingerprint:raise TrialUnavailable('queue-preview-stale')
        self.write('Player.GoTo',{'playerid':0,'to':position})
        self.wait_for(lambda:self.observe().current_index==position)
        actual=self.observe();self.saved=actual;self.intent(actual,status='playing')
        return actual

    @serialized
    def next_track(self,*,expected_queue):
        state=self.observe()
        if state.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
        if state.current_index is None:raise TrialUnavailable('no-trial-playback')
        if state.current_index+1>=len(state.song_ids):raise TrialUnavailable('end-of-queue')
        return self.select(state.current_index+1,expected_queue=state.fingerprint)

    @serialized
    def start_queued(self,*,expected_queue,confirmed=False):
        """Start the verified idle queue without replacing or duplicating it."""
        self.check_cancel();state=self.observe()
        if not confirmed:raise TrialUnavailable('replacement-confirmation-required')
        if state.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
        if state.current_index is not None or not state.song_ids:raise TrialUnavailable('idle-queued-music-required')
        self.intent(state,status='start-queued-requested');self.started=True
        self.write('Player.Open',{'item':{'playlistid':0,'position':0}})
        self.wait_for(lambda:self.observe().current_index is not None)
        self.check_cancel()
        modes=self.rpc('Player.GetProperties',{'playerid':0,'properties':['shuffled','repeat']})
        if modes.get('shuffled') is not False or modes.get('repeat')!='off':
            self.stop();raise TrialUnavailable('player-modes-not-supported-in-trial')
        self.saved=self.observe();self.intent(self.saved,status='playing')

    @serialized
    def remove(self,position,*,expected_queue):
        self.check_cancel();state=self.observe()
        if self.shuffled:raise TrialUnavailable('turn-shuffle-off-before-editing')
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
        if self.shuffled:raise TrialUnavailable('turn-shuffle-off-before-editing')
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
        if self.shuffle_uncertain:raise TrialUnavailable('shuffle-recovery-required')
        if self.shuffled:
            ended=self.snapshot()
            if ended.current_index is None:self.restore_idle_shuffle(ended)
            else:self.set_shuffle(False,expected_queue=self.observe().fingerprint,confirmed=True,cleanup=True)
        state=self.observe()
        if state.song_ids:
            # A cancelled partial stage must not replace the durable full
            # requested order with only the already inserted prefix.
            if state.song_ids==self.saved.song_ids:self.saved=state
            self.intent(self.saved,status='stopping')
        super().stop()
        self.intent(self.saved,status='stopped')

    def restore_idle_shuffle(self,state):
        """Ended/owned-stopped queue: restore only our mode, never restart audio.

        The existing Jellyfin OnStop monitor may already have cleared it. An
        empty queue is safe here; any different nonempty queue is not ours.
        """
        if not self.started or state.current_index is not None or state.song_ids not in (self.last.song_ids,()):
            raise TrialUnavailable('external-queue-change')
        props=self.rpc('Player.GetProperties',{'playerid':0,'properties':['playlistid','shuffled']})
        if props.get('playlistid')!=0 or type(props.get('shuffled')) is not bool:
            raise TrialUnavailable('external-player-mode-change')
        try:
            if props['shuffled']:
                self.intent(state,status='ended-shuffle-off-requested')
                self.shuffle_request_sent=True
                self.write('Player.SetShuffle',{'playerid':0,'shuffle':False})
            actual=self.snapshot()
            mode=self.rpc('Player.GetProperties',{'playerid':0,'properties':['shuffled']})
            if (actual.current_index is not None or actual.song_ids not in (self.shuffle_original,())
                    or mode.get('shuffled') is not False):raise TrialUnavailable('ended-shuffle-restore-unverified')
            self.last=actual;self.shuffled=False;self.shuffle_request_sent=False
            self.saved=QueueSnapshot(self.shuffle_original,None)
            self.intent(actual,status='ended-shuffle-restored')
        except Exception:
            if self.shuffle_request_sent:self.shuffle_uncertain=True
            raise

    @serialized
    def set_shuffle(self,enabled,*,expected_queue,confirmed=False,cleanup=False):
        if self.shuffle_uncertain:raise TrialUnavailable('shuffle-recovery-required')
        self.shuffle_request_sent=False
        try:
            result=self._set_shuffle_change(enabled,expected_queue=expected_queue,confirmed=confirmed,cleanup=cleanup)
            self.shuffle_request_sent=False;return result
        except Exception:
            if self.shuffle_request_sent:self.shuffle_uncertain=True
            raise

    def _set_shuffle_change(self,enabled,*,expected_queue,confirmed=False,cleanup=False):
        """Single native mode change; preserve the playing song, time and pause.

        Native Kodi keeps occurrence order internally and restores it on Off.
        Never clear/reopen or guess a permutation. Edits are refused until Off.
        """
        if type(enabled) is not bool or confirmed is not True:raise TrialUnavailable('shuffle-confirmation-required')
        if cleanup and enabled:raise TrialUnavailable('invalid-shuffle-cleanup')
        if not cleanup:self.check_cancel()
        before=self.observe()
        if before.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
        if before.current_index is None or len(before.song_ids)<2:raise TrialUnavailable('shuffle-needs-playing-queue')
        props=self.rpc('Player.GetProperties',{'playerid':0,'properties':['speed','time','shuffled','repeat']})
        if (props.get('shuffled') is not self.shuffled or props.get('repeat')!='off'
                or type(props.get('speed')) is not int or props['speed'] not in (0,1)):
            raise TrialUnavailable('external-player-mode-change')
        if enabled==self.shuffled:return before
        if props['speed']==0:
            # Kodi can report speed zero before the last buffered clock update
            # settles. Establish a stable paused clock *before* the mode write.
            samples=[clock_milliseconds(props.get('time'))]
            for _ in range(15):
                self.sleep(.1)
                sample=self.rpc('Player.GetProperties',{'playerid':0,'properties':['speed','time','shuffled','repeat']})
                if sample.get('speed')!=0 or sample.get('shuffled') is not self.shuffled or sample.get('repeat')!='off':
                    raise TrialUnavailable('external-player-mode-change')
                samples=(samples+[clock_milliseconds(sample.get('time'))])[-4:]
                props=sample
                if len(samples)==4 and max(samples)-min(samples)<=250:break
            else:raise TrialUnavailable('paused-clock-not-stable')
        if enabled:
            self.shuffle_original=before.song_ids;self.shuffle_origin_index=before.current_index
        original=self.shuffle_original
        if original is None:raise TrialUnavailable('shuffle-original-unavailable')
        self.intent(before,status='shuffle-on-requested' if enabled else 'shuffle-off-requested')
        if self.observe().fingerprint!=before.fingerprint:raise TrialUnavailable('queue-preview-stale')
        self.shuffle_request_sent=True
        self.write('Player.SetShuffle',{'playerid':0,'shuffle':enabled})
        # Accept a reordered snapshot only for this one explicitly requested
        # mode change, with the exact same multiset including duplicates.
        after=self.snapshot()
        if (after.current_index is None or Counter(after.song_ids)!=Counter(before.song_ids)
                or after.song_ids[after.current_index]!=before.song_ids[before.current_index]
                or not enabled and after.song_ids!=original):
            raise TrialUnavailable('shuffle-order-unverified')
        if not enabled and before.current_index==self.shuffle_native_index and after.current_index!=self.shuffle_origin_index:
            raise TrialUnavailable('shuffle-occurrence-unverified')
        self.last=after;self.shuffled=enabled
        if enabled:self.shuffle_native_index=after.current_index
        actual=self.rpc('Player.GetProperties',{'playerid':0,'properties':['speed','time','shuffled']})
        if actual.get('speed')!=props['speed'] or actual.get('shuffled') is not enabled:
            raise TrialUnavailable('shuffle-player-state-unverified')
        if props['speed']==0 and abs(clock_milliseconds(actual.get('time'))-clock_milliseconds(props.get('time')))>500:
            raise TrialUnavailable('shuffle-playback-clock-changed')
        self.observe();self.saved=after
        self.intent(after,status='shuffled' if enabled else 'ordered')
        return after

    @serialized
    def replay(self,*,confirmed=False):
        """Explicit start of saved intent; never called automatically on Stop."""
        selected=self.saved.song_ids
        if not selected:raise TrialUnavailable('no-saved-queue-intent')
        self.play(selected,confirmed=confirmed)
