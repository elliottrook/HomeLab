"""HP-only household progress observer, retaining the established streaming bridge."""
import fcntl,json,os,secrets,sys,time
from pathlib import Path
import xbmc,xbmcgui,xbmcvfs
sys.path.insert(0,str(Path(__file__).resolve().parent/'resources/lib'))
from resources.lib.bridge import Bridge,BridgeError,CONTROL_SOCKET,load_config,secure_kodi_log
from books_sync import ACCOUNT,Observer,QueueCleaner
from books_sync_bridge import ProgressBridge
try:from books_sleep import SleepTimer,Listening,countdown_label,owned_audio_player
except ImportError:SleepTimer=None  # Historical nine-file overlays have no sleep module.
PROFILE=Path(xbmcvfs.translatePath('special://profile/addon_data/plugin.audio.asterbooks'))

def main():
    PROFILE.mkdir(mode=0o700,parents=True,exist_ok=True);os.chmod(PROFILE,0o700)
    try:origin,key=load_config(PROFILE/'client.json')
    except (OSError,ValueError,BridgeError):return
    flag=PROFILE/'progress-enabled.json'
    enabled=False
    if os.uname().nodename=='AsterTV' and flag.is_file() and not flag.is_symlink():
        try:enabled=json.loads(flag.read_text())==dict(enabled=True,host='AsterTV',account_sha256=ACCOUNT,kind='aster-books-sync-pilot.v1')
        except (OSError,ValueError):pass
    fd=None;bridge=None;observer=None;sleep_timer=None;home=xbmcgui.Window(10000)
    try:
        if enabled:
            fd=os.open(PROFILE/'progress-sync.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            bridge=ProgressBridge(origin,key,PROFILE/'progress-journal')
            bridge.writer.account()
        else:bridge=Bridge(origin,key)
        del key
        secure_kodi_log(xbmcvfs.translatePath('special://logpath/kodi.log'))
        bridge.start(PROFILE/CONTROL_SOCKET)
        player=xbmc.Player();monitor=xbmc.Monitor()
        def status(state,text):
            home.setProperty('AsterBooks.SyncState',state);home.setProperty('AsterBooks.SyncStatus',text)
            home.setProperty('AsterBooks.SyncReason',observer.error or '' if observer else '')
        def seek(url,position):
            if not player.isPlayingAudio() or player.getPlayingFile()!=url:raise RuntimeError('seek-ownership-changed')
            player.seekTime(position)
        if enabled:
            observer=Observer(bridge.registry,bridge.writer,seek,status)
            status('idle','Shared household progress ready')
            home.setProperty('AsterBooks.SyncService','ready')
            def queue_rpc(method,params):
                if method not in ('Player.GetActivePlayers','Playlist.GetItems','Playlist.Clear'):raise RuntimeError('queue-rpc-boundary')
                if method=='Playlist.Clear' and params!={'playlistid':0}:raise RuntimeError('audio-queue-only')
                response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
                if 'error' in response:raise RuntimeError('queue-request-failed')
                return response['result']
            cleaner=QueueCleaner(bridge.registry,queue_rpc,PROFILE/'progress-journal')
            def listening():
                try:
                    if player.isPlayingAudio() and observer.binding is not None and player.getPlayingFile()==observer.url:
                        return Listening(observer.binding.scope,observer.url)
                except Exception:pass
                return None
            def sleep_save(url):
                context=listening()
                if context is None or context.url!=url:raise RuntimeError('sleep-save-ownership-changed')
                observer.save()
                return observer.phase=='ready' and observer.last_saved is not None and observer.position is not None and abs(observer.last_saved-observer.position)<.5
            def sleep_stop(url):
                context=listening()
                if context is None or context.url!=url:raise RuntimeError('sleep-stop-ownership-changed')
                if not owned_audio_player(queue_rpc('Player.GetActivePlayers',{})):raise RuntimeError('sleep-only-owned-audio')
                reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Player.Stop',params=dict(playerid=0)))))
                if reply.get('result')!='OK':raise RuntimeError('sleep-stop-unacknowledged')
                for _ in range(20):
                    if not player.isPlaying():return True
                    if monitor.waitForAbort(.1):break
                return False
            def sleep_report(state,text):home.setProperty('AsterBooks.SleepStatus',text)
            if SleepTimer is not None:sleep_timer=SleepTimer(listening,sleep_save,sleep_stop,sleep_report)
            sleep_scope=None;sleep_token='';last_request=''
            home.clearProperty('AsterBooks.SleepRequest');home.clearProperty('AsterBooks.SleepStatus')
        pending_queue=None
        while not monitor.abortRequested():
            observed_known=True
            if observer:home.setProperty('AsterBooks.SyncHeartbeat',str(time.time()))
            if observer:
                try:
                    previous=observer.binding
                    if player.isPlaying():
                        if player.isPlayingAudio():
                            url=player.getPlayingFile();duration=player.getTotalTime();position=player.getTime()
                            observed_known=duration>0
                            # Kodi can announce playing before AV metadata is ready.
                            observer.tick(url,position,duration,xbmc.getCondVisibility('Player.Paused'),known=duration>0)
                        else:observer.tick(None)
                    else:observer.tick(None)
                    if previous is not None and observer.binding is None and not player.isPlaying():pending_queue=previous.scope
                    if player.isPlaying():pending_queue=None
                    if pending_queue is not None and xbmcgui.getCurrentWindowId()!=10502 and not player.isPlaying():
                        candidate=pending_queue;pending_queue=None
                        try:cleaner.clean(candidate)
                        except Exception:status('queue-uncertain','Audio stopped · queue cleanup needs review')
                except Exception:pass  # Never log a private media URL/exception.
            if sleep_timer:
                try:
                    context=listening();scope=context.scope if context else None
                    if observed_known and scope!=sleep_scope:
                        sleep_scope=scope;sleep_token=secrets.token_hex(16) if scope else ''
                    home.setProperty('AsterBooks.SleepToken',sleep_token)
                    command=home.getProperty('AsterBooks.SleepRequest')
                    if command:
                        home.clearProperty('AsterBooks.SleepRequest')
                        request=json.loads(command) if len(command)<=512 else {}
                        if (set(request)=={'token','request','minutes'} and request['token']==sleep_token and sleep_token
                            and isinstance(request['request'],str) and len(request['request'])==32 and request['request']!=last_request):
                            last_request=request['request']
                            if request['minutes']==0 and type(request['minutes']) is int:sleep_timer.cancel()
                            else:sleep_timer.arm(request['minutes'])
                    sleep_timer.tick(known=observed_known)
                    remaining=sleep_timer.remaining()
                    if remaining is not None:home.setProperty('AsterBooks.SleepStatus',countdown_label(remaining))
                except Exception:home.setProperty('AsterBooks.SleepStatus','Sleep timer unavailable · reopen controls')
            if monitor.waitForAbort(.2):break
    except Exception:
        home.setProperty('AsterBooks.SyncState','unavailable')
        home.setProperty('AsterBooks.SyncStatus','Shared progress unavailable · check the private Books connection')
    finally:
        try:
            if observer:observer.finish()
        finally:
            if bridge:bridge.stop()
        if fd is not None:os.close(fd)
        home.clearProperty('AsterBooks.SyncState')
        home.clearProperty('AsterBooks.SyncService');home.clearProperty('AsterBooks.SyncHeartbeat')
        for name in ('SleepToken','SleepRequest','SleepStatus'):home.clearProperty('AsterBooks.'+name)
if __name__=='__main__':main()
