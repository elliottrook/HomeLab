"""ID-only accepted-page routes and navigation observation; no player writes."""
from dataclasses import dataclass
import hashlib,json
from pathlib import Path
from global_search import Hit,SearchUnavailable,normalize_query

SERIES_SHA='4c090e0b3a66b7b56679a07569453d668c372727eeb458f91d97d27ab772796d'
MUSIC_SHA='0c19d992a337bee55ec449423b16576962e7721e573a60a640e448d3fb220334'
LABELS={'tvshow':'Open TV series','album':'Open album player','song':'Open song player'}

@dataclass(frozen=True)
class Route:
    command: str
    marker: str
    expected: str

def route_for(hit,*,movie=False):
    if movie and isinstance(hit,Hit) and hit.kind=='movie' and type(hit.identity) is int and 0<hit.identity<=2147483647:
        from movie_player import MOVIE_STAGE
        return Route('RunScript(/storage/.aster-staging/'+MOVIE_STAGE+'/movie.py,'+str(hit.identity)+')','AsterMovie.Window',str(hit.identity))
    if not isinstance(hit,Hit) or hit.kind not in LABELS or type(hit.identity) is not int or not 0<hit.identity<=2147483647:
        raise SearchUnavailable('unsupported-search-player-link')
    if hit.kind=='tvshow':
        return Route('RunScript(/storage/.aster-staging/aster-series-preview16/default.py,'+str(hit.identity)+',play)',
                     'AsterSeries.PreviewWindow',hit.title)
    return Route('RunScript(script.astermusic.v2lab,'+hit.kind+','+str(hit.identity)+')',
                 'AsterV2Lab.AlbumWindow',str(hit.identity) if hit.kind=='album' else 'song-'+str(hit.identity))

def verify_child(kind,storage=Path('/storage'),*,movie=False):
    if kind=='movie' and movie:
        from movie_player import verify_stage,MovieUnavailable
        try:verify_stage(storage)
        except MovieUnavailable:raise SearchUnavailable('accepted-movie-page-changed') from None
        return
    if kind not in LABELS:raise SearchUnavailable('unsupported-search-player-link')
    stage=storage/'.aster-staging'/('aster-series-preview16' if kind=='tvshow' else 'aster-music-v2lab-0.1.0-candidate64')
    try:
        raw=(stage/'manifest.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=(SERIES_SHA if kind=='tvshow' else MUSIC_SHA):raise ValueError()
        manifest=json.loads(raw)
        rows=manifest['files']
        if len(rows)!=(6 if kind=='tvshow' else 48):raise ValueError()
        for row in rows:
            relative=Path(row['path'])
            if relative.is_absolute() or '..' in relative.parts:raise ValueError()
            path=stage/relative if kind=='tvshow' else storage/'.kodi/addons'/relative
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError()
    except (OSError,ValueError,KeyError,TypeError):
        raise SearchUnavailable('accepted-player-page-changed') from None

@dataclass(frozen=True)
class Cursor:
    query: str
    kind: str
    identity: int

def restore_cursor(groups,cursor):
    if not isinstance(cursor,Cursor) or normalize_query(cursor.query)!=cursor.query:
        raise SearchUnavailable('invalid-search-return')
    for group_index,group in enumerate(groups):
        if group.kind==cursor.kind:
            for result_index,hit in enumerate(group.hits):
                if hit.kind==cursor.kind and hit.identity==cursor.identity:return group_index,result_index
            return group_index,None
    raise SearchUnavailable('missing-search-group')

class Admission:
    """One launch only. Return only after observed child and settled navigation."""
    def __init__(self,route,now):
        self.route=route;self.started=now;self.phase='new';self.settling=None;self.destination=None
    def dispatch(self,*,idle,source_visible):
        if self.phase!='new' or not idle or not source_visible:raise SearchUnavailable('search-handoff-not-idle')
        self.phase='pending';return self.route.command
    def observe(self,*,marker,ready,source_visible,players,now):
        if self.phase not in ('pending','child'):return self.phase
        if self.phase=='pending':
            if marker and ready:self.phase='child'
            elif now-self.started>=30:self.phase='uncertain'
            return self.phase
        if marker:self.settling=None;self.destination=None;return 'child'
        destination='restore' if source_visible else 'left'
        if self.settling is None or self.destination!=destination:
            self.settling=now;self.destination=destination
        if players:
            if now-self.settling>=5:self.phase='left'
        elif now-self.settling>=.75:self.phase=destination
        return self.phase
