"""HP native movie page; explicit ID-only Play/Resume, no autoplay or new resolver."""
import fcntl,json,os,sys,time
from pathlib import Path
from urllib.parse import quote
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
sys.path.insert(0,str(ROOT))
from movie_player import MovieSession,MovieUnavailable,READS,read_movie,idle,verify_stage
from jellyfin_trailer_route import validated_kodi_youtube_plugin_url
DIRECTORY=Path('/storage/.aster-checkpoints/aster-movie-playback-20261024')
PREFIX='AsterMovie.'
def require(value,reason):
    if not value:raise MovieUnavailable(reason)
def rpc(method,params=None):
    require(method in READS|{'Player.Open','Player.Stop','Playlist.Clear','Addons.GetAddonDetails'},'movie-rpc-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'movie-native-request-failed');return reply.get('result',{})
def fence(session):
    path=DIRECTORY/'unresolved-start.json'
    if session.phase=='recovery' and not path.exists():
        with path.open('x') as handle:json.dump(dict(movie_id=session.movie_id,error=session.error,time=int(time.time())),handle)
        path.chmod(0o600)
def trailer_route(movie_id):
    try:
        addon=rpc('Addons.GetAddonDetails',{'addonid':'plugin.video.youtube','properties':['enabled']}).get('addon',{})
        if not addon.get('enabled'):return None
        detail=rpc('VideoLibrary.GetMovieDetails',dict(movieid=movie_id,properties=['trailer'])).get('moviedetails',{})
        value=detail.get('trailer','') if isinstance(detail,dict) else ''
        return validated_kodi_youtube_plugin_url(value) if isinstance(value,str) else None
    except MovieUnavailable:return None

def enrichment(movie):
    people=[];related=[]
    try:
        detail=rpc('VideoLibrary.GetMovieDetails',dict(movieid=movie.movie_id,
            properties=['cast','director','writer','genre'])).get('moviedetails',{})
        cast=detail.get('cast',[]);directors=detail.get('director',[]);writers=detail.get('writer',[])
        if not isinstance(cast,list) or not isinstance(directors,list) or not isinstance(writers,list):raise ValueError('movie-people')
        for row in cast[:16]:
            if isinstance(row,dict) and isinstance(row.get('name'),str):
                people.append((row['name'],str(row.get('role') or 'Cast'),str(row.get('thumbnail') or '')))
        for name,role in [(n,'Director') for n in directors[:4]]+[(n,'Writer') for n in writers[:4]]:
            if isinstance(name,str) and name and not any(p[0]==name and p[1]==role for p in people):people.append((name,role,''))
        genre=next((g for g in detail.get('genre',[]) if isinstance(g,str) and g),None)
        if genre:
            result=rpc('VideoLibrary.GetMovies',dict(properties=['title','thumbnail','year'],
                filter={'field':'genre','operator':'contains','value':genre},
                sort={'method':'rating','order':'descending'},limits={'start':0,'end':30}))
            for row in result.get('movies',[]):
                identity=row.get('movieid')
                if type(identity) is int and identity!=movie.movie_id and isinstance(row.get('title'),str):
                    related.append((identity,row['title'],str(row.get('thumbnail') or ''),row.get('year',0)))
                    if len(related)==14:break
    except (MovieUnavailable,ValueError,KeyError,TypeError):pass
    return people,related

def admitted_source(movie_id):
    """Only the selected local movie may open a detail page from a library row."""
    window_id=xbmcgui.getCurrentWindowId()
    if window_id==11127:
        return xbmcgui.getCurrentWindowDialogId() in (0,9999)
    try:focus=xbmcgui.Window(window_id).getFocusId()
    except RuntimeError:return False
    if (window_id,focus) not in ((10025,50),(10000,100),(10000,110),(11112,100),(11112,110)):
        return False
    item=110 if focus==110 else 100 if focus==100 else 50
    identity=xbmc.getInfoLabel(f'Container({item}).ListItem.DBID')
    return (identity.isdecimal() and int(identity)==movie_id
            and xbmc.getInfoLabel(f'Container({item}).ListItem.DBTYPE')=='movie'
            and not xbmc.getCondVisibility(f'Container({item}).ListItem.IsParentFolder'))
def main():
    if os.uname().nodename not in ('AsterTV-Bedroom','AsterTV-Family','AsterTV-Jen'):return
    DIRECTORY.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(DIRECTORY/'entry.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    admitted=False;opened=False;session=None;home=xbmcgui.Window(10000)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        admitted=True
        source_window=xbmcgui.getCurrentWindowId()
        require(len(sys.argv)==2 and sys.argv[1].isdecimal(),'invalid-movie-link')
        require(not (DIRECTORY/'unresolved-start.json').exists(),'movie-recovery-required')
        require(admitted_source(int(sys.argv[1])) and idle(rpc),'idle-movie-source-required')
        verify_stage();value=read_movie(rpc,int(sys.argv[1]));session=MovieSession(rpc,value.movie_id)
        for name in ('Command','Ready','Window','Phase'):home.clearProperty(PREFIX+name)
        xbmc.executebuiltin('ActivateWindow(1130)');opened=True
        monitor=xbmc.Monitor();end=time.monotonic()+10
        while xbmcgui.getCurrentWindowId()!=11130:
            require(time.monotonic()<end and not monitor.waitForAbort(.05),'movie-window-not-ready')
        window=xbmcgui.Window(11130)
        xbmc.sleep(300)  # Kodi publishes the custom ID before its XML controls settle.
        def render():
            metadata=' / '.join(value.genres)
            if value.year:metadata+='  [COLOR ff91c6a2]'+str(value.year)+'[/COLOR]'
            score=(f'Score {value.rating:.1f} / 10  ' if value.rating else '')+value.certificate
            duration=f'{value.seconds//60} min' if value.seconds else 'Duration unavailable'
            for key,text in dict(Id=str(value.movie_id),Title=value.title,Metadata=metadata,Rating=score,
                Synopsis=value.synopsis or 'Synopsis unavailable',Poster=value.poster or 'special://skin/media/08-film.png',
                Fanart=value.fanart,Duration=duration,HasResume='true' if value.has_resume else 'false',
                Resume=f'Resume · {int(value.resume_seconds)//60}:{int(value.resume_seconds)%60:02d}',
                Playable='true' if value.available else 'false',HasTrailer='true' if trailer_route(value.movie_id) else 'false').items():window.setProperty('Movie.'+key,text)
            window.setProperty('Movie.Status','')
            people,related=enrichment(value)
            xbmc.log('AsterMovieRails: model people='+str(len(people))+' related='+str(len(related)),xbmc.LOGINFO)
            cast_control=window.getControl(500);cast_control.reset();cast_items=[]
            for name,role,thumb in people:
                item=xbmcgui.ListItem(label=name);item.setProperty('Role',role);item.setProperty('Person',name);item.setArt({'thumb':thumb or 'special://skin/media/aster-compass-128.png'});cast_items.append(item)
            if cast_items:cast_control.addItems(cast_items)
            related_control=window.getControl(501);related_control.reset();related_items=[]
            for identity,title,thumb,year in related:
                item=xbmcgui.ListItem(label=title);item.setProperty('Year',str(year) if year else '')
                item.setProperty('MovieId',str(identity));item.setArt({'thumb':thumb or 'special://skin/media/08-film.png'});related_items.append(item)
            if related_items:related_control.addItems(related_items)
            xbmc.log('AsterMovieRails: controls cast='+str(cast_control.size())+' related='+str(related_control.size()),xbmc.LOGINFO)
            window.setProperty('Movie.CastVisible','true' if people else 'false')
            window.setProperty('Movie.RelatedVisible','true' if related else 'false')
            window.setProperty('Movie.Ready','true')
            window.setProperty('Movie.Phase',session.phase)
        render();home.setProperty(PREFIX+'Window','11130');home.setProperty(PREFIX+'Ready','true')
        xbmc.executebuiltin('SetFocus('+('201' if value.has_resume else '200')+')')
        fullscreen=False;return_until=0;external_mode=''
        while not monitor.abortRequested():
            current=xbmcgui.getCurrentWindowId();command=home.getProperty(PREFIX+'Command')
            home.clearProperty(PREFIX+'Command')
            if command=='related' and current==11130 and session.phase=='idle':
                try:
                    identity=window.getControl(501).getSelectedItem().getProperty('MovieId')
                    require(identity.isdecimal(),'invalid-related-movie')
                    value=read_movie(rpc,int(identity));session=MovieSession(rpc,value.movie_id);render();xbmc.executebuiltin('SetFocus(200)')
                except (MovieUnavailable,ValueError,AttributeError):window.setProperty('Movie.Status','That related title is currently unavailable.')
            if command=='person' and current==11130 and session.phase=='idle':
                try:
                    person=window.getControl(500).getSelectedItem().getProperty('Person')
                    require(bool(person),'invalid-person')
                    external_mode='person-opening'
                    xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.astersearch/?actor='+quote(person,safe='')+'",return)')
                except (MovieUnavailable,ValueError,AttributeError):window.setProperty('Movie.Status','That person is currently unavailable.')
            if command=='trailer' and current==11130 and session.phase=='idle':
                try:
                    route=trailer_route(value.movie_id);require(bool(route),'trailer-unavailable');require(idle(rpc),'idle-trailer-required')
                    rpc('Player.Open',{'item':{'file':route}});external_mode='trailer';fullscreen=False
                except (MovieUnavailable,ValueError,KeyError):window.setProperty('Movie.Status','A safe Jellyfin trailer is not available for this title.')
            if command in ('play','resume') and current==11130 and session.phase=='idle':
                try:
                    verify_stage();session.start(resume=command=='resume');fullscreen=False
                except MovieUnavailable:
                    window.setProperty('Movie.Status','The movie or idle player could not be verified. Nothing was retried.')
            # Leaving to Home/another destination cancels only this owned request.
            if current not in (11130,12005) and session.phase in ('opening','playing','stopping'):session.cancel()
            try:ended=session.poll()
            except Exception:
                session.phase='recovery';session.error='movie-player-observation-uncertain';ended=False
            home.setProperty(PREFIX+'Phase',session.phase);window.setProperty('Movie.Phase',session.phase)
            if (session.phase=='playing' or external_mode=='trailer') and not fullscreen and rpc('Player.GetActivePlayers'):
                fullscreen=True;xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
            if external_mode=='trailer' and not rpc('Player.GetActivePlayers'):
                external_mode='';fullscreen=False
                if current!=11130:xbmc.executebuiltin('ActivateWindow(1130)')
            if external_mode=='person-opening' and current==10025:
                external_mode='person'
            if external_mode=='person' and current not in (11130,10025):
                xbmc.executebuiltin('ActivateWindow(1130)')
            if external_mode=='person' and current==11130:
                external_mode=''
            if ended:
                return_until=time.monotonic()+2
                if current!=11130:
                    xbmc.executebuiltin('ActivateWindow(1130)')
                    until=time.monotonic()+5
                    while xbmcgui.getCurrentWindowId()!=11130:
                        require(time.monotonic()<until and not monitor.waitForAbort(.05),'movie-return-not-ready')
                    current=11130;xbmc.sleep(300)
                try:value=read_movie(rpc,value.movie_id);render()
                except MovieUnavailable:window.setProperty('Movie.Status','Progress is syncing. Reopen later to refresh it.')
                xbmc.executebuiltin('SetFocus('+('201' if value.has_resume else '200')+')')
            if session.phase in ('conflict','recovery'):
                fence(session)
                if session.error=='movie-stop-not-confirmed':
                    message='Stop was not confirmed. Playback may still be running. Use the native Stop control; automatic retries are blocked.'
                    if current==11130:window.setProperty('Movie.Status',message)
                    else:
                        xbmcgui.Dialog().notification('Aster playback needs attention',message)
                        break
                elif current==11130:window.setProperty('Movie.Status','Playback could not be verified. No retry; Back leaves without interrupting another player.')
                else:break
            if session.phase=='idle' and not external_mode and current!=11130 and time.monotonic()>=return_until:
                if source_window==11127 and current!=11127:
                    xbmc.executebuiltin('ActivateWindow(1127)')
                    until=time.monotonic()+5
                    while xbmcgui.getCurrentWindowId()!=11127:
                        require(time.monotonic()<until and not monitor.waitForAbort(.05),'search-return-not-ready')
                break
            if monitor.waitForAbort(.1):break
    except (MovieUnavailable,ValueError,OSError,KeyError):
        if not opened:xbmcgui.Dialog().notification('Movie unavailable','Return to Search and try again. Nothing was started.')
        elif session and session.phase not in ('idle','conflict','recovery'):
            session.phase='recovery';session.error='movie-controller-interrupted';fence(session)
    finally:
        if session:fence(session)
        if admitted:
            for name in ('Window','Ready','Command','Phase'):home.clearProperty(PREFIX+name)
        os.close(fd)
if __name__=='__main__':main()
