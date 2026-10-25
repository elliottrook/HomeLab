"""HP exact-ID series player test using native actions; no manual history writes."""
import importlib.util,json,os,re,sys,time
from pathlib import Path
import xbmc,xbmcgui,xbmcaddon

def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
name=sys.argv[1] if len(sys.argv)>1 else 'aster-series-preview10'
require(re.fullmatch(r'aster-series-preview[1-9][0-9]*',name),'valid-stage')
stage=Path('/storage/.aster-staging')/name
sys.path.insert(0,str(stage/'resources/lib'))
from series_adapter import read_series
spec=importlib.util.spec_from_file_location('aster_series_native_policy','/storage/.kodi/addons/plugin.video.asterhome/library.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
root=Path('/storage/.aster-checkpoints/aster-series-playback-20261024')
fixtures=json.loads((root/'fixture.json').read_text())
rewind=xbmcaddon.Addon('plugin.video.jellyfin').getSettingInt('resumeJumpBack')
require(type(rewind) is int and 0<=rewind<=120,'configured-resume-rewind')

def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Player.GetItem','Player.GetProperties',
        'Player.Stop','Input.ExecuteAction','VideoLibrary.GetEpisodeDetails','VideoLibrary.GetTVShowDetails','VideoLibrary.GetEpisodes'},'native-test-boundary')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-rpc-failed');return result['result']
def label(key):return xbmc.getInfoLabel(key)
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,message,seconds=35):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if 'trace' in globals():
            identity=label('Window(Home).Property(AsterSeries.PreviewWindow)')
            state=[xbmcgui.getCurrentWindowId(),bool(rpc('Player.GetActivePlayers')),
                label('Window('+identity+').Property(Series.Playback)') if identity else '',
                label('Window(Home).Property(AsterNextEpisode.Running)')]
            if not trace or trace[-1]['state']!=state:
                trace.append(dict(at=round(time.monotonic()-started,2),state=state,check=message))
        if check():return
        xbmc.sleep(80)
    raise AssertionError(message)
def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def setfocus(identity):
    xbmc.executebuiltin('SetFocus('+str(identity)+')');until(lambda:focus(identity),'focus-'+str(identity))
def selected(identity):
    return label('Window.Property(Series.SelectedId)')==str(identity) and label('Container(300).ListItem.Property(EpisodeId)')==str(identity)
def item():
    if not rpc('Player.GetActivePlayers'):return {}
    return rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid'])).get('item',{})
def same(fixture):
    value=item();return value.get('type')=='episode' and value.get('id')==fixture['episode_id'] and value.get('tvshowid')==fixture['show_id']
def props():return rpc('Player.GetProperties',dict(playerid=1,properties=['time','totaltime','speed']))
def clock(value):
    return value.get('hours',0)*3600+value.get('minutes',0)*60+value.get('seconds',0)+value.get('milliseconds',0)/1000

