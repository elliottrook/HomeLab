"""Native HP search preview remote paths; no playback or library mutations."""
import json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui

def require(value,message):
    if not value:raise RuntimeError(message)

require(os.uname().nodename=='AsterTV','hp-only')
stage=sys.argv[1] if len(sys.argv)==2 else 'aster-global-search-ui1'
require(stage in ('aster-global-search-ui1','aster-global-search-ui2'),'known-search-stage')
HOME=xbmcgui.Window(10000)
def prop(key):return HOME.getProperty('AsterSearch.'+key)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Input.SendText'},'native-test-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request-failed');return reply['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,message):
    end=time.monotonic()+20
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
checks=[];passed=False;failure=None
try:
    require(xbmcgui.getCurrentWindowId()==10000 and idle() and not prop('Open'),'idle-home-required')
    xbmc.executebuiltin('RunScript(/storage/.aster-staging/'+stage+'/default.py)')
    until(lambda:prop('Ready')=='true','preview-ready')
    require(xbmcgui.getCurrentWindowDialogId()==11127,'native-preview-dialog')
    require('Search' in prop('Query'),'initial-search-hint')
    press('select');until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'native-keyboard')
    rpc('Input.SendText',dict(text='a',done=True))
    until(lambda:prop('Query')=='a' and prop('Ready')=='true','grouped-results-ready')
    # addItem completion precedes the render thread's Container labels.
    until(lambda:xbmc.getInfoLabel('Container(20).NumItems')=='5','five-source-groups')
    until(lambda:int(xbmc.getInfoLabel('Container(30).NumItems') or 0)>0,'actual-local-matches')
    checks.extend(['native-keyboard-query','five-source-groups','local-matches'])
    press('down');until(lambda:xbmc.getCondVisibility('Control.HasFocus(20)'),'group-focus')
    press('down');until(lambda:'first 500 of' in prop('Status'),'movie-truncation-visible')
    press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)'),'result-focus')
    selected=xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')
    require(selected.isdecimal(),'positive-indexed-result')
    # Dynamic ControlList rows do not dispatch XML onclick on this Kodi build.
    # This stage qualifies browsing only, not a result-opening integration.
    press('select');xbmc.sleep(300)
    require(idle(),'no-autoplay')
    checks.extend(['remote-groups-and-results','truncation-visible','id-only-result','browse-only-no-autoplay'])
    screenshot='native-search-view-'+str(time.time_ns())+'.png'
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-global-search-20261024/'+screenshot+')')
    xbmc.sleep(700)
    xbmc.executebuiltin('SetFocus(10)');press('select')
    until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'keyboard-reopen')
    press('back');until(lambda:xbmcgui.getCurrentWindowDialogId()==11127,'keyboard-cancel-return')
    require(prop('Query')=='a' and xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')==selected,'cancel-retains-results')
    press('select');until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'empty-query-keyboard')
    rpc('Input.SendText',dict(text='AsterNoMatchQualificationXZQ901728',done=True))
    until(lambda:prop('Query').startswith('AsterNoMatch') and prop('Ready')=='true','no-match-ready')
    until(lambda:prop('Status')=='No matching titles in this group.' and xbmc.getInfoLabel('Container(30).NumItems')=='0','explicit-empty-state')
    checks.extend(['keyboard-cancel-preserves-results','explicit-no-match'])
    press('back');until(lambda:not prop('Open') and xbmcgui.getCurrentWindowDialogId()!=11127,'back-closes-preview')
    require(xbmcgui.getCurrentWindowId()==10000 and idle(),'home-and-idle-preserved')
    checks.append('back-home-and-empty-queues');passed=True
except Exception as error:
    failure=str(error) if str(error).isascii() and len(str(error))<100 else 'native-test-failed'
finally:
    if xbmcgui.getCurrentWindowDialogId()==10103:press('back');xbmc.sleep(200)
    if xbmcgui.getCurrentWindowDialogId()==11127:press('back');xbmc.sleep(300)
    clean=idle() and not prop('Open')
    path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('native-ui-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(stage=stage,passed=passed,checks_enforced=True,checks=checks,failure=failure,idle_empty=clean,screenshot=locals().get('screenshot')),handle)
    path.chmod(0o600)
    require(clean,'search-ui-recovery-required')
