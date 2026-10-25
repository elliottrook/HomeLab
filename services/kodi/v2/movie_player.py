"""Exact-ID movie snapshots and one-shot, positively observed playback ownership."""
from dataclasses import dataclass
import hashlib,json,math,time
from pathlib import Path

class MovieUnavailable(ValueError):pass
def require(value,reason):
    if not value:raise MovieUnavailable(reason)
def identity(value):
    require(type(value) is int and 0<value<=2147483647,'invalid-movie-id');return value
def number(value):
    require(type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid-movie-number');return float(value)
def text(value,limit):
    require(isinstance(value,str) and len(value)<=limit,'invalid-movie-text');return value

PROPERTIES=['title','year','plot','genre','runtime','resume','thumbnail','fanart','rating','mpaa','file']
READS=frozenset(('VideoLibrary.GetMovieDetails','Player.GetActivePlayers','Playlist.GetItems','Player.GetItem'))
MOVIE_STAGE='aster-global-search-ui12'
PREVIOUS_SEARCH='01e499b94aa5f819900fa311515a95a58ead1207f9e3e272fb287590d63b282e'
TARGETS={'overlay/Home.xml':'1080i/Home.xml','overlay/select_dispatch.py':'tools/select_dispatch.py',
    'overlay/custom_1127_search.xml':'1080i/custom_1127_search.xml',
    'overlay/custom_1128_searchdetails.xml':'1080i/custom_1128_searchdetails.xml',
    'overlay/custom_1129_artistalbums.xml':'1080i/custom_1129_artistalbums.xml',
    'overlay/custom_1130_movie.xml':'1080i/custom_1130_movie.xml'}
MEMBERS={'default.py','movie.py','resources/lib/global_search.py','resources/lib/search_details.py',
    'resources/lib/search_handoff.py','resources/lib/search_extensions.py','resources/lib/movie_player.py',*TARGETS}
GUARDS={'skin.asterhome/1080i/VideoFullScreen.xml':'07e723b884f8a25271819fbe59e6162770661a58d24edba983b233645cca5d6a',
    'skin.asterhome/tools/next_episode.py':'8fe18880de923443734fde26dd0c47815e93c68c531e9a34103630054e22c102',
    'plugin.video.jellyfin/jellyfin_kodi/player.py':'21b93325b6ef9b50fdd3f5c48b273e12820f5a662ae534405dacdebcc15388fd'}

def verify_stage(storage=Path('/storage')):
    root=storage/'.aster-staging'/MOVIE_STAGE;skin=storage/'.kodi/addons/skin.asterhome'
    try:
        raw=(root/'manifest.json').read_bytes()
        require(raw==(storage/'.aster-checkpoints/aster-global-search-20261024/active-manifest.json').read_bytes(),'movie-active-stage-changed')
        manifest=json.loads(raw)
        require(manifest.get('stage')==MOVIE_STAGE and manifest.get('movie_page')==11130
            and manifest.get('previous_manifest_sha256')==PREVIOUS_SEARCH,'movie-stage-kind')
        require(len(manifest['files'])==len(MEMBERS) and {r['path'] for r in manifest['files']}==MEMBERS,'movie-stage-members')
        for row in manifest['files']:
            path=root/row['path'];require(not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'movie-stage-drift')
            if row['path'] in TARGETS:
                path=skin/TARGETS[row['path']]
                require(not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'movie-installed-drift')
        for name,expected in GUARDS.items():
            path=storage/'.kodi/addons'/name
            require(not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,'movie-playback-guard-drift')
    except (OSError,KeyError,TypeError,ValueError):raise MovieUnavailable('movie-stage-or-guard-unavailable') from None

@dataclass(frozen=True)
class Movie:
    movie_id:int
    title:str
    year:int
    synopsis:str
    genres:tuple
    seconds:int
    resume_seconds:float
    resume_total:float
    poster:str
    fanart:str
    rating:float
    certificate:str
    available:bool
    @property
    def has_resume(self):return 0<self.resume_seconds<self.resume_total

def read_movie(rpc,movie_id):
    identity(movie_id)
    def snapshot():
        try:value=rpc('VideoLibrary.GetMovieDetails',dict(movieid=movie_id,properties=PROPERTIES))
        except Exception:raise MovieUnavailable('movie-unavailable') from None
        require(isinstance(value,dict) and isinstance(value.get('moviedetails'),dict),'movie-unavailable')
        row=value['moviedetails'];require(identity(row.get('movieid'))==movie_id,'movie-identity-changed')
        title=text(row.get('title'),4096).strip();require(bool(title),'missing-movie-title')
        year=row.get('year',0);seconds=row.get('runtime',0)
        require(type(year) is int and 0<=year<10000 and type(seconds) is int and 0<=seconds<=604800,'invalid-movie-metadata')
        genres=row.get('genre',[]);require(isinstance(genres,list) and len(genres)<=100,'invalid-movie-genres')
        genres=tuple(text(g,4096) for g in genres)
        resume=row.get('resume',{});require(isinstance(resume,dict),'invalid-movie-resume')
        position=number(resume.get('position',0));total=number(resume.get('total',0))
        require(position<=total,'invalid-movie-resume')
        # File values never leave this source-local snapshot, enter a URL,
        # appear in evidence or become authority for Player.Open.
        available=bool(text(row.get('file',''),65536))
        rating=number(row.get('rating',0));require(rating<=10,'invalid-movie-rating')
        return Movie(movie_id,title,year,text(row.get('plot',''),100000),genres,seconds,position,total,
            text(row.get('thumbnail',''),16384),text(row.get('fanart',''),16384),rating,
            text(row.get('mpaa',''),1024),available)
    first=snapshot();require(first==snapshot(),'movie-changed-during-read');return first

def idle(rpc):
    players=rpc('Player.GetActivePlayers',{})
    require(isinstance(players,list),'invalid-player-state')
    return not players and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))

