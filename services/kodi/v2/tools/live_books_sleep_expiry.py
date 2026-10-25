"""HP full 15-minute sleep expiry through normal UI; existing lab book only.

No direct progress writes or shortened production deadlines. Never stops an
unknown stream, and records failure rather than replaying uncertain writes.
"""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
home=xbmcgui.Window(10000);player=xbmc.Player();root=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')
result=dict(passed=False,full_preset_minutes=15);phase='preflight';url=None
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems'),'read-only-rpc')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'read-failed');return reply['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,code,timeout=40):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if check():return
        if xbmc.Monitor().waitForAbort(.1):raise RuntimeError('aborted')
    raise RuntimeError(code)
def focus(identity,index=None):
    xbmc.executebuiltin('SetFocus('+str(identity)+')' if index is None else 'Control.SetFocus('+str(identity)+','+str(index)+',absolute)')
    xbmc.sleep(350);require(xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'focus-failed')
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-required')
    target=next(t for t in json.loads(Path('/storage/.aster-checkpoints/aster-books-progress-20261025/trial1/targets-private.json').read_text()) if t['kind']=='audiobook')
    xbmc.executebuiltin('ActivateWindow(1110)')
    until(lambda:xbmcgui.getCurrentWindowId()==11110 and xbmc.getInfoLabel('Container(502).NumItems') not in ('','0'),'books-home')
    xbmc.sleep(700);focus(111);select()
    until(lambda:xbmcgui.getCurrentWindowId()==11119 and xbmc.getInfoLabel('Container(500).NumItems') not in ('','0'),'audiobook-page')
    found=False
    for i in range(min(1000,int(xbmc.getInfoLabel('Container(500).NumItems')))):
        focus(500,i)
        if xbmc.getInfoLabel('Container(500).ListItem.Property(AsterBooks.Id)')==target['item']:found=True;break
    require(found,'existing-test-book-required');select()
    until(lambda:xbmcgui.getCurrentWindowId()==10502 and xbmc.getInfoLabel('Container(50).NumItems') not in ('','0'),'chapter-page')
    focus(50,0);require(xbmc.getInfoLabel('Container(50).ListItem.Property(AsterBooks.Resume)')=='true','existing-resume-row-required')
    result['resume_label']=xbmc.getInfoLabel('Container(50).ListItem.Label')
    result['resume_time']=xbmc.getInfoLabel('Container(50).ListItem.Property(AsterBooks.Length)')
    url=xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath');select()
    until(lambda:player.isPlayingAudio() and home.getProperty('AsterBooks.SyncState')=='ready' and bool(home.getProperty('AsterBooks.SleepToken')),'owned-resume-ready')
    require(player.getPlayingFile()==url and player.getTotalTime()-player.getTime()>925,'long-enough-fixture')
    result['players']=rpc('Player.GetActivePlayers');phase='arm'
    focus(9106);select();until(lambda:xbmcgui.getCurrentWindowDialogId()==12000,'sleep-menu')
    xbmc.executebuiltin('Action(Down)');xbmc.sleep(200);xbmc.executebuiltin('Action(Select)')
    until(lambda:home.getProperty('AsterBooks.SleepStatus')=='Sleep in 15 min','normal-preset-armed')
    started=time.monotonic();phase='countdown';seen_seconds=False
    while time.monotonic()-started<930:
        status=home.getProperty('AsterBooks.SleepStatus')
        if status.startswith('Sleep in ') and ':' in status:seen_seconds=True
        if not player.isPlaying():break
        require(player.getPlayingFile()==url,'playback-changed-no-test-stop')
        require(not status.startswith(('Sleep stop unverified','Sleep cancelled','Sleep timer unavailable')),'sleep-error-'+status)
        if xbmc.Monitor().waitForAbort(.5):raise RuntimeError('aborted')
    result.update(elapsed_seconds=round(time.monotonic()-started,2),second_countdown_seen=seen_seconds,
                  final_status=home.getProperty('AsterBooks.SleepStatus'))
    require(not player.isPlaying() and seen_seconds and result['final_status']=='Sleep timer ended','expiry-not-verified')
    require(895<=result['elapsed_seconds']<=915,'full-preset-duration')
    xbmc.executebuiltin('Action(Back)');until(idle,'owned-queue-cleaned')
    xbmc.executebuiltin('ActivateWindow(Home)');result['passed']=True
except Exception as error:
    result.update(phase=phase,code=str(error) if isinstance(error,RuntimeError) else type(error).__name__)
finally:
    path=root/('sleep-expiry-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
