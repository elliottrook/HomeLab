"""Complete, stable Kodi-only series snapshots. Never opens a player or URL."""
from copy import deepcopy
from dataclasses import dataclass
from series_model import build_series,SeriesUnavailable

EPISODE_PROPERTIES=['title','plot','art','file','lastplayed','resume','runtime',
                    'playcount','showtitle','season','episode','tvshowid','firstaired']
SHOW_PROPERTIES=['title','plot','genre','year','rating','mpaa','art','uniqueid']
READS=frozenset(('VideoLibrary.GetTVShowDetails','VideoLibrary.GetEpisodes'))

@dataclass(frozen=True)
class SeriesSnapshot:
    page: object
    title: str
    synopsis: str
    genres: tuple
    year: object
    rating: object
    certificate: str
    fanart: str
    tvdb_id: object

def _read(rpc,method,params):
    if method not in READS:raise SeriesUnavailable('read-only-series-preview')
    try:
        result=deepcopy(rpc(method,params))
        if not isinstance(result,dict):raise ValueError()
        return result
    except Exception:raise SeriesUnavailable('series-read-unavailable') from None

def _snapshot(rpc,show_id,page_size,cap):
    show=_read(rpc,'VideoLibrary.GetTVShowDetails',dict(tvshowid=show_id,properties=SHOW_PROPERTIES)).get('tvshowdetails')
    if not isinstance(show,dict) or type(show.get('tvshowid')) is not int or show['tvshowid']!=show_id:
        raise SeriesUnavailable('invalid-show-identity')
    rows=[];total=None
    while total is None or len(rows)<total:
        start=len(rows)
        response=_read(rpc,'VideoLibrary.GetEpisodes',dict(tvshowid=show_id,properties=EPISODE_PROPERTIES,
            sort=dict(method='episode',order='ascending'),limits=dict(start=start,end=start+page_size)))
        if not isinstance(response,dict):raise SeriesUnavailable('invalid-episode-response')
        limits=response.get('limits');batch=response.get('episodes',[])
        if not isinstance(limits,dict) or not isinstance(batch,list):raise SeriesUnavailable('invalid-episode-page')
        n=limits.get('total');end=limits.get('end')
        if (type(n) is not int or not 0<=n<=cap or type(end) is not int
                or type(limits.get('start')) is not int or limits['start']!=start
                or not start<=end<=min(n,start+page_size) or end-start!=len(batch)
                or (end==start and n!=start) or (total is not None and n!=total)):
            raise SeriesUnavailable('incomplete-or-changing-series')
        total=n;rows.extend(batch)
    return show,rows

def read_series(rpc,show_id,next_up,*,today=None,page_size=200,cap=5000):
    if (type(show_id) is not int or not 0<show_id<=2147483647
            or type(page_size) is not int or not 1<=page_size<=500
            or type(cap) is not int or not page_size<=cap<=10000):
        raise SeriesUnavailable('invalid-series-read-options')
    first=_snapshot(rpc,show_id,page_size,cap)
    second=_snapshot(rpc,show_id,page_size,cap)
    if first!=second:raise SeriesUnavailable('series-changed-during-read')
    show,rows=second
    # Validate before handing raw rows to the already accepted Up Next policy.
    build_series(show_id,rows,expected_total=len(rows),today=today)
    try:next_row=next_up(deepcopy(show),deepcopy(rows),today=today)
    except Exception:raise SeriesUnavailable('accepted-up-next-unavailable') from None
    if next_row is not None and not isinstance(next_row,dict):raise SeriesUnavailable('invalid-up-next-result')
    page=build_series(show_id,rows,expected_total=len(rows),today=today,
                      next_episode_id=next_row.get('episodeid') if next_row else None)
    text=lambda key,default='':show.get(key) if isinstance(show.get(key),str) and show[key] else default
    genres=show.get('genre');art=show.get('art')
    year=show.get('year');rating=show.get('rating')
    import math
    unique=show.get('uniqueid') if isinstance(show.get('uniqueid'),dict) else {}
    tvdb=unique.get('tvdb')
    tvdb_id=int(tvdb) if isinstance(tvdb,str) and tvdb.isdecimal() and int(tvdb)>0 else None
    return SeriesSnapshot(page,text('title',text('label','Series')),text('plot'),
        tuple(g for g in genres if isinstance(g,str)) if isinstance(genres,list) else (),
        year if type(year) is int and year>0 else None,
        rating if type(rating) in (int,float) and math.isfinite(rating) and 0<rating<=10 else None,
        text('mpaa'),art.get('fanart','') if isinstance(art,dict) and isinstance(art.get('fanart',''),str) else '',
        tvdb_id)
