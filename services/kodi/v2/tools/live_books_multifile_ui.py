"""HP owned UI transition/resume acceptance; no direct source progress writes."""
import fcntl,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
sys.path[:0]=['/storage/.kodi/addons/plugin.audio.asterbooks','/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib']
from resources.lib.bridge import Bridge,load_config,chapter_starts
from books_sync_bridge import book_files
from books_progress_reader import Reader
from books_sync import ACCOUNT
origin,key=load_config(Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/client.json'))
bridge=Bridge(origin,key);del key
reader=Reader(bridge.upstream);account=reader.account()
require(account.limited and account.fingerprint==ACCOUNT,'approved-household-account')
root=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')
home=xbmcgui.Window(10000);player=xbmc.Player();owned_urls=set();phase='preflight'
result=dict(passed=False,checks_enforced=True,normal_ui=True)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Player.Seek'),'bounded-native-method')
    if method=='Player.Seek':require(owned() and home.getProperty('AsterBooks.SyncState')=='ready','seek-owned-ready-stream')
    row=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in row,'native-request');return row['result']
def owned():
    try:return player.isPlayingAudio() and player.getPlayingFile() in owned_urls
    except Exception:return False
def until(check,code,timeout=40):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(100)
    raise RuntimeError(code)
def focus(identity,index=None):
    for _ in range(3):
        xbmc.executebuiltin('SetFocus('+str(identity)+')' if index is None else 'Control.SetFocus('+str(identity)+','+str(index)+',absolute)')
        xbmc.sleep(250)
        if xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'):return
    raise RuntimeError('focus-'+str(identity))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def enter(item):
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-entry')
    xbmc.executebuiltin('ActivateWindow(1110)')
    until(lambda:xbmcgui.getCurrentWindowId()==11110 and xbmc.getInfoLabel('Container(502).NumItems') not in ('','0'),'books-home')
    xbmc.sleep(600);focus(111);select()
    until(lambda:xbmcgui.getCurrentWindowId()==11119 and xbmc.getInfoLabel('Container(500).NumItems') not in ('','0'),'audiobook-page')
    found=False
    for index in range(min(int(xbmc.getInfoLabel('Container(500).NumItems')),1000)):
        focus(500,index)
        if xbmc.getInfoLabel('Container(500).ListItem.Property(AsterBooks.Id)')==item:found=True;break
    require(found,'exact-book-found');select()
    until(lambda:xbmcgui.getCurrentWindowId()==10502 and item in xbmc.getInfoLabel('Container.FolderPath')
        and xbmc.getInfoLabel('Container(50).NumItems') not in ('','0'),'listening-page')
def row(number):
    for index in range(min(int(xbmc.getInfoLabel('Container(50).NumItems')),1001)):
        focus(50,index)
        if xbmc.getInfoLabel('Container(50).ListItem.Property(AsterBooks.Number)')==str(number):
            url=xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')
            require(url.startswith('http://127.0.0.1:') and '/audio/' in url,'private-audio-row')
            owned_urls.add(url);return url
    raise RuntimeError('exact-row-not-found')
def exit_home():
    rpc('Input.ExecuteAction',dict(action='back'))
    until(lambda:xbmcgui.getCurrentWindowId()!=10502 and not rpc('Player.GetActivePlayers'),'back-stops')
    until(idle,'owned-queue-empty');xbmc.executebuiltin('ActivateWindow(Home)')
    until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-return')
try:
    require(idle() and home.getProperty('AsterBooks.SyncService')=='ready','idle-service-ready')
    candidates=json.loads(sorted(root.glob('multifile-private-*.json'))[-1].read_text());selected=None
    for candidate in candidates:
        item=candidate['item'];media=bridge.metadata(item)['media'];inodes,spans=book_files(media)
        before=reader.progress(account,'audiobook',item)
        if before is not None:continue  # Never rewind an existing household position for this test.
        chapters=chapter_starts(media,media['audioFiles'])
        rows=[(r[4],r[1]) for r in chapters] if chapters else [(i+1,i) for i in range(len(spans))]
        pairs=[(a,b) for a,b in zip(rows,rows[1:]) if a[1]==0 and b[1]==1]
        if pairs:selected=(item,spans,pairs[0]);break
    require(selected is not None,'untouched-mapped-transition-fixture-required')
    item,spans,(first,second)=selected;phase='first-file'
    enter(item);next_url=row(second[0]);first_url=row(first[0]);select()
    until(lambda:owned() and player.getPlayingFile()==first_url and home.getProperty('AsterBooks.SyncState')=='ready','first-file-owned-ready')
    require(abs(player.getTotalTime()-spans[0].duration)<=2,'first-file-duration')
    phase='natural-transition'
    rpc('Player.Seek',dict(playerid=0,value=dict(percentage=100*(spans[0].duration-4)/spans[0].duration)))
    until(lambda:owned() and player.getPlayingFile()==next_url and home.getProperty('AsterBooks.SyncState')=='ready','automatic-next-file',25)
    start=player.getTime();until(lambda:owned() and player.getTime()>=start+4,'second-file-clock')
    focus(9102);select();until(lambda:xbmc.getCondVisibility('Player.Paused'),'pause-second-file')
    paused=player.getTime();until(lambda:home.getProperty('AsterBooks.SyncStatus')=='Saved to household position','whole-book-save')
    saved=reader.progress(account,'audiobook',item)
    require(saved is not None and abs(saved.position-(spans[1].start+paused))<=2 and not saved.finished,'whole-book-time-verified')
    result.update(natural_file_transition=True,global_position_verified=True,completion_unchanged=True)
    exit_home();phase='resume-second-file'
    enter(item);url=row('R');select()
    until(lambda:owned() and player.getPlayingFile()==url and home.getProperty('AsterBooks.SyncState')=='ready'
        and saved.position-spans[1].start-2<=player.getTime()<=saved.position-spans[1].start+8,'resume-correct-second-file')
    require(abs(player.getTotalTime()-spans[1].duration)<=2,'second-file-resume-duration')
    exit_home();result.update(passed=True,source_resume_correct_file=True)
except Exception as error:
    result.update(code=str(error) if isinstance(error,RuntimeError) else 'multifile-test-unavailable',phase=phase,
        observer_reason=home.getProperty('AsterBooks.SyncReason'))
finally:
    if not result['passed'] and owned() and xbmcgui.getCurrentWindowId()==10502:
        try:
            focus(9104);select();until(lambda:not rpc('Player.GetActivePlayers'),'owned-stop',8)
            focus(9000);select();until(lambda:xbmcgui.getCurrentWindowId()!=10502,'owned-return',8)
            until(idle,'owned-empty',8);result['owned_failure_cleanup']=True
        except Exception:result['owned_failure_cleanup']=False
    result.update(idle_empty=idle(),window=xbmcgui.getCurrentWindowId())
    path=root/('multifile-ui-'+str(time.time_ns())+'.json')
    with path.open('x') as stream:json.dump(result,stream,indent=2)
    path.chmod(0o600);os.close(lock)
