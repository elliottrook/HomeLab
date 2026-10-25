"""HP third-review screenshots/focus/season-tail checks; no media starts."""
import fcntl,json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-review3-20261025');home=xbmcgui.Window(10000)
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
result=dict(passed=False,checks_enforced=True,no_playback=True);phase='home'
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Input.SendText','VideoLibrary.GetTVShowDetails'),'native-input-read-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-read');return reply['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,code,timeout=40):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if check():return
        if xbmc.Monitor().waitForAbort(.1):raise RuntimeError('aborted')
    raise RuntimeError(code)
def focus(i,index=None):
    xbmc.executebuiltin('SetFocus('+str(i)+')' if index is None else 'Control.SetFocus('+str(i)+','+str(index)+',absolute)')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(i)+')'),'focus-'+str(i))
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def shot(name):xbmc.executebuiltin('TakeScreenshot('+str(root/(name+'.png'))+')');xbmc.sleep(600)
def prop(k):return home.getProperty('AsterSearch.'+k)
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home')
    focus(133);shot('media-header-archive-movies');focus(135);shot('search-gold')
    focus(9001);shot('short-side-rail');press('right');focus(135);select()
    until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true','search-ready')
    focus(10);select();until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'keyboard');shot('keyboard-depth')
    title=rpc('VideoLibrary.GetTVShowDetails',dict(tvshowid=126,properties=['title']))['tvshowdetails']['title']
    rpc('Input.SendText',dict(text=title,done=True));until(lambda:prop('Ready')=='true' and prop('Query')==title,'query-ready')
    focus(20,0);press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)'),'result-focus')
    require(xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')=='126','exact-show-result')
    phase='direct-series';select()
    until(lambda:home.getProperty('AsterSeries.PreviewWindow') and prop('Handoff')=='child','direct-series-ready')
    require(idle(),'no-autoplay');focus(300,0);xbmc.sleep(250);press('up')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus(201)'),'season-button');select()
    def season_focus():return next((i for i in range(311,316) if xbmc.getCondVisibility('Control.HasFocus('+str(i)+')')),None)
    until(lambda:season_focus() is not None,'season-menu')
    for _ in range(25):press('down');xbmc.sleep(80)
    xbmc.sleep(400);last=xbmc.getInfoLabel('Control.GetLabel('+str(season_focus())+')')
    require(last=='Season 4','actual-last-season-selected')
    require(sum(xbmc.getCondVisibility('Control.IsVisible('+str(i)+')') for i in range(311,316))==4,'four-real-season-rows');shot('season-last-entry')
    press('down');xbmc.sleep(300);require(xbmc.getInfoLabel('Control.GetLabel('+str(season_focus())+')')==last,'season-end-no-wrap')
    select();until(lambda:xbmc.getInfoLabel('Window.Property(Series.Season)')=='Season 4' and xbmc.getCondVisibility('Control.HasFocus(300)'),'season-four-selected')
    require(idle(),'season-change-no-autoplay')
    press('up');until(lambda:xbmc.getCondVisibility('Control.HasFocus(201)'),'season-return-up');select()
    until(lambda:season_focus() is not None,'season-reopened')
    press('back');until(lambda:xbmc.getCondVisibility('Control.HasFocus(201)'),'season-back')
    press('back');until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true' and not prop('Handoff'),'exact-search-return')
    require(xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')=='126','search-cursor-retained')
    press('back');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-return')
    result.update(passed=True,season_tail_no_blank_or_wrap=True,season_four_selection=True,exact_show126_search_return=True,keyboard_opened=True)
except Exception as error:
    result.update(phase=phase,code=str(error) if isinstance(error,RuntimeError) else type(error).__name__,window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId())
finally:
    result['idle_empty']=idle();path=root/('native-ui-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600);os.close(lock)
