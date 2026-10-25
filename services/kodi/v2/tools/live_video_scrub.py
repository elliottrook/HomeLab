"""Enforced HP watched-episode scrub/OSD test; no manufactured history."""
import json,os,re,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
name=sys.argv[1];require(re.fullmatch(r'aster-video-scrub[1-9][0-9]*',name),'stage-name')
integrated='--integrated' in sys.argv
root=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')
source=json.loads(Path('/storage/.aster-checkpoints/aster-series-playback-20261024/fixture.json').read_text())['fixture']
fixture=dict(kind='episode',identity=source['episode_id'],show_id=source['show_id'],watched=source['watched'])
require(fixture.get('watched') is True,'watched-fixture-required')
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Player.GetItem','Player.GetProperties',
        'VideoLibrary.GetEpisodeDetails','VideoLibrary.GetMovies','VideoLibrary.GetMovieDetails',
        'Player.Open','Player.Stop','Input.ExecuteAction'},'native-test-boundary')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-rpc-failed');return result['result']
def label(key):return xbmc.getInfoLabel(key)
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
def until(check,message,seconds=25):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if message=='fixture-playing' and 'samples' in globals():
            players=rpc('Player.GetActivePlayers');state=dict(players=players)
            if any(p.get('playerid')==1 for p in players):
                item=rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid'])).get('item',{})
                state['item']={k:item.get(k) for k in ('type','id','tvshowid')}
                state['canseek']=props().get('canseek');state['duration']=milliseconds(props()['totaltime'])
            if not samples or samples[-1]!=state:samples.append(state)
        if check():return
        xbmc.sleep(80)
    raise AssertionError(message)
