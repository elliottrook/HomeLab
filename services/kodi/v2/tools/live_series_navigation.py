"""HP installed Select route and exact native library return, no playback."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction'},'native-test-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-rpc-failed');return reply['result']
def label(key):return xbmc.getInfoLabel(key)
def until(check,message):
    end=time.monotonic()+25
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise AssertionError(message)
def idle():return not rpc('Player.GetActivePlayers') and all(
    rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def selected():return (label('Container(50).ListItem.DBTYPE'),label('Container(50).ListItem.DBID'))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def press(action):rpc('Input.ExecuteAction',dict(action=action))
require(idle() and not label('Window(Home).Property(AsterSeries.PreviewWindow)'),'idle-required')
passed=False;error_code=None;identity=None;checks=[]
try:
    xbmc.executebuiltin('ActivateWindow(Videos,videodb://tvshows/titles/,return)')
    until(lambda:xbmcgui.getCurrentWindowId()==10025 and label('Container.Content')=='tvshows'
        and int(label('Container(50).NumItems') or 0)>1,'native-tv-library')
    xbmc.executebuiltin('SetFocus(50)');xbmc.sleep(1000)
    for _ in range(8):
        kind,identity=selected()
        if kind=='tvshow' and identity.isdecimal():break
        press('down');xbmc.sleep(250)
    require(kind=='tvshow' and identity.isdecimal(),'verified-real-tv-show')
    select();until(lambda:bool(label('Window(Home).Property(AsterSeries.PreviewWindow)'))
        and label('Window.Property(Series.Mode)').startswith('TV SERIES')
        and label('Window.Property(Series.Ready)')=='true','installed-select-opens-series')
    require(idle(),'no-autoplay-on-tv-selection')
    require(label('Window.Property(Series.Title)') and label('Container(300).ListItem.Property(EpisodeId)').isdecimal(),'episode-page-populated')
    count=int(label('Container(300).NumItems') or 0);require(count>0,'episode-count')
    xbmc.executebuiltin('Control.SetFocus(300,'+str(count-1)+',absolute)');xbmc.sleep(500)
    last=label('Container(300).ListItem.Property(EpisodeId)');require(last.isdecimal(),'last-episode-selected')
    press('down');xbmc.sleep(200);press('down');xbmc.sleep(200)
    require(label('Container(300).ListItem.Property(EpisodeId)')==last
        and xbmc.getCondVisibility('Control.HasFocus(300)'),'last-episode-does-not-wrap')
    checks.append('last-episode-stops-instead-of-wrapping')
    press('back');until(lambda:not label('Window(Home).Property(AsterSeries.PreviewWindow)')
        and xbmcgui.getCurrentWindowId()==10025 and xbmc.getCondVisibility('Control.HasFocus(50)'),'back-native-library')
    require(selected()==('tvshow',identity),'exact-show-focus-preserved')
    checks.extend(['installed-select-dispatch-tv-show','no-autoplay','populated-episode-page','exact-show-and-library-focus'])
    xbmc.executebuiltin('ActivateWindow(Videos,videodb://movies/titles/,return)')
    until(lambda:xbmcgui.getCurrentWindowId()==10025 and label('Container.Content')=='movies','native-movies-retained')
    require(not label('Window(Home).Property(AsterSeries.PreviewWindow)') and idle(),'movies-not-intercepted')
    checks.append('native-movies-navigation-retained');passed=True
except Exception as error:
    value=str(error);error_code=value if value.isascii() and len(value)<100 else type(error).__name__
    raise
finally:
    if label('Window(Home).Property(AsterSeries.PreviewWindow)') and idle():press('back');xbmc.sleep(1000)
    clean=idle() and not label('Window(Home).Property(AsterSeries.PreviewWindow)')
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    path=Path('/storage/.aster-checkpoints/aster-series-integration-20261024')/('native-navigation-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(passed=passed,checks_enforced=True,checks=checks,error=error_code,idle_empty=clean),handle)
    path.chmod(0o600);require(clean,'navigation-recovery-required')
