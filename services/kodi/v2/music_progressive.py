"""Single-owner progressive loading; no GUI calls or detached queue writers."""
import threading

from music_queue import QueueSnapshot,identities
from music_trial import TrialUnavailable
from music_expanded_trial import TrialCancelled


class ProgressiveSession:
    def __init__(self,engine,*,first_batch=25,fill_batch=50,resource_check=None):
        if type(first_batch) is not int or not 1<=first_batch<=200:
            raise TrialUnavailable('invalid-starting-batch')
        if type(fill_batch) is not int or not 1<=fill_batch<=200:
            raise TrialUnavailable('invalid-fill-batch')
        self.engine=engine;self.first_batch=first_batch
        self.fill_batch=fill_batch
        self.resource_check=resource_check or (lambda:None)
        self.lock=threading.Lock();self.worker=None
        self.lifecycle=threading.Lock()
        self.control_pending=threading.Event()
        self.selected=();self.done=0;self.phase='idle';self.error=None;self.closed=False
        self.original_intent=engine.intent
        engine.intent=self.record

    def record(self,snapshot,*,status):
        # Persist the complete requested order even while native Kodi contains
        # only its prefix. Never silently replay that intent after restart.
        intended=QueueSnapshot(self.selected,snapshot.current_index) if self.selected else snapshot
        self.original_intent(intended,status=status)

    def status(self):
        with self.lock:
            return dict(phase=self.phase,loaded=self.done,total=len(self.selected),
                        error=self.error,writer_active=bool(self.worker and self.worker.is_alive()))

    def update(self,**values):
        with self.lock:
            for key,value in values.items():setattr(self,key,value)

    def start(self,selected,*,confirmed=False):
        with self.lifecycle:self.start_locked(selected,confirmed=confirmed)

    def start_locked(self,selected,*,confirmed=False):
        if self.phase!='idle' or self.closed:raise TrialUnavailable('session-already-started')
        ids=identities(selected,allow_empty=False)
        if (not confirmed or len(ids)>self.engine.queue_limit
                or any(i not in self.engine.allowed for i in ids)):
            raise TrialUnavailable('unconfirmed-or-outside-grant')
        self.selected=ids;self.update(phase='starting')
        try:
            self.resource_check()
            self.engine.play(ids[:self.first_batch],confirmed=True)
            self.update(done=min(len(ids),self.first_batch),phase='loading')
            self.worker=threading.Thread(target=self.fill,name='AsterMusicQueueFill')
            self.worker.start()
        except BaseException:
            self.update(phase='failed');raise

    def fill(self):
        try:
            for offset in range(self.done,len(self.selected),self.fill_batch):
                self.engine.check_cancel();self.resource_check()
                self.engine.edit('append',self.selected[offset:offset+self.fill_batch])
                self.update(done=min(len(self.selected),offset+self.fill_batch))
                # Yield between batches so a pending Pause/Resume can acquire
                # the engine lock; don't let a fast filler starve controls.
                self.engine.cancel.wait(.01)
                while self.control_pending.is_set():
                    if self.engine.cancel.wait(.01):self.engine.check_cancel()
            self.engine.check_cancel()
            if self.engine.observe().song_ids!=self.selected:
                raise TrialUnavailable('progressive-order-verification-failed')
            self.update(phase='ready')
        except TrialCancelled:self.update(phase='cancelled')
        except Exception as error:
            # Sanitised code only; never print arbitrary transport exceptions.
            code=str(error) if isinstance(error,TrialUnavailable) else 'progressive-fill-failed'
            self.update(phase='failed',error=code)

    def pause(self,play):
        if self.closed or self.engine.cancel.is_set():raise TrialUnavailable('session-closed')
        self.control_pending.set()
        try:
            with self.engine.lock:
                if self.closed or self.engine.cancel.is_set():raise TrialUnavailable('session-closed')
                self.engine.pause(play)
        finally:self.control_pending.clear()

    def select(self,position):
        if type(position) is not int or not 0<=position<len(self.selected):raise TrialUnavailable('invalid-queue-position')
        self.control_pending.set()
        try:self.select_locked(position)
        finally:self.control_pending.clear()

    def select_locked(self,position):
        with self.engine.lock:
            if self.closed or self.engine.cancel.is_set():raise TrialUnavailable('session-closed')
            state=self.engine.observe()
            if state.current_index is None:raise TrialUnavailable('no-trial-playback')
            if position>=len(state.song_ids):raise TrialUnavailable('selected-track-not-loaded')
            if state.song_ids[position]!=self.selected[position]:raise TrialUnavailable('external-queue-change')
            self.engine.write('Player.Open',{'item':{'playlistid':0,'position':position}})
            self.engine.wait_for(lambda:self.engine.observe().current_index==position)
            self.record(self.engine.observe(),status='playing')

    def close(self):
        # Set cancellation without taking the engine lock; a batch may own it.
        # Joining happens before Stop/Clear, so no late append can revive it.
        self.engine.cancel.set()
        with self.lifecycle:
            if self.closed:return
            if self.worker:
                if self.worker is threading.current_thread():raise TrialUnavailable('cannot-join-own-writer')
                self.worker.join()
            self.engine.close()
            self.update(closed=True,phase='closed')