require(idle() and not label('Window(Home).Property(AsterSeries.PreviewWindow)'),'idle-empty-required')
require(not (root/'unresolved-start.json').exists(),'no-series-recovery')
passed=False;error_code=None;checks=[];results=[];current=None;diagnostic={};trace=[];started=time.monotonic()
scrub_stage=next((arg[14:] for arg in sys.argv if arg.startswith('--scrub-stage=')),None)
if scrub_stage:require(re.fullmatch(r'aster-video-scrub[1-9][0-9]*',scrub_stage),'valid-scrub-stage')
try:
    cases=[fixtures['fixture']]
    if fixtures.get('resume_fixture'):cases.append(fixtures['resume_fixture'])
    for number,current in enumerate(cases):
        snapshot=read_series(rpc,current['show_id'],policy.next_up_item)
        target=snapshot.page.restore(current['episode_id']);require(target is not None,'fixture-indexed')
        xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'source-home');setfocus(130)
        xbmc.executebuiltin('RunScript('+str(stage/'default.py')+','+str(current['show_id'])+',play)')
        until(lambda:bool(label('Window(Home).Property(AsterSeries.PreviewWindow)')) and focus(300)
            and label('Window.Property(Series.Ready)')=='true'
            and label('Container(300).ListItem.Property(EpisodeId)')==label('Window.Property(Series.SelectedId)'),'series-player-ready')
        require(label('Window.Property(Series.Mode)').startswith('TV SERIES'),'normal-player-mode')
        require(idle(),'series-does-not-autoplay')
        season=int(label('Window.Property(Series.SeasonIndex)'))
        if season!=target[0]:
            setfocus(201);select();until(lambda:label('Control.GetLabel(1)')=='Choose season','choose-fixture-season')
            for _ in range(abs(target[0]-season)):press('down' if target[0]>season else 'up')
            select();until(lambda:focus(300) and label('Window.Property(Series.SeasonIndex)')==str(target[0])
                and label('Window.Property(Series.Ready)')=='true','fixture-season')
        xbmc.executebuiltin('Control.SetFocus(300,'+str(target[1])+',absolute)')
        until(lambda:selected(current['episode_id']),'exact-fixture-row')
        before_details=rpc('VideoLibrary.GetEpisodeDetails',dict(episodeid=current['episode_id'],properties=['resume'])).get('episodedetails',{})
        before=before_details.get('resume',{}).get('position',0) or 0
        require(bool(before)==bool(current.get('resume_seconds')),'fixture-resume-shape-retained')
        select()
        until(lambda:same(current) and xbmcgui.getCurrentWindowId()==12005 and clock(props().get('totaltime',{}))>0,'episode-fullscreen-start',45)
        # Metadata/fullscreen can precede Kodi's asynchronous bookmark seek.
        # Compare to the fresh bookmark, not the original discovery snapshot.
        until(lambda:before-5<=clock(props().get('time',{}))<=before+60,'stored-resume-start-position',12)
        initial=clock(props().get('time',{}))
        until(lambda:label('Window(Home).Property(AsterNextEpisode.CurrentId)')==str(current['episode_id'])
            and label('Window(Home).Property(AsterNextEpisode.Running)')=='true','existing-intro-outro-monitor')
        until(lambda:clock(props().get('time',{}))>=initial+2,'playback-clock-advances')
        press('pause');until(lambda:props()['speed']==0,'native-pause');press('pause');until(lambda:props()['speed']==1,'native-resume')
        if number==0:
            if xbmc.getCondVisibility('Window.IsVisible(11125)'):xbmc.executebuiltin('Dialog.Close(11125)');xbmc.sleep(300)
            press('osd');until(lambda:xbmc.getCondVisibility('Window.IsVisible(videoosd)') and focus(602),'existing-osd')
            press('up')
            if xbmc.getCondVisibility('Control.IsVisible(7200)'):
                until(lambda:focus(7200),'seek-entry-reachable');press('up')
            until(lambda:focus(7100),'audio-reachable');press('right');until(lambda:focus(7101),'subtitles-reachable')
            press('right');until(lambda:focus(7102),'quality-reachable');press('back')
            until(lambda:not xbmc.getCondVisibility('Window.IsVisible(videoosd)') and same(current),'osd-back-keeps-playback')
            checks.append('native-osd-audio-subtitles-quality-navigation')
        if number==0 and ('--scrub' in sys.argv or scrub_stage):
            if scrub_stage:
                xbmc.executebuiltin('RunScript(/storage/.aster-staging/'+scrub_stage+'/default.py)')
            else:
                press('osd');until(lambda:xbmc.getCondVisibility('Window.IsVisible(videoosd)') and focus(602),'scrub-osd')
                press('up');until(lambda:focus(7200),'scrub-bar-entry');select()
            until(lambda:label('Window(Home).Property(AsterVideo.ScrubOpen)')=='true','series-scrub-open')
            start=int(label('Window(Home).Property(AsterVideo.ScrubTarget)'))
            press('right');xbmc.sleep(100);press('right');xbmc.sleep(100)
            until(lambda:label('Window(Home).Property(AsterVideo.ScrubTarget)')==str(start+10000),'series-scrub-preview')
            select();until(lambda:not label('Window(Home).Property(AsterVideo.ScrubOpen)')
                and xbmc.getCondVisibility('Window.IsVisible(videoosd)') and same(current),'series-scrub-applied')
            until(lambda:abs(clock(props()['time'])-(start+10000)/1000)<=5,'series-scrub-clock')
            press('back');until(lambda:not xbmc.getCondVisibility('Window.IsVisible(videoosd)') and same(current),'series-scrub-osd-back')
            checks.append('series-background-video-scrub-and-owned-return')
        if number==0 and '--next' in sys.argv:
            next_id=label('Window(Home).Property(AsterNextEpisode.NextId)')
            require(next_id.isdecimal() and label('Window(Home).Property(AsterNextEpisode.Ready)')=='true','real-next-episode-ready')
            row=next((e for s in snapshot.page.seasons for e in s.episodes if e.episode_id==int(next_id)),None)
            require(row is not None and row.available and row.watched,'already-watched-next-fixture-required')
            next_details=rpc('VideoLibrary.GetEpisodeDetails',dict(episodeid=row.episode_id,properties=['resume'])).get('episodedetails',{})
            before=next_details.get('resume',{}).get('position',0) or 0
            next_fixture=dict(show_id=current['show_id'],episode_id=row.episode_id,watched=True,resume_seconds=before or None)
            if xbmc.getCondVisibility('Window.IsVisible(11125)'):xbmc.executebuiltin('Dialog.Close(11125)');xbmc.sleep(300)
            press('osd');until(lambda:xbmc.getCondVisibility('Window.IsVisible(videoosd)') and focus(602),'next-osd')
            press('right');until(lambda:focus(606),'next-plus30');press('right');until(lambda:focus(607),'next-button-reachable')
            select();current=next_fixture
            until(lambda:same(current) and xbmcgui.getCurrentWindowId()==12005
                and before-5<=clock(props().get('time',{}))<=before+60,'real-next-native-handoff',45)
            initial=clock(props().get('time',{}))
            until(lambda:clock(props().get('time',{}))>=initial+2,'next-clock-advances')
            checks.append('native-next-existing-policy-exact-following-episode')
        if xbmc.getCondVisibility('Window.IsVisible(11125)'):xbmc.executebuiltin('Dialog.Close(11125)');xbmc.sleep(300)
        last_clock=clock(props().get('time',{}))
        press('back')
        until(lambda:idle() and bool(label('Window(Home).Property(AsterSeries.PreviewWindow)')) and focus(300)
            and selected(current['episode_id']),'video-back-stops-and-restores-exact-episode',40)
        xbmc.sleep(1600)
        require(selected(current['episode_id']),'metadata-refresh-preserves-episode')
        require(not (root/'unresolved-start.json').exists(),'no-unresolved-playback')
        press('contextmenu');until(lambda:label('Control.GetLabel(1)')=='Episode information','episode-information')
        press('back');until(lambda:focus(300),'information-back-retains-page');xbmc.sleep(400)
        press('back');until(lambda:idle() and not label('Window(Home).Property(AsterSeries.PreviewWindow)')
            and xbmcgui.getCurrentWindowId()==10000 and focus(130),'page-back-restores-source')
        details=rpc('VideoLibrary.GetEpisodeDetails',dict(episodeid=current['episode_id'],properties=['resume','playcount'])).get('episodedetails',{})
        after=details.get('resume',{}).get('position',0)
        if before:require(last_clock-rewind-5<=after<=last_clock+5 and after>0,'resume-not-cleared-on-exit')
        require((details.get('playcount',0)>0)==current['watched'],'watched-state-not-reset')
        results.append(dict(existing_resume=bool(before),resume_before=before,initial_clock=initial,last_clock=last_clock,
            resume_after=after,configured_resume_rewind=rewind,back_stop=True,exact_return=True))
    checks.extend(['exact-id-native-playback','boolean-resume-existing-bookmark','pause-resume','existing-marker-monitor',
        'fullscreen-back-stop','exact-episode-and-source-focus','no-autoplay-on-entry','metadata-refresh'])
    passed=True
