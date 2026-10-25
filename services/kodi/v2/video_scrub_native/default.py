"""HP native skin dialog controller; no Python-owned GUI window/callback."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from video_scrub import ScrubSession,ScrubUnavailable,read_state,clock_label
DIRECTORY=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')
NATIVE=Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1126_videoscrub.xml')
PREFIX='AsterVideo.'
def rpc(method,params):
    if method not in {'Player.GetActivePlayers','Player.GetItem','Player.GetProperties','Player.Seek','Player.PlayPause'}:raise ScrubUnavailable('scrub-boundary')
    if method=='Player.PlayPause' and params!=dict(playerid=1,play=False):raise ScrubUnavailable('pause-preservation-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    if 'error' in reply:raise ScrubUnavailable('native-request-unavailable')
    return reply.get('result',{})
class PlaybackEpoch(xbmc.Player):
    def __init__(self):super().__init__();self.value=0
    def onPlayBackStarted(self):self.value+=1
    def onPlayBackStopped(self):self.value+=1
    def onPlayBackEnded(self):self.value+=1
def main():
    if os.uname().nodename!='AsterTV':return
    DIRECTORY.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(DIRECTORY/'entry.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        if (DIRECTORY/'unresolved-seek.json').exists():raise ScrubUnavailable('seek-needs-review')
        manifest=json.loads((ROOT/'manifest.json').read_text())
        if manifest.get('kind')!='hp-video-scrub-native':raise ScrubUnavailable('native-stage-required')
        row=next(r for r in manifest['files'] if r['path']=='overlay/custom_1126_videoscrub.xml')
        if hashlib.sha256(NATIVE.read_bytes()).hexdigest()!=row['sha256']:raise ScrubUnavailable('native-dialog-not-verified')
        observer=PlaybackEpoch();session=ScrubSession(rpc,lambda:observer.value)
        home=xbmcgui.Window(10000);monitor=xbmc.Monitor()
        def render():
            preview=session.preview
            home.setProperty(PREFIX+'ScrubTime',clock_label(preview.target_ms)+' / '+clock_label(preview.state.duration_ms))
            home.setProperty(PREFIX+'ScrubTarget',str(preview.target_ms))
            home.setProperty(PREFIX+'ScrubHint','Left / right · 5 seconds    OK · seek    Back · cancel')
            home.setProperty(PREFIX+'ScrubPaused','Paused' if preview.state.speed==0 else 'Playing · preview only')
            if xbmc.getCondVisibility('Window.IsVisible(11126)'):
                native=xbmcgui.Window(11126)
                native.getControl(20).setPercent(preview.percentage)
                native.getControl(21).setPosition(70+round(preview.percentage*17.8)-9,813)
        home.clearProperty(PREFIX+'ScrubCommand');render()
        xbmc.executebuiltin('ActivateWindow(1126)')
        try:
            end=time.monotonic()+10
            while not xbmc.getCondVisibility('Window.IsVisible(11126)'):
                if time.monotonic()>end or monitor.waitForAbort(.05):raise ScrubUnavailable('native-dialog-not-ready')
            render()
            while xbmc.getCondVisibility('Window.IsVisible(11126)') and not monitor.abortRequested():
                if observer.value!=session.initial_epoch:break
                command=home.getProperty(PREFIX+'ScrubCommand')
                if command:
                    home.clearProperty(PREFIX+'ScrubCommand')
                    if command=='apply':session.apply();break
                    if command in ('left','right'):session.adjust(-1 if command=='left' else 1);render()
                if monitor.waitForAbort(.02):break
        finally:
            session.cancel();xbmc.executebuiltin('Dialog.Close(11126)')
            for key in ('ScrubOpen','ScrubCommand','ScrubTarget'):home.clearProperty(PREFIX+key)
            try:
                if read_state(rpc).key==session.preview.state.key and xbmcgui.getCurrentWindowId()==12005:
                    xbmc.executebuiltin('ActivateWindow(VideoOSD)')
            except ScrubUnavailable:pass
    except (OSError,ValueError,KeyError,StopIteration):
        if 'session' in locals() and session.phase=='uncertain':
            path=DIRECTORY/'unresolved-seek.json'
            if not path.exists():
                with path.open('x') as handle:json.dump(dict(identity=session.preview.state.identity,target_ms=session.preview.target_ms,time=int(time.time())),handle)
                path.chmod(0o600)
        xbmcgui.Dialog().notification('Seek unavailable','The video or native dialog could not be verified. Nothing was retried.')
    finally:os.close(fd)
if __name__=='__main__':main()
