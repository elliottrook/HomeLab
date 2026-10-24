"""Single-owner progressive loading; no GUI calls or detached queue writers."""
import threading

from music_queue import QueueSnapshot,identities
from music_trial import TrialUnavailable
from music_expanded_trial import TrialCancelled
from music_scrub import ScrubPreview,clock_milliseconds


def clock_label(value):
    if type(value) is not int or value<0:raise TrialUnavailable('playback-clock-unavailable')
    seconds=value//1000;hours,seconds=divmod(seconds,3600);minutes,seconds=divmod(seconds,60)
    return f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes}:{seconds:02}'


def verify_seek_state(engine,before,properties):
    """PAPlayer resumes on seek; restore pause only for the same occurrence."""
    actual=engine.rpc('Player.GetProperties',{'playerid':0,'properties':['playlistid','position','speed']})
    item=engine.rpc('Player.GetItem',{'playerid':0,'properties':[]}).get('item',{})
    if (actual.get('playlistid')!=0 or actual.get('position')!=before.current_index
            or item.get('type')!='song' or item.get('id')!=before.song_ids[before.current_index]):
        raise TrialUnavailable('seek-state-changed')
    if properties['speed']==0 and actual.get('speed')==1:
        engine.write('Player.PlayPause',{'playerid':0,'play':False})
        engine.wait_for(lambda:engine.rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')==0)
    after=engine.observe()
    speed=engine.rpc('Player.GetProperties',{'playerid':0,'properties':['speed']}).get('speed')
    if after.current_index!=before.current_index or speed!=properties['speed']:
        raise TrialUnavailable('seek-state-changed')


def seek_owned(engine,selected,preview):
    """One seek, exact owned queue/occurrence/duration; no retries or GUI calls."""
    if not isinstance(preview,ScrubPreview):raise TrialUnavailable('invalid-scrub-preview')
    with engine.lock:
        engine.check_cancel()
        if engine.closed:raise TrialUnavailable('session-closed')
        before=engine.observe()
        if (before.current_index!=preview.index or before.song_ids[preview.index]!=preview.song_id
                or QueueSnapshot(selected,before.current_index).fingerprint!=preview.queue_fingerprint):
            raise TrialUnavailable('scrub-preview-stale')
        props=engine.rpc('Player.GetProperties',{'playerid':0,'properties':['totaltime','canseek','speed']})
        if (props.get('canseek') is not True or type(props.get('speed')) is not int or props['speed'] not in (0,1)
                or clock_milliseconds(props.get('totaltime'))!=preview.duration_ms):
            raise TrialUnavailable('scrub-preview-stale')
        if engine.observe().current_index!=before.current_index:raise TrialUnavailable('track-changed-before-seek')
        engine.check_cancel()
        engine.write('Player.Seek',{'playerid':0,'value':{'percentage':preview.percentage}})
        verify_seek_state(engine,before,props)


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
            self.engine.select(position,expected_queue=state.fingerprint)
            self.record(self.engine.observe(),status='playing')

    def editable(self):
        if self.closed or self.engine.cancel.is_set():raise TrialUnavailable('session-closed')
        if self.status()['phase']!='ready' or self.status()['writer_active']:
            raise TrialUnavailable('queue-still-loading')

    def remove(self,position,*,expected_queue):
        self.control_pending.set()
        try:
            with self.engine.lock:
                self.editable()
                # The edit intent must be the requested new order, not the
                # full starting order normally supplied by record().
                previous=self.engine.intent;self.engine.intent=self.original_intent
                try:state=self.engine.remove(position,expected_queue=expected_queue)
                finally:self.engine.intent=previous
                self.selected=state.song_ids
                self.update(done=len(self.selected));self.record(state,status='edited')
                return state
        finally:self.control_pending.clear()

    def set_shuffle(self,enabled,*,expected_queue,confirmed=False):
        self.control_pending.set()
        try:
            with self.engine.lock:
                self.editable()
                previous=self.engine.intent;self.engine.intent=self.original_intent
                try:state=self.engine.set_shuffle(enabled,expected_queue=expected_queue,confirmed=confirmed)
                finally:self.engine.intent=previous
                self.selected=state.song_ids;self.record(state,status='shuffled' if enabled else 'ordered')
                return state
        finally:self.control_pending.clear()

    def clear(self,*,expected_queue,confirmed=False):
        if confirmed is not True:raise TrialUnavailable('clear-confirmation-required')
        self.control_pending.set()
        try:
            with self.engine.lock:
                self.editable();state=self.engine.observe()
                if state.fingerprint!=expected_queue:raise TrialUnavailable('queue-preview-stale')
                # Explicit UI confirmation covers Stop as well as Clear.
                # No implicit Stop is hidden in the idle-only clear planner.
                self.engine.stop()
                idle=self.engine.observe()
                previous=self.engine.intent;self.engine.intent=self.original_intent
                try:result=self.engine.clear(expected_queue=idle.fingerprint,confirmed=True)
                finally:self.engine.intent=previous
                self.selected=();self.update(done=0,phase='cleared')
                return result
        finally:self.control_pending.clear()

    def seek(self,offset):
        if type(offset) is not int or offset not in (-10,10):raise TrialUnavailable('invalid-seek-step')
        self.control_pending.set()
        try:
            with self.engine.lock:
                if self.closed or self.engine.cancel.is_set():raise TrialUnavailable('session-closed')
                before=self.engine.observe()
                if before.current_index is None:raise TrialUnavailable('no-trial-playback')
                properties=self.engine.rpc('Player.GetProperties',{'playerid':0,'properties':['time','totaltime','canseek','speed']})
                if (properties.get('canseek') is not True or type(properties.get('speed')) is not int
                        or properties['speed'] not in (0,1)):
                    raise TrialUnavailable('seek-unavailable')
                current=clock_milliseconds(properties.get('time'))//1000
                duration=clock_milliseconds(properties.get('totaltime'))//1000
                if not 0<=current<duration:raise TrialUnavailable('seek-unavailable')
                step=max(-current,min(offset,duration-current-1))
                if not step:return
                if self.engine.observe().current_index!=before.current_index:
                    raise TrialUnavailable('track-changed-before-seek')
                self.engine.check_cancel()
                self.engine.write('Player.Seek',{'playerid':0,'value':{'seconds':step}})
                self.verify_seek_state(before,properties)
        finally:self.control_pending.clear()

    def seek_to(self,preview):
        if not isinstance(preview,ScrubPreview):raise TrialUnavailable('invalid-scrub-preview')
        self.control_pending.set()
        try:
            if self.closed:raise TrialUnavailable('session-closed')
            seek_owned(self.engine,self.selected,preview)
        finally:self.control_pending.clear()

    def verify_seek_state(self,before,properties):
        verify_seek_state(self.engine,before,properties)

    def close(self):
        # Set cancellation without taking the engine lock; a batch may own it.
        # Joining happens before Stop/Clear, so no late append can revive it.
        self.engine.cancel.set()
        with self.lifecycle:
            if self.closed:return
            if self.worker:
                if self.worker is threading.current_thread():raise TrialUnavailable('cannot-join-own-writer')
                self.worker.join()
            previous=self.engine.intent
            if self.engine.shuffled:self.engine.intent=self.original_intent
            try:self.engine.close()
            finally:self.engine.intent=previous
            self.update(closed=True,phase='closed')
