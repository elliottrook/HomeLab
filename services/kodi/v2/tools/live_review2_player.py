"""HP normal series/OSD acceptance. One existing fixture, owned Back cleanup."""
import fcntl,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-review2-20261025')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
home=xbmcgui.Window(10000);result=dict(passed=False,checks_enforced=True);phase='preflight';started=False
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Player.GetItem','Player.GetProperties','Input.ExecuteAction'),'native-read-input-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request');return reply['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,code,timeout=45):
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
def owned():
    return bool(rpc('Player.GetActivePlayers')) and rpc('Player.GetItem',dict(playerid=1)).get('item',{}).get('id')==expected
def shot(name):xbmc.executebuiltin('TakeScreenshot('+str(root/(name+'.png'))+')');xbmc.sleep(400)
try:
    fixture=json.loads(Path('/storage/.aster-checkpoints/aster-series-playback-20261024/fixture.json').read_text())['fixture']
    if '--resume-osd' in sys.argv:
        require(home.getProperty('AsterSeries.PreviewWindow') and rpc('Player.GetActivePlayers'),'owned-series-required')
        item=rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid']))['item']
        require(item.get('tvshowid')==fixture['show_id'],'fixture-show-required');expected=item['id'];started=True
        result['resume_owned_osd_test']=True
    else:
        require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-required')
        phase='series';xbmc.executebuiltin('RunScript(/storage/.aster-staging/aster-series-preview18/default.py,'+str(fixture['show_id'])+',play)')
        until(lambda:home.getProperty('AsterSeries.PreviewWindow') and xbmc.getInfoLabel('Window.Property(Series.Ready)')=='true','series-ready')
        if xbmc.getInfoLabel('Window.Property(Series.Multiple)')=='true':
            focus(300,0);xbmc.sleep(300);press('up')
            until(lambda:xbmc.getCondVisibility('Control.HasFocus(201)'),'up-from-first')
            select();until(lambda:xbmc.getCondVisibility('Control.HasFocus(301)'),'season-inline-focus');shot('season-dropdown')
            select();until(lambda:xbmc.getCondVisibility('Control.HasFocus(300)'),'season-return')
            result['season_dropdown_up_and_select']=True
        expected=int(xbmc.getInfoLabel('Container(300).ListItem.Property(EpisodeId)'))
        phase='play';select();started=True
        until(lambda:owned() and xbmcgui.getCurrentWindowId()==12005,'owned-fullscreen')
    for identity,title in ((7100,'Soundtrack'),(7101,'Subtitles'),(7102,'Video quality')):
        phase=title
        if not xbmc.getCondVisibility('Window.IsVisible(videoosd)'):press('osd')
        until(lambda:xbmc.getCondVisibility('Window.IsVisible(videoosd)'),'osd')
        focus(identity);select()
        def menu_ready():
            dialog=xbmcgui.getCurrentWindowDialogId()
            return dialog not in (0,9999,12901) and xbmcgui.Window(dialog).getProperty('Compact.Title')==title
        until(menu_ready,'compact-menu-'+title)
        dialog=xbmcgui.getCurrentWindowDialogId();window=xbmcgui.Window(dialog)
        until(lambda:xbmc.getInfoLabel('Container(10).NumItems') not in ('','0'),'nonempty-menu',5)
        if identity==7101:require(xbmc.getInfoLabel('Container(10).ListItemAbsolute(0).Label').startswith('Subtitles:'),'toggle-first')
        shot('osd-'+str(identity));press('back')
        until(lambda:owned() and xbmcgui.getCurrentWindowDialogId()!=dialog,'menu-back-keeps-media')
        if xbmc.getCondVisibility('Window.IsVisible(videoosd)'):press('back')
        until(lambda:owned() and not xbmc.getCondVisibility('Window.IsVisible(videoosd)'),'osd-dismiss')
        result[title]=True
    phase='exit';press('back')
    until(lambda:idle() and bool(home.getProperty('AsterSeries.PreviewWindow')),'owned-back-stops')
    until(lambda:home.getProperty('AsterSeries.PreviewWindow').isdecimal() and xbmcgui.getCurrentWindowId()==int(home.getProperty('AsterSeries.PreviewWindow')),'series-visible-after-stop')
    press('back');until(lambda:idle() and not home.getProperty('AsterSeries.PreviewWindow'),'series-close')
    xbmc.executebuiltin('ActivateWindow(Home)');result['passed']=True
except Exception as error:
    result.update(phase=phase,code=str(error) if isinstance(error,RuntimeError) else type(error).__name__,
                  window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId())
finally:
    result['idle_empty']=idle()
    path=root/('native-player-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
    os.close(lock)
