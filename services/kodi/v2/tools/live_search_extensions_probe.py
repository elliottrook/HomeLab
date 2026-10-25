"""HP scratch proof: exact artist membership and native movie-info/Back only.

No installed file changes, playback, queue or settings writes. No paths, art,
titles or exception text are exported in evidence. Native info is dismissed
only after its exact displayed ID/type/title have been observed.
"""
import json, os, sys, threading, time
from pathlib import Path
import xbmc, xbmcgui

def require(value, reason):
    if not value:raise RuntimeError(reason)

require(os.uname().nodename=='AsterTV','hp-only')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from global_search import Hit
from search_extensions import artist_albums, movie_info_item

def rpc(method, params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','VideoLibrary.GetMovieDetails',
                       'AudioLibrary.GetArtists','AudioLibrary.GetAlbums','Input.ExecuteAction'},'read-input-only')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-request-failed')
    return result['result']

def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',
        dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))

def until(check, reason, timeout=15):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(70)
    raise RuntimeError(reason)

root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
passed=False;checks=[];failure=None;owned=False;worker=None;native_result=[];stats={}
try:
    require(xbmcgui.getCurrentWindowId()==10000 and xbmcgui.getCurrentWindowDialogId() in (0,9999) and idle(),'idle-home-required')
    home=xbmcgui.Window(10000)
    require(not any(home.getProperty(k) for k in ('AsterSearch.Open','AsterSearch.Handoff',
        'AsterV2Lab.AlbumWindow','AsterSeries.PreviewWindow')) and not (root/'handoff-pending.json').exists(),'no-other-owner')
    artists=rpc('AudioLibrary.GetArtists',dict(albumartistsonly=True,
        filter=dict(field='artist',operator='isnot',value='[Missing Tag]'),limits=dict(start=0,end=5))).get('artists',[])
    require(bool(artists),'artist-fixture')
    counts=[]
    for artist in artists:
        result=artist_albums(rpc,artist['artistid'])
        counts.append(dict(total=result['total'],shown=len(result['hits']),truncated=result['truncated']))
    require(any(row['total']>0 for row in counts),'artist-albums-present')
    stats['artist_sources']=len(counts);stats['artist_album_counts']=counts
    checks.append('exact-artist-id-double-read-membership')
    row=rpc('VideoLibrary.GetMovieDetails',dict(movieid=1036,properties=['title','year']))['moviedetails']
    hit=Hit('movie',row['movieid'],row['title'],str(row.get('year') or ''))
    item=movie_info_item(xbmcgui,hit)
    def show():
        try:native_result.append(xbmcgui.Dialog().info(item))
        except Exception:native_result.append(False)
    worker=threading.Thread(target=show);worker.start()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==12003,'native-movie-info-visible')
    until(lambda:xbmc.getInfoLabel('ListItem.DBID')==str(hit.identity)
        and xbmc.getInfoLabel('ListItem.DBTYPE')=='movie'
        and xbmc.getInfoLabel('ListItem.Title')==hit.title,'native-exact-movie-identity')
    owned=True;require(idle(),'no-autoplay-on-info')
    stats['native_play_control_visible']=xbmc.getCondVisibility('Control.IsVisible(8)')
    stats['native_resume_control_visible']=xbmc.getCondVisibility('Control.IsVisible(9)')
    checks.append('native-movie-info-exact-id-no-autoplay')
    rpc('Input.ExecuteAction',dict(action='back'))
    worker.join(timeout=10)
    require(not worker.is_alive() and native_result==[True],'native-info-returned')
    require(xbmcgui.getCurrentWindowId()==10000 and xbmcgui.getCurrentWindowDialogId() in (0,9999) and idle(),'exact-home-return-idle')
    checks.append('native-movie-info-back-return');passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<80 else 'extension-probe-failed'
finally:
    if owned and xbmcgui.getCurrentWindowDialogId()==12003 and idle():
        rpc('Input.ExecuteAction',dict(action='back'))
    if worker:worker.join(timeout=2)
    clean=idle() and xbmcgui.getCurrentWindowId()==10000 and xbmcgui.getCurrentWindowDialogId() in (0,9999)
    result=dict(passed=passed,checks_enforced=True,checks=checks,failure=failure,idle_empty=clean,**stats)
    path=root/('native-extension-probe-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(result,handle)
    path.chmod(0o600)
