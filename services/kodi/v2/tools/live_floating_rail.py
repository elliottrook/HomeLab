"""HP idle-only floating-rail navigation and screenshot test. No media writes."""
import json,os,re,sys,time
from pathlib import Path
import xbmc,xbmcgui

def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
def rpc(method,params=None):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-rpc-failed');return reply['result']
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def until(check,message):
    end=time.monotonic()+35
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(70)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def setfocus(identity):
    xbmc.executebuiltin('SetFocus('+str(identity)+')');until(lambda:focus(identity),'focus-'+str(identity))
def picture(name):
    xbmc.sleep(600);xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/rail-'+name+'.png)');xbmc.sleep(300)
def idle():return not rpc('Player.GetActivePlayers') and rpc('Playlist.GetItems',dict(playlistid=0,limits=dict(start=0,end=1)))['limits']['total']==0
def music_ready():return xbmcgui.getCurrentWindowId()==11113 and xbmcgui.Window(11113).getProperty('AsterMusic.LoadReady')=='true' and focus(500)

require(idle(),'idle-empty-required')
checks=[];passed=False;error_code=None
try:
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'media-home')
    setfocus(130);picture('media-closed');press('left');until(lambda:focus(9001),'left-enters-real-media-route')
    require(not xbmc.getInfoLabel('Control.GetLabel(8999)'),'no-chevron')
    picture('media-open')
    for identity in (9002,9003,9004,9007,9005):
        press('down');until(lambda:focus(identity),'rail-down-'+str(identity))
    for identity in (9007,9004,9003,9002,9001):
        press('up');until(lambda:focus(identity),'rail-up-'+str(identity))
    press('right');until(lambda:focus(100),'right-returns-to-media')
    checks.append('media-left-immediate-route-all-six-directions-and-return')
    xbmc.executebuiltin('SetFocus(8999)');until(lambda:focus(9001),'reopen-media');press('down');until(lambda:focus(9002),'books-route');select()
    until(lambda:xbmcgui.getCurrentWindowId()==11110,'books-page');xbmc.sleep(600)
    xbmc.executebuiltin('SetFocus(8999)');until(lambda:focus(9002),'books-immediate-current-route');picture('books-open')
    press('right');until(lambda:not any(focus(i) for i in (8999,9001,9002,9003,9004,9005,9007,9008)),'books-right-to-content')
    checks.append('books-current-route-and-content-return')
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-for-music')
    setfocus(9007);select();until(music_ready,'normal-music-ready');picture('music-closed')
    xbmc.executebuiltin('Control.SetFocus(500,0,absolute)');until(lambda:focus(500),'music-tile')
    press('left');until(lambda:focus(9007),'music-left-direct-current-route');picture('music-open')
    press('right');until(lambda:focus(500),'music-right-to-same-grid')
    checks.append('music-left-and-right-preserved')
    setfocus(114);select();until(lambda:xbmc.getInfoLabel('Window.Property(Lab.View)')=='genres' and focus(500),'genre-browser')
    press('left');until(lambda:focus(9007),'genre-floating-mini-rail');picture('genres-open')
    press('right');until(lambda:focus(500),'genre-return-to-grid');press('back')
    until(lambda:xbmcgui.getCurrentWindowId()==11113 and not xbmc.getInfoLabel('Window(Home).Property(AsterV2Lab.Window)'),'genre-back-to-music')
    checks.append('genre-mini-rail-and-source-return')
    require(idle(),'no-playback-side-effects');passed=True
except Exception as error:
    value=str(error);error_code=value if re.fullmatch('[a-z0-9-]{1,100}',value) else type(error).__name__
    raise
finally:
    if xbmc.getInfoLabel('Window(Home).Property(AsterV2Lab.Window)'):press('back');xbmc.sleep(500)
    if idle():xbmc.executebuiltin('ActivateWindow(Home)')
    path=Path('/storage/.aster-checkpoints/aster-floating-rail-20261024')/('native-'+str(time.time_ns())+'.json')
    with path.open('x') as output:json.dump(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        checks=checks,error=error_code,idle_empty=idle(),no_media_or_server_writes=True),output)
    path.chmod(0o600)
