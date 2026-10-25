"""HP normal Books UI save/resume checks; no direct playback/progress writes."""
import fcntl,importlib.util,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
sys.path.insert(0,'/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib')
from books_progress_reader import Reader
from books_sync import ACCOUNT
spec=importlib.util.spec_from_file_location('audit_bridge','/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib/bridge.py')
bridge_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge_module)
origin,key=bridge_module.load_config(Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/client.json'))
client=bridge_module.Bridge(origin,key);del key
reader=Reader(client.upstream);account=reader.account()
require(account.limited and account.fingerprint==ACCOUNT,'approved-household-account')
home=xbmcgui.Window(10000);player=xbmc.Player();checks=[];phase='preflight';stop_mode='--stop' in sys.argv
tempo_mode='--tempo' in sys.argv
sleep_mode='--sleep' in sys.argv
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Player.GetProperties','Player.SetTempo'),'native-test-input-read-boundary')
    if method=='Player.SetTempo':
        require(tempo_mode and params.get('playerid')==0 and params.get('tempo') in (1.0,1.25)
            and 'url' in globals() and owned(url),'bounded-owned-tempo-probe')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-request');return result['result']
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,code,timeout=35):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(100)
    raise RuntimeError(code)
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def focus(identity,index=None):
    command='SetFocus('+str(identity)+')' if index is None else 'Control.SetFocus('+str(identity)+','+str(index)+',absolute)'
    for _ in range(3):
        xbmc.executebuiltin(command);xbmc.sleep(250)
        if xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'):return
    raise RuntimeError('focus-'+str(identity))
def owned(url):
    try:return player.isPlayingAudio() and player.getPlayingFile()==url
    except Exception:return False
def enter(target):
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-entry')
    xbmc.executebuiltin('ActivateWindow(1110)')
    until(lambda:xbmcgui.getCurrentWindowId()==11110 and xbmc.getInfoLabel('Container(502).NumItems') not in ('','0'),'books-home')
    xbmc.sleep(600)  # Onload population may still be restoring its default rail.
    pill=111 if target['kind']=='audiobook' else 112
    page=11119 if target['kind']=='audiobook' else 11120
    focus(pill);select();until(lambda:xbmcgui.getCurrentWindowId()==page and xbmc.getInfoLabel('Container(500).NumItems') not in ('','0'),'books-kind-page')
    count=int(xbmc.getInfoLabel('Container(500).NumItems'));found=False
    for index in range(min(count,1000)):
        focus(500,index)
        if xbmc.getInfoLabel('Container(500).ListItem.Property(AsterBooks.Id)')==target['item']:found=True;break
    require(found,'exact-title-selected');select()
    until(lambda:xbmcgui.getCurrentWindowId()==10502 and xbmc.getInfoLabel('Container(50).NumItems') not in ('','0')
        and target['item'] in xbmc.getInfoLabel('Container.FolderPath'),'normal-listening-page')
    count=int(xbmc.getInfoLabel('Container(50).NumItems'));found=False
    for index in range(min(count,1000)):
        focus(50,index)
        if target['kind']=='audiobook':
            match=xbmc.getInfoLabel('Container(50).ListItem.Property(AsterBooks.Resume)')=='true'
        else:
            match=xbmc.getInfoLabel('Container(50).ListItem.Property(AsterBooks.Episode)')==target['episode']
        if match:found=True;break
    require(found,'resume-or-episode-row-found')
    url=xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')
    require(url.startswith('http://127.0.0.1:') and '/audio/' in url,'private-selected-audio')
    return url