except Exception as error:
    diagnostic=dict(window=xbmcgui.getCurrentWindowId(),fullscreen_active=xbmc.getCondVisibility('Window.IsActive(fullscreenvideo)'),
        marker_running=label('Window(Home).Property(AsterNextEpisode.Running)'),
        marker_id=label('Window(Home).Property(AsterNextEpisode.CurrentId)'),
        player_matches_fixture=bool(current and same(current)))
    value=str(error);error_code=value if re.fullmatch('[a-z0-9-]{1,100}',value) else type(error).__name__
    raise
finally:
    if not passed and current and same(current):rpc('Player.Stop',dict(playerid=1))
    if not passed:
        end=time.monotonic()+15
        while time.monotonic()<end and label('Window(Home).Property(AsterSeries.PreviewWindow)') and idle():
            if str(xbmcgui.getCurrentWindowId())==label('Window(Home).Property(AsterSeries.PreviewWindow)'):
                press('back');xbmc.sleep(1000)
            else:xbmc.sleep(100)
    clean=idle() and not label('Window(Home).Property(AsterSeries.PreviewWindow)')
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    path=root/('native-player-'+str(time.time_ns())+'.json')
    with path.open('x') as output:json.dump(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        stage=name,scrub_stage=scrub_stage,checks=checks,results=results,error=error_code,diagnostic=diagnostic,trace=trace[:120],idle_empty=clean,
        natural_native_progress_only=True,no_manual_history_or_server_api_writes=True),output)
    path.chmod(0o600);require(clean,'series-recovery-required')
