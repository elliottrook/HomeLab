"""HP actual Search→movie page/play/resume/OSD/Back tests, no direct player writes."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
active=json.loads((root/'active-manifest.json').read_text())
require(active.get('stage') in ('aster-global-search-ui12','aster-global-search-ui13','aster-global-search-ui14'),'known-stage')
stage=Path('/storage/.aster-staging')/active['stage']
sys.path.insert(0,str(stage/'resources/lib'))
from movie_player import read_movie
lock=os.open(root/'native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    os.close(lock);raise RuntimeError('native-driver-already-running')
play='--play' in sys.argv;home=xbmcgui.Window(10000)
def prop(name):return home.getProperty('AsterSearch.'+name)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Player.GetItem','Player.GetProperties',
        'VideoLibrary.GetMovieDetails','VideoLibrary.GetMovies','Input.ExecuteAction','Input.SendText','Input.Home'},'movie-test-input-read-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request-failed');return reply['result']
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,reason):
    end=time.monotonic()+40
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(reason)
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def focus(identity):
    xbmc.sleep(150);xbmc.executebuiltin('SetFocus('+str(identity)+')')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'focus-'+str(identity));xbmc.sleep(100)
def enter(movie_id):
    value=read_movie(rpc,movie_id);require(value.available,'fixture-not-playable')
    require(idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Ready'),'idle-home-required')
    focus(135);select();until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true','normal-search')
    query=' '.join(value.title.split()[:5])[:90];focus(10);select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'keyboard')
    rpc('Input.SendText',dict(text=query,done=True));until(lambda:prop('Query')==query and prop('Ready')=='true','query-ready')
    xbmc.executebuiltin('Control.SetFocus(20,1,absolute)')
    until(lambda:xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Kind)')=='movie','movie-group')
    xbmc.executebuiltin('Control.SetFocus(30,0,absolute)');xbmc.sleep(200)
    found=False
    for _ in range(min(500,int(xbmc.getInfoLabel('Container(30).NumItems') or 0))):
        if xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')==str(movie_id):found=True;break
        press('down');xbmc.sleep(150)
    require(found,'fixture-found-by-search');focus(30);select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==11128 and prop('DetailTitle')==value.title and prop('CanOpen')=='true','movie-details')
    focus(11);select()
    until(lambda:home.getProperty('AsterMovie.Window')=='11130' and prop('Handoff')=='child'
        and xbmc.getInfoLabel('Window.Property(Movie.Id)')==str(movie_id),'native-movie-page')
    require(idle(),'no-autoplay');return query,value
def leave(query,movie_id):
    if xbmcgui.getCurrentWindowId()==11130:press('back')
    else:require(xbmcgui.getCurrentWindowId()==11127,'movie-return-source')
    until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true' and not prop('Handoff')
        and not home.getProperty('AsterMovie.Window') and prop('Query')==query
        and xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')==str(movie_id)
        and xbmc.getCondVisibility('Control.HasFocus(30)'),'exact-movie-search-return')
    require(idle(),'return-idle');press('back')
    until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Ready'),'search-home')
def owned(movie_id):
    players=rpc('Player.GetActivePlayers')
    if len(players)!=1 or players[0].get('playerid')!=1 or players[0].get('type')!='video':return False
    item=rpc('Player.GetItem',dict(playerid=1,properties=[]))['item']
    return item.get('type')=='movie' and type(item.get('id')) is int and item['id']==movie_id
def seconds():
    value=rpc('Player.GetProperties',dict(playerid=1,properties=['time']))['time']
    return value['hours']*3600+value['minutes']*60+value['seconds']+value['milliseconds']/1000
def stop_back(movie_id):
    require(owned(movie_id),'owned-before-back');press('back')
    until(lambda:not rpc('Player.GetActivePlayers') and (
        (xbmcgui.getCurrentWindowId()==11130 and home.getProperty('AsterMovie.Phase')=='idle') or
        (xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true' and not prop('Handoff'))),'back-stops-and-returns-source')
    require(idle(),'post-video-empty')
passed=False;failure=None;checks=[];resume_fixture=False;state=None
try:
    query,value=enter(1036);checks.append('normal-movie-no-autoplay')
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-global-search-20261024/movie-page-'+str(time.time_ns())+'.png)')
    if play:
        focus(200);select();until(lambda:owned(1036) and xbmcgui.getCurrentWindowId()==12005,'exact-movie-play')
        require(seconds()<20,'explicit-play-from-start');xbmc.sleep(20000)
        press('osd');until(lambda:xbmc.getCondVisibility('Window.IsVisible(videoosd)'),'movie-osd')
        require(all(xbmc.getCondVisibility('Control.IsVisible('+str(i)+')') for i in (7100,7101,7102)),'osd-audio-subtitle-quality-retained')
        xbmc.sleep(400)
        xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-feedback-20261024/video-osd.png)')
        xbmc.sleep(400)
        press('back');until(lambda:not xbmc.getCondVisibility('Window.IsVisible(videoosd)'),'osd-dismissed')
        stop_back(1036);checks.extend(['explicit-movie-play-from-start','existing-osd-retained','fullscreen-back-stops-and-returns'])
    leave(query,1036);checks.append('exact-movie-query-id-focus-return')
    if play:
        rows=rpc('VideoLibrary.GetMovies',dict(filter=dict(field='inprogress',operator='true',value=''),
            properties=['resume','runtime'],limits=dict(start=0,end=100))).get('movies',[])
        candidate=next((r for r in rows if type(r.get('movieid')) is int and r['movieid']!=1036 and r.get('runtime',0)>1200
            and 180<r.get('resume',{}).get('position',0)<r.get('resume',{}).get('total',0)-120),None)
        if candidate:
            resume_fixture=True;identity=candidate['movieid'];query,value=enter(identity)
            require(value.has_resume and xbmc.getCondVisibility('Control.IsVisible(201)'),'real-resume-present')
            focus(201);select();until(lambda:owned(identity) and xbmcgui.getCurrentWindowId()==12005,'real-movie-resume')
            position=seconds();require(max(0,value.resume_seconds-15)<=position<=value.resume_seconds+20,'native-resume-position')
            xbmc.sleep(1500);stop_back(identity);leave(query,identity);checks.append('real-existing-movie-bookmark-resume')
    query,_=enter(1036);rpc('Input.Home')
    until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Handoff') and not home.getProperty('AsterMovie.Window'),'movie-global-home')
    xbmc.sleep(900);require(idle() and xbmcgui.getCurrentWindowId()==10000,'home-not-hijacked');checks.append('movie-home-no-hijack')
    passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<100 else 'native-movie-test-failed'
    state=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),
        owner=home.getProperty('AsterMovie.Window'),phase=home.getProperty('AsterMovie.Phase'),handoff=prop('Handoff'))
finally:
    # Never issue a cleanup Stop on an unidentified movie or unrelated player.
    if idle():
        if xbmcgui.getCurrentWindowDialogId() in (10103,11128):press('back');xbmc.sleep(350)
        if xbmcgui.getCurrentWindowId()==11130:press('back');xbmc.sleep(1000)
        if xbmcgui.getCurrentWindowId()==11127:press('back');xbmc.sleep(500)
    clean=idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Ready') and not home.getProperty('AsterMovie.Window')
    path=root/('native-movie-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(passed=passed,checks_enforced=True,playback_test=play,
        checks=checks,failure=failure,failure_state=state,resume_fixture_available=resume_fixture,idle_empty=clean,
        stage_manifest_sha256=hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()),handle)
    path.chmod(0o600);os.close(lock)