def idle():return not rpc('Player.GetActivePlayers') and all(
    rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def same():
    if not any(p.get('playerid')==1 and p.get('type')=='video' for p in rpc('Player.GetActivePlayers')):return False
    row=rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid'])).get('item',{})
    return row.get('type')==fixture['kind'] and row.get('id')==fixture['identity'] and (
        fixture['kind']!='episode' or row.get('tvshowid')==fixture['show_id'])
def props():return rpc('Player.GetProperties',dict(playerid=1,properties=['time','totaltime','speed','canseek']))
def milliseconds(clock):return ((clock['hours']*60+clock['minutes'])*60+clock['seconds'])*1000+clock['milliseconds']
def opened():return label('Window(Home).Property(AsterVideo.ScrubOpen)')=='true'
def launch():
    if xbmc.getCondVisibility('Window.IsVisible(11125)'):xbmc.executebuiltin('Dialog.Close(11125)');xbmc.sleep(300)
    if integrated:
        if not xbmc.getCondVisibility('Window.IsVisible(videoosd)'):press('osd')
        until(lambda:xbmc.getCondVisibility('Window.IsVisible(videoosd)') and focus(602),'osd-ready')
        press('up');until(lambda:focus(7200),'interactive-bar-reachable');select()
    else:
        xbmc.executebuiltin('Dialog.Close(VideoOSD)');xbmc.sleep(200)
        xbmc.executebuiltin('RunScript(/storage/.aster-staging/'+name+'/default.py)')
    until(lambda:opened() and focus(10),'scrub-ready')
def back_to_osd():until(lambda:not opened() and xbmc.getCondVisibility('Window.IsVisible(videoosd)') and focus(602),'return-existing-osd')
require(idle() and not label('Window(Home).Property(AsterSeries.PreviewWindow)') and not opened(),'idle-required')
require(not (root/'unresolved-seek.json').exists(),'no-uncertain-seek')
if '--movie' in sys.argv:
    excluded={int(arg[10:]) for arg in sys.argv if arg.startswith('--exclude=') and arg[10:].isdecimal()}
    require(len(excluded)<=10,'bounded-fixture-exclusions')
    movies=rpc('VideoLibrary.GetMovies',dict(properties=['playcount','resume','runtime'],filter=dict(field='playcount',operator='greaterthan',value='0'),
        limits=dict(start=0,end=100),sort=dict(method='lastplayed',order='descending'))).get('movies',[])
    movie=next((m for m in movies if type(m.get('movieid')) is int and m['movieid']>0 and m['movieid'] not in excluded and m.get('playcount',0)>0
        and m.get('runtime',0)>120 and not m.get('resume',{}).get('position')),None)
    require(movie is not None,'watched-movie-fixture-required')
    fixture=dict(kind='movie',identity=movie['movieid'],watched=True)
detail_method='VideoLibrary.Get'+fixture['kind'].title()+'Details';identity_key=fixture['kind']+'id';detail_key=fixture['kind']+'details'
row=rpc(detail_method,{identity_key:fixture['identity'],'properties':['playcount','resume']}).get(detail_key,{})
require(row.get('playcount',0)>0 and not row.get('resume',{}).get('position'),'watched-zero-resume-required')
passed=False;error_code=None;checks=[];metrics={};samples=[]
try:
    xbmc.executebuiltin('ActivateWindow(Home)')
    rpc('Player.Open',dict(item={identity_key:fixture['identity']},options=dict(resume=False)))
    until(lambda:same() and props()['canseek'] is True and milliseconds(props()['totaltime'])>120000,'fixture-playing')
    xbmc.executebuiltin('ActivateWindow(fullscreenvideo)');until(lambda:xbmcgui.getCurrentWindowId()==12005,'fullscreen')
    until(lambda:milliseconds(props()['time'])>1500,'fixture-clock-ready')
    press('pause');until(lambda:props()['speed']==0,'paused-fixture')
    original=milliseconds(props()['time']);launch()
    start=int(label('Window(Home).Property(AsterVideo.ScrubTarget)'))
    for _ in range(4):press('right');xbmc.sleep(100)
    until(lambda:int(label('Window(Home).Property(AsterVideo.ScrubTarget)'))==start+20000,'preview-target-moves')
    require(abs(milliseconds(props()['time'])-original)<1000 and props()['speed']==0,'preview-does-not-seek-or-unpause')
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/video-scrub-native.png)');xbmc.sleep(350)
    press('back');back_to_osd()
    require(same() and abs(milliseconds(props()['time'])-original)<1000 and props()['speed']==0,'cancel-no-seek-no-stop')
    checks.append('paused-preview-and-back-cancel-zero-clock-change')
    launch();start=int(label('Window(Home).Property(AsterVideo.ScrubTarget)'))
    for _ in range(3):press('right');xbmc.sleep(100)
    target=start+15000;until(lambda:int(label('Window(Home).Property(AsterVideo.ScrubTarget)'))==target,'paused-target')
    select();back_to_osd()
    until(lambda:same() and abs(milliseconds(props()['time'])-target)<=5000 and props()['speed']==0,'paused-apply-retains-pause')
    metrics['paused_target_ms']=target;metrics['paused_actual_ms']=milliseconds(props()['time'])
    require(not (root/'unresolved-seek.json').exists(),'paused-seek-confirmed')
    checks.append('absolute-seek-and-paused-state-retained')
    press('back');until(lambda:not xbmc.getCondVisibility('Window.IsVisible(videoosd)') and same(),'osd-back-keeps-video')
    press('pause');until(lambda:props()['speed']==1,'playing-fixture')
    launch();start=int(label('Window(Home).Property(AsterVideo.ScrubTarget)'));press('right');xbmc.sleep(100)
    target=start+5000;select();back_to_osd()
    until(lambda:same() and abs(milliseconds(props()['time'])-target)<=5000 and props()['speed']==1,'playing-seek-retains-play')
    after=milliseconds(props()['time']);until(lambda:milliseconds(props()['time'])>=after+1500,'playing-clock-advances')
    require(not (root/'unresolved-seek.json').exists(),'playing-seek-confirmed')
    checks.append('playing-apply-and-clock-advance')
    press('back');until(lambda:not xbmc.getCondVisibility('Window.IsVisible(videoosd)') and same(),'close-osd-only')
    press('back');until(lambda:idle() and not opened(),'fullscreen-back-still-stops')
    checks.append('existing-fullscreen-back-stop')
    require(rpc(detail_method,{identity_key:fixture['identity'],'properties':['playcount']})[detail_key]['playcount']>0,'watched-state-retained')
    passed=True
except Exception as error:
    value=str(error);error_code=value if re.fullmatch('[a-z0-9-]{1,100}',value) else type(error).__name__
    raise
finally:
    if opened():press('back');xbmc.sleep(500)
    if not passed and same():rpc('Player.Stop',dict(playerid=1))
    until(lambda:not same(),'fixture-finished')
    if not rpc('Player.GetActivePlayers'):
        until(idle,'native-idle-cleanup',10)
    clean=idle() and not opened()
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    path=root/('native-scrub-'+str(time.time_ns())+'.json')
    with path.open('x') as output:json.dump(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        stage=name,integrated=integrated,media_kind=fixture['kind'],checks=checks,error=error_code,metrics=metrics,idle_empty=clean,
        expected_identity=fixture['identity'],samples=samples[:25],
        natural_native_progress_only=True,no_manual_history_writes=True),output)
    path.chmod(0o600);require(clean,'scrub-recovery-required')
