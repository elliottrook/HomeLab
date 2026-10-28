"""Exact-ID native episode handoff and conservative ownership, no stream URLs."""
from dataclasses import dataclass
from contextlib import contextmanager
import fcntl,os
import time
from series_adapter import EPISODE_PROPERTIES
from series_model import build_series,SeriesUnavailable

PLAYER_READS=frozenset(('Player.GetActivePlayers','Playlist.GetItems','Player.GetItem','VideoLibrary.GetEpisodeDetails'))

def release_parked_video_queue(rpc,write,confirm):
    """Replace one parked item only after a fresh, explicit viewer decision."""
    def snapshot():
        require(not rpc('Player.GetActivePlayers',{}),'another-player-or-queue-active')
        audio=rpc('Playlist.GetItems',dict(playlistid=0,limits=dict(start=0,end=1)))
        require(audio.get('limits',{}).get('total')==0,'another-player-or-queue-active')
        video=rpc('Playlist.GetItems',dict(playlistid=1,limits=dict(start=0,end=2)))
        total=video.get('limits',{}).get('total')
        require(type(total) is int and 0<=total<=1,'video-queue-not-singleton')
        if total==1:require(isinstance(video.get('items'),list) and len(video['items'])==1,
                            'video-queue-not-singleton')
        return video
    first=snapshot();second=snapshot()
    require(first==second,'video-queue-changed')
    if first['limits']['total']==0:return True
    if not confirm():return False
    require(snapshot()==first,'video-queue-changed')
    write('Playlist.Clear',dict(playlistid=1))
    require(idle(rpc),'video-queue-clear-not-verified')
    return True

@contextmanager
def entry_lock(directory):
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    descriptor=os.open(directory/'entry.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SeriesUnavailable('series-already-opening') from None
        yield
    finally:os.close(descriptor)

def require(value,message):
    if not value:raise SeriesUnavailable(message)

def idle(rpc):
    return not rpc('Player.GetActivePlayers',{}) and all(
        rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))

@dataclass(frozen=True)
class EpisodePlan:
    show_id:int
    episode_id:int
    resume:bool

def prepare_episode(rpc,show_id,episode_id,*,resume=True,today=None):
    require(type(show_id) is int and 0<show_id<=2147483647 and type(episode_id) is int
        and 0<episode_id<=2147483647 and type(resume) is bool,'invalid-episode-request')
    require(idle(rpc),'another-player-or-queue-active')
    row=rpc('VideoLibrary.GetEpisodeDetails',dict(episodeid=episode_id,properties=EPISODE_PROPERTIES)).get('episodedetails')
    require(isinstance(row,dict) and type(row.get('episodeid')) is int and row['episodeid']==episode_id,'episode-identity-changed')
    page=build_series(show_id,[row],expected_total=1,today=today)
    episode=page.seasons[0].episodes[0]
    require(episode.available,'episode-not-available')
    return EpisodePlan(show_id,episode_id,resume and episode.resume_seconds is not None)

class EpisodeSession:
    """One open at a time; stop only a positively observed owned episode.

    The caller supplies accepted following identities, not another sequencer.
    An unresolved Open is never retried or interpreted as an empty safe player.
    """
    def __init__(self,rpc,show_id,following,*,clock=time.monotonic):
        self.rpc=rpc;self.show_id=show_id;self.following=following;self.clock=clock
        self.phase='idle';self.expected=None;self.confirmed=False;self.cancelled=False
        self.completed_id=None;self.completed_until=0
        self.deadline=0;self.error=None;self.stops=0

    def start(self,episode_id):
        require(self.phase=='idle','episode-open-already-pending')
        self.phase='preparing';self.cancelled=False;self.error=None;self.completed_id=None
        try:
            plan=prepare_episode(self.rpc,self.show_id,episode_id)
            require(idle(self.rpc),'another-player-or-queue-active')
        except Exception:
            self.phase='idle';raise
        if self.cancelled:self.phase='idle';return
        self.expected=plan.episode_id;self.confirmed=False;self.deadline=self.clock()+30
        self.phase='opening'
        try:self.rpc('Player.Open',dict(item=dict(episodeid=plan.episode_id),options=dict(resume=plan.resume)))
        except Exception:
            self.phase='recovery';self.error='episode-open-result-unknown'
            raise SeriesUnavailable(self.error) from None

    def cancel(self):self.cancelled=True

    def poll(self):
        if self.phase=='idle' and self.completed_id is not None and self.clock()>self.completed_until:
            self.completed_id=None
        if self.phase in ('preparing','conflict') or (self.phase=='idle' and self.completed_id is None):return False
        players=self.rpc('Player.GetActivePlayers',{})
        if not players:
            if self.phase=='idle':return False
            if self.confirmed:
                self.completed_id=None if self.cancelled else self.expected
                self.completed_until=self.clock()+5
                self.phase='idle';self.expected=None;self.confirmed=False;return True
            if self.clock()>=self.deadline:
                self.phase='recovery';self.error='episode-start-not-confirmed'
            return False
        if (not isinstance(players,list) or len(players)!=1 or players[0].get('playerid')!=1
                or players[0].get('type')!='video'):
            self.phase='conflict';self.confirmed=False;self.error='external-player-active';return False
        item=self.rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid'])).get('item',{})
        # Metadata can arrive after the player handle: never stop an unknown item.
        if item.get('type')!='episode' or type(item.get('id')) is not int or type(item.get('tvshowid')) is not int:
            if self.phase!='idle' and self.clock()>=self.deadline:self.phase='recovery';self.error='episode-identity-not-confirmed'
            return False
        expected=item['id']==self.expected and item['tvshowid']==self.show_id
        if not expected and self.phase=='idle' and self.completed_id and not self.cancelled and item['tvshowid']==self.show_id:
            following=self.following(self.completed_id)
            if type(following) is int and item['id']==following:self.expected=following;expected=True
        if not expected and self.confirmed and item['tvshowid']==self.show_id:
            following=self.following(self.expected)
            if type(following) is int and item['id']==following:self.expected=following;expected=True
        if not expected:
            self.phase='conflict';self.confirmed=False;self.error='external-episode-active';return False
        self.confirmed=True
        if self.cancelled and self.phase!='stopping':
            self.phase='stopping';self.rpc('Player.Stop',dict(playerid=1));self.stops+=1
        elif self.phase!='stopping':self.phase='playing'
        return False

    @property
    def can_close(self):return self.phase in ('idle','conflict','recovery')
