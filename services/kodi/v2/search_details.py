"""Exact-ID read-only details; never resolve streams or issue playback commands."""
from dataclasses import dataclass
from global_search import Hit,SOURCES,SearchUnavailable,_hit

DETAILS = {
    'tvshow': ('VideoLibrary.GetTVShowDetails','tvshowdetails','plot'),
    'movie': ('VideoLibrary.GetMovieDetails','moviedetails','plot'),
    'album': ('AudioLibrary.GetAlbumDetails','albumdetails','description'),
    'artist': ('AudioLibrary.GetArtistDetails','artistdetails','description'),
    'song': ('AudioLibrary.GetSongDetails','songdetails','comment'),
}
DETAIL_READS=frozenset(row[0] for row in DETAILS.values())

@dataclass(frozen=True)
class Detail:
    hit: Hit
    synopsis: str
    artwork: str
    source: str
    hero: str = ''

def read_details(rpc,hit):
    if (not isinstance(hit,Hit) or hit.kind not in DETAILS
            or type(hit.identity) is not int or not 0<hit.identity<=2147483647):
        raise SearchUnavailable('invalid-result-identity')
    source=next(s for s in SOURCES if s.kind==hit.kind)
    method,key,synopsis=DETAILS[hit.kind]
    params={source.identity:hit.identity,'properties':list(source.properties)+[synopsis,'thumbnail']}
    if hit.kind in ('tvshow','movie'):params['properties'].append('fanart')
    def snapshot():
        try:result=rpc(method,params)
        except Exception:raise SearchUnavailable('result-unavailable') from None
        if not isinstance(result,dict) or not isinstance(result.get(key),dict):
            raise SearchUnavailable('result-unavailable')
        row=result[key];current=_hit(source,row)
        if current!=hit:raise SearchUnavailable('result-changed-refresh-search')
        text=row.get(synopsis,'');art=row.get('thumbnail','');hero=row.get('fanart','')
        if (not isinstance(text,str) or len(text)>100000 or not isinstance(art,str) or len(art)>16384
                or not isinstance(hero,str) or len(hero)>16384):
            raise SearchUnavailable('invalid-result-details')
        return Detail(current,text.strip() or 'Synopsis is not available in this box’s synced index.',
                      art,source.label+' · synced Kodi index',hero or art)
    first=snapshot();second=snapshot()
    if first!=second:raise SearchUnavailable('result-changed-refresh-search')
    return second
