"""HP native movie page; explicit ID-only Play/Resume, no autoplay or new resolver."""
import fcntl,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from movie_player import MovieSession,MovieUnavailable,READS,read_movie,idle,verify_stage
DIRECTORY=Path('/storage/.aster-checkpoints/aster-movie-playback-20261024')
PREFIX='AsterMovie.'
def require(value,reason):
    if not value:raise MovieUnavailable(reason)
def rpc(method,params=None):
    require(method in READS|{'Player.Open','Player.Stop','Playlist.Clear'},'movie-rpc-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'movie-native-request-failed');return reply.get('result',{})
def fence(session):
    path=DIRECTORY/'unresolved-start.json'
    if session.phase=='recovery' and not path.exists():
        with path.open('x') as handle:json.dump(dict(movie_id=session.movie_id,error=session.error,time=int(time.time())),handle)
        path.chmod(0o600)
def main():
    if os.uname().nodename!='AsterTV':return
    DIRECTORY.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(DIRECTORY/'entry.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    admitted=False;opened=False;session=None;home=xbmcgui.Window(10000)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        admitted=True
        require(len(sys.argv)==2 and sys.argv[1].isdecimal(),'invalid-movie-link')
        require(not (DIRECTORY/'unresolved-start.json').exists(),'movie-recovery-required')
        require(xbmcgui.getCurrentWindowId()==11127 and xbmcgui.getCurrentWindowDialogId() in (0,9999) and idle(rpc),'idle-search-source-required')
        verify_stage();value=read_movie(rpc,int(sys.argv[1]));session=MovieSession(rpc,value.movie_id)
        for name in ('Command','Ready','Window','Phase'):home.clearProperty(PREFIX+name)
        xbmc.executebuiltin('ActivateWindow(1130)');opened=True
        monitor=xbmc.Monitor();end=time.monotonic()+10
        while xbmcgui.getCurrentWindowId()!=11130:
            require(time.monotonic()<end and not monitor.waitForAbort(.05),'movie-window-not-ready')
        window=xbmcgui.Window(11130)
        def render():
            metadata=' / '.join(value.genres)
            if value.year:metadata+='  [COLOR ff91c6a2]'+str(value.year)+'[/COLOR]'
            score=(f'Score {value.rating:.1f} / 10  ' if value.rating else '')+value.certificate
            duration=f'{value.seconds//60} min' if value.seconds else 'Duration unavailable'
            for key,text in dict(Id=str(value.movie_id),Title=value.title,Metadata=metadata,Rating=score,
                Synopsis=value.synopsis or 'Synopsis unavailable',Poster=value.poster or 'special://skin/media/08-film.png',
                Fanart=value.fanart,Duration=duration,HasResume='true' if value.has_resume else 'false',
                Resume=f'Resume · {int(value.resume_seconds)//60}:{int(value.resume_seconds)%60:02d}',
                Playable='true' if value.available else 'false').items():window.setProperty('Movie.'+key,text)
            window.setProperty('Movie.Status','Choose Play or Resume · opening this page never starts playback')
            window.setProperty('Movie.Ready','true')
            window.setProperty('Movie.Phase',session.phase)
        render();home.setProperty(PREFIX+'Window','11130');home.setProperty(PREFIX+'Ready','true')
        xbmc.executebuiltin('SetFocus('+('201' if value.has_resume else '200')+')')
        fullscreen=False;return_until=0
        while not monitor.abortRequested():
            current=xbmcgui.getCurrentWindowId();command=home.getProperty(PREFIX+'Command')
            home.clearProperty(PREFIX+'Command')
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
            if session.phase=='playing' and not fullscreen and current==11130:
                fullscreen=True;xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
            if ended:
                return_until=time.monotonic()+2
                try:value=read_movie(rpc,value.movie_id);render()
                except MovieUnavailable:window.setProperty('Movie.Status','Progress is syncing. Reopen later to refresh it.')
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
            if session.phase=='idle' and current!=11130 and time.monotonic()>=return_until:break
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