result=dict(passed=False,checks_enforced=True,normal_ui=True,checks=checks)
try:
    require(idle() and home.getProperty('AsterBooks.SyncService')=='ready','idle-service-ready')
    targets=json.loads(Path('/storage/.aster-checkpoints/aster-books-progress-20261025/trial1/targets-private.json').read_text())
    require(len(targets)==2 and {t['kind'] for t in targets}=={'audiobook','podcast'},'two-audited-fixtures')
    for target in targets:
        phase=target['kind']+'-enter'
        before=reader.progress(account,target['kind'],target['item'],target['episode'])
        require(before is not None and before.position>0 and not before.finished,'existing-position-required')
        url=enter(target)
        xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-books-sync-20261025/listening-page.png)')
        select();phase=target['kind']+'-resume'
        until(lambda:owned(url) and home.getProperty('AsterBooks.SyncState')=='ready'
            and before.position-2<=player.getTime()<=before.position+8,'server-position-resumed')
        start=player.getTime();until(lambda:owned(url) and player.getTime()>=start+4,'normal-clock-advances')
        if sleep_mode:
            until(lambda:bool(home.getProperty('AsterBooks.SleepToken')),'sleep-owned-token')
            focus(9106);select();until(lambda:xbmcgui.getCurrentWindowDialogId()==12000,'normal-sleep-selector')
            press('down');press('select')
            until(lambda:home.getProperty('AsterBooks.SleepStatus')=='Sleep in 15 min','normal-sleep-armed')
            require(owned(url),'sleep-arm-preserves-playback')
            xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-books-sync-20261025/sleep-controls.png)')
            focus(9106);select();until(lambda:xbmcgui.getCurrentWindowDialogId()==12000,'normal-sleep-off-selector')
            press('select');until(lambda:home.getProperty('AsterBooks.SleepStatus')=='Sleep timer off','normal-sleep-cancelled')
            require(owned(url),'sleep-cancel-preserves-playback')
            result.setdefault('sleep_controls',[]).append(dict(kind=target['kind'],normal_select_arm_cancel=True))
        if tempo_mode:
            probe=dict(kind=target['kind'],supported=False,restored=False)
            try:
                props=rpc('Player.GetProperties',dict(playerid=0,properties=['tempo']))
                require(abs(props['tempo']-1.0)<.01,'normal-tempo-required')
                rpc('Player.SetTempo',dict(playerid=0,tempo=1.25))
                until(lambda:abs(rpc('Player.GetProperties',dict(playerid=0,properties=['tempo']))['tempo']-1.25)<.01,'tempo-not-observed',4)
                clock_start=time.monotonic();media_start=player.getTime();xbmc.sleep(4000)
                probe.update(supported=True,wall_seconds=round(time.monotonic()-clock_start,2),
                    media_seconds=round(player.getTime()-media_start,2))
            except Exception:probe['code']='native-audio-tempo-unavailable'
            finally:
                if owned(url):
                    try:
                        rpc('Player.SetTempo',dict(playerid=0,tempo=1.0))
                        props=rpc('Player.GetProperties',dict(playerid=0,properties=['tempo']))
                        probe['restored']=abs(props['tempo']-1.0)<.01
                    except Exception:probe['restored']=False
            result.setdefault('tempo_probes',[]).append(probe)
        phase=target['kind']+'-pause'
        focus(9102);select();until(lambda:xbmc.getCondVisibility('Player.Paused'),'normal-pause')
        paused=player.getTime();until(lambda:home.getProperty('AsterBooks.SyncStatus')=='Saved to household position','pause-save-ack')
        saved=reader.progress(account,target['kind'],target['item'],target['episode'])
        require(saved is not None and abs(saved.position-paused)<=2 and saved.position>before.position+1,'pause-saved-correct-position')
        focus(9102);select();until(lambda:not xbmc.getCondVisibility('Player.Paused'),'normal-unpause')
        until(lambda:owned(url) and player.getTime()>=paused+3,'normal-after-pause-clock')
        phase=target['kind']+'-exit'
        if stop_mode:
            focus(9104);select();until(lambda:not rpc('Player.GetActivePlayers'),'normal-stop-button')
            focus(9000);select()
        else:press('back')
        until(lambda:not rpc('Player.GetActivePlayers') and xbmcgui.getCurrentWindowId()!=10502,'normal-back-stops')
        xbmc.sleep(1200)
        final=reader.progress(account,target['kind'],target['item'],target['episode'])
        require(final is not None and final.position>saved.position+1,'exit-position-saved')
        require(idle(),'normal-exit-empty-queues')
        checks.append(dict(kind=target['kind'],normal_page_entry=True,source_resume=True,pause_saved=True,
            exit_action='stop-button' if stop_mode else 'back',exit_saved_and_stopped=True))
        xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-return')
    result['passed']=True
except Exception as error:
    result.update(code=str(error) if isinstance(error,RuntimeError) else 'books-ui-test-failed',phase=phase)
    result['observer_reason']=home.getProperty('AsterBooks.SyncReason')
    if 'url' in locals() and owned(url):result['observed_duration']=player.getTotalTime()
    if 'before' in locals() and before is not None:result['expected_duration']=before.duration
finally:
    # Test failures may stop only the exact positively observed test stream.
    # Never inspect inactive native ControlList objects or clear any queue here.
    if not result['passed'] and 'url' in locals() and owned(url) and xbmcgui.getCurrentWindowId()==10502:
        try:
            if xbmcgui.getCurrentWindowDialogId()==12000:
                press('back');until(lambda:xbmcgui.getCurrentWindowDialogId()!=12000,'owned-test-dialog-close',4)
            focus(9104);select();until(lambda:not rpc('Player.GetActivePlayers'),'owned-test-stop',8)
            focus(9000);select();until(lambda:xbmcgui.getCurrentWindowId()!=10502,'owned-test-return',8)
            xbmc.sleep(800);result['owned_failure_cleanup']=True
        except Exception:result['owned_failure_cleanup']=False
    result.update(idle_empty=idle(),window=xbmcgui.getCurrentWindowId(),
        service_state=home.getProperty('AsterBooks.SyncState'),service_status=home.getProperty('AsterBooks.SyncStatus'))
    path=root/('native-ui-'+str(time.time_ns())+'.json')
    with path.open('x') as f:json.dump(result,f,indent=2)
    path.chmod(0o600);os.close(lock)