class MovieSession:
    def __init__(self,rpc,movie_id,*,clock=time.monotonic):
        self.rpc=rpc;self.movie_id=identity(movie_id);self.clock=clock
        self.phase='idle';self.confirmed=False;self.cancelled=False;self.deadline=0;self.error=None;self.stops=0
    def start(self,*,resume=False):
        require(type(resume) is bool and self.phase=='idle','movie-open-not-idle')
        require(idle(self.rpc),'another-player-or-queue-active')
        value=read_movie(self.rpc,self.movie_id)
        require(value.available,'movie-not-indexed-playable')
        require(not resume or value.has_resume,'movie-resume-unavailable')
        require(idle(self.rpc),'another-player-or-queue-active')
        self.confirmed=False;self.cancelled=False;self.deadline=self.clock()+30;self.error=None;self.phase='opening'
        try:self.rpc('Player.Open',dict(item=dict(movieid=self.movie_id),options=dict(resume=resume)))
        except Exception:
            self.phase='recovery';self.error='movie-open-result-unknown'
            raise MovieUnavailable(self.error) from None
    def cancel(self):self.cancelled=True
    def finish_queue(self):
        """Restore only the empty video queue this exact request started with."""
        require(self.confirmed and self.phase in ('playing','stopping'),'movie-queue-ownership-not-confirmed')
        def snapshot():
            require(not self.rpc('Player.GetActivePlayers',{}),'movie-player-still-active')
            audio=self.rpc('Playlist.GetItems',dict(playlistid=0,limits=dict(start=0,end=1)))
            require(audio.get('limits',{}).get('total')==0,'external-audio-queue-active')
            video=self.rpc('Playlist.GetItems',dict(playlistid=1,limits=dict(start=0,end=2)))
            count=video.get('limits',{}).get('total');items=video.get('items',[])
            require(type(count) is int and isinstance(items,list),'invalid-owned-video-queue')
            if count==0:
                require(not items,'invalid-empty-video-queue');return False
            require(count==1 and len(items)==1 and items[0].get('type')=='movie'
                and type(items[0].get('id')) is int and items[0]['id']==self.movie_id,'owned-video-queue-changed')
            return True
        first=snapshot();require(first==snapshot(),'owned-video-queue-changing')
        require(not self.rpc('Player.GetActivePlayers',{}),'movie-player-still-active')
        if first:
            self.phase='cleaning'
            try:self.rpc('Playlist.Clear',dict(playlistid=1))
            except Exception:
                self.phase='recovery';self.error='movie-queue-clear-result-unknown'
                raise MovieUnavailable(self.error) from None
            require(not snapshot(),'movie-queue-clear-not-confirmed')
    def poll(self):
        if self.phase in ('idle','conflict','recovery'):return False
        players=self.rpc('Player.GetActivePlayers',{})
        require(isinstance(players,list),'invalid-player-state')
        if not players:
            if self.confirmed:
                try:self.finish_queue()
                except MovieUnavailable:
                    if self.phase!='recovery':self.phase='conflict';self.error='owned-movie-queue-not-restored'
                    self.confirmed=False;return False
                self.phase='idle';self.confirmed=False;return True
            if self.clock()>=self.deadline:self.phase='recovery';self.error='movie-start-not-confirmed'
            return False
        if len(players)!=1 or players[0].get('playerid')!=1 or players[0].get('type')!='video':
            self.phase='conflict';self.error='external-player-active';return False
        item=self.rpc('Player.GetItem',dict(playerid=1,properties=[])).get('item',{})
        if item.get('type')!='movie' or type(item.get('id')) is not int:
            if self.clock()>=self.deadline:self.phase='recovery';self.error='movie-identity-not-confirmed'
            return False
        if item['id']!=self.movie_id:
            self.phase='conflict';self.error='external-movie-active';return False
        self.confirmed=True
        if self.cancelled and self.phase!='stopping':
            self.phase='stopping';self.stops+=1
            try:self.rpc('Player.Stop',dict(playerid=1))
            except Exception:
                self.phase='recovery';self.error='movie-stop-result-unknown'
                raise MovieUnavailable(self.error) from None
        elif self.phase!='stopping':self.phase='playing'
        return False
