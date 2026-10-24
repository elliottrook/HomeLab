"""Native read-only HP series preview acceptance. No playback or server writes."""
import importlib.util,json,os,re,sys,time
from pathlib import Path
import xbmc,xbmcgui

def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
name=sys.argv[1] if len(sys.argv)>1 else 'aster-series-preview1'
require(re.fullmatch(r'aster-series-preview[1-9][0-9]*',name) is not None,'valid-stage-required')
stage=Path('/storage/.aster-staging')/name
sys.path.insert(0,str(stage/'resources/lib'))
from series_adapter import read_series
from series_view import SeriesSelection
spec=importlib.util.spec_from_file_location('aster_accepted_preview_policy','/storage/.kodi/addons/plugin.video.asterhome/library.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)

def rpc(method,params=None):
    require(method in {'VideoLibrary.GetTVShows','VideoLibrary.GetTVShowDetails','VideoLibrary.GetEpisodes',
        'Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction'},'native-test-method-boundary')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-rpc-failed');return result['result']
def label(key):return xbmc.getInfoLabel(key)
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,message):
    deadline=time.monotonic()+35
    while time.monotonic()<deadline:
        if check():return
        xbmc.sleep(80)
    raise AssertionError(message)
def setfocus(identity):
    xbmc.executebuiltin('SetFocus('+str(identity)+')');until(lambda:focus(identity),'focus-'+str(identity))
def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def opened():return bool(label('Window(Home).Property(AsterSeries.PreviewWindow)'))
def row_selected(identity):
    return (label('Window.Property(Series.SelectedId)')==str(identity)
        and label('Container(300).ListItem.Property(EpisodeId)')==str(identity)
        and label('Container(300).ListItem.Property(Selected)')=='true')

require(idle() and not opened(),'idle-empty-required')
checks=[];counts=[];passed=False;error_code=None
try:
    shows=rpc('VideoLibrary.GetTVShows',dict(properties=['title','season','episode'],limits=dict(start=0,end=250),sort=dict(method='title',order='ascending'))).get('tvshows',[])
    candidates=[]
    for multiple in (True,False):
        found=None
        for show in shows:
            seasons=show.get('season');episodes=show.get('episode')
            if type(seasons) is not int or type(episodes) is not int or episodes<2 or ((seasons>1)!=multiple):continue
            snapshot=read_series(rpc,show['tvshowid'],policy.next_up_item)
            if snapshot.page.show_season_picker==multiple and snapshot.page.seasons and len(snapshot.page.seasons[0].episodes)>=2:
                found=(show['tvshowid'],snapshot);break
        require(found is not None,'single-and-multiseason-fixtures-required');candidates.append(found)
    for number,(show_id,snapshot) in enumerate(candidates):
        xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-source');setfocus(130)
        xbmc.executebuiltin('RunScript('+str(stage/'default.py')+','+str(show_id)+')')
        until(lambda:opened() and focus(300) and bool(label('Window.Property(Series.SelectedId)')),'preview-ready')
        require(label('Window.Property(Series.Mode)')=='HP SERIES PREVIEW · NO PLAYBACK','preview-labelled')
        selected=SeriesSelection(snapshot.page,snapshot.page.primary_episode_id)
        require(row_selected(selected.episode.episode_id),'primary-exact-id-focus')
        # First group gives adjacent rows even if the resume lives elsewhere.
        if selected.season!=0:
            setfocus(201);select();until(lambda:label('Control.GetLabel(1)')=='Choose season','season-dialog')
            for _ in range(selected.season):press('up')
            select()
            until(lambda:focus(300) and label('Window.Property(Series.SeasonIndex)')=='0','first-season')
        xbmc.executebuiltin('Control.SetFocus(300,0,absolute)')
        first,second=snapshot.page.seasons[0].episodes[:2]
        until(lambda:row_selected(first.episode_id),'first-row')
        press('down');until(lambda:row_selected(second.episode_id),'down-adjacent-row')
        press('up');until(lambda:row_selected(first.episode_id),'up-adjacent-row')
        press('down');until(lambda:row_selected(second.episode_id),'remember-second-row')
        require(xbmc.getCondVisibility('Control.IsVisible(201)')==snapshot.page.show_season_picker,'season-picker-visibility')
        xbmc.sleep(400);xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/series-preview-focus-'+str(number)+'.png)');xbmc.sleep(500)
        if snapshot.page.show_season_picker:
            press('left');until(lambda:focus(201),'left-to-season-picker');select()
            until(lambda:label('Control.GetLabel(1)')=='Choose season','season-dialog')
            press('down');select()
            until(lambda:focus(300) and label('Window.Property(Series.SeasonIndex)')=='1','second-season')
            setfocus(201);select();until(lambda:label('Control.GetLabel(1)')=='Choose season','return-season-dialog')
            press('up');select()
            until(lambda:focus(300) and row_selected(second.episode_id),'exact-season-focus-restored')
            checks.append('season-round-trip-exact-id')
        select();until(lambda:label('Control.GetLabel(1)')=='Episode preview','episode-details-no-autoplay')
        require(idle(),'details-no-player-or-queue')
        press('back');until(lambda:opened() and focus(300),'dialog-back-retains-page');xbmc.sleep(400)
        press('back');until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000 and focus(130),'back-restores-source-focus')
        counts.append(sum(len(group.episodes) for group in snapshot.page.seasons));checks.append('multiple-seasons' if number==0 else 'single-season-simplified')
    require(idle(),'unchanged-empty-player-and-queues');passed=True
except Exception as error:
    value=str(error);error_code=value if re.fullmatch('[a-z0-9-]{1,100}',value) else type(error).__name__
    raise
finally:
    if opened():
        if label('Control.GetLabel(1)') in ('Choose season','Episode preview'):press('back');xbmc.sleep(500)
        press('back');xbmc.sleep(700)
    clean=idle() and not opened()
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    evidence=Path('/storage/.aster-checkpoints/aster-series-preview-20261024')
    path=evidence/('native-'+str(time.time_ns())+'.json')
    with path.open('x') as output:json.dump(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        checks=checks,episode_counts=counts,error=error_code,idle_empty=clean,no_media_or_server_writes=True),output)
    path.chmod(0o600);require(clean,'preview-recovery-required')
