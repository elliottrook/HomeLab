"""HP video scrub dialog: preview only until one explicit OK."""
import fcntl,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'resources/lib'))
from video_scrub import ScrubSession,ScrubUnavailable,read_state,clock_label
BACK={9,10,92,216,247,257,275}
DIRECTORY=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')

def rpc(method,params):
    if method not in {'Player.GetActivePlayers','Player.GetItem','Player.GetProperties','Player.Seek','Player.PlayPause'}:
        raise ScrubUnavailable('scrub-boundary')
    if method=='Player.PlayPause' and params!=dict(playerid=1,play=False):raise ScrubUnavailable('pause-preservation-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    if 'error' in reply:raise ScrubUnavailable('native-request-unavailable')
    return reply.get('result',{})

class ScrubDialog(xbmcgui.WindowXMLDialog):
    def onInit(self):
        self.ready=True;self.render();self.setFocusId(10)
        home=xbmcgui.Window(10000);home.setProperty('AsterVideo.ScrubOpen','true')
    def render(self):
        preview=self.session.preview
        self.getControl(20).setPercent(preview.percentage)
        self.getControl(21).setPosition(70+round(preview.percentage*17.8)-9,811)
        self.setProperty('Scrub.Time',clock_label(preview.target_ms)+' / '+clock_label(preview.state.duration_ms))
        self.setProperty('Scrub.Hint','Left / right · 5 seconds    OK · seek    Back · cancel')
        self.setProperty('Scrub.Paused','Paused' if preview.state.speed==0 else 'Playing · preview only')
        xbmcgui.Window(10000).setProperty('AsterVideo.ScrubTarget',str(preview.target_ms))
    def onAction(self,action):
        if not self.ready or self.done:return
        key=action.getId()
        if key in BACK:self.session.cancel();self.done=True;self.close()
        elif key in (1,2):self.session.adjust(-1 if key==1 else 1);self.render()
    def onClick(self,identity):
        if identity!=10 or not self.ready or self.done:return
        self.done=True
        try:self.session.apply()
        except ScrubUnavailable:
            if self.session.phase=='uncertain':
                path=DIRECTORY/'unresolved-seek.json'
                if not path.exists():
                    with path.open('x') as handle:json.dump(dict(kind=self.session.preview.state.kind,
                        identity=self.session.preview.state.identity,target_ms=self.session.preview.target_ms,time=int(time.time())),handle)
                    path.chmod(0o600)
            xbmcgui.Dialog().notification('Seek not confirmed','The video changed or seeking could not be verified. No retry was sent.')
        self.close()

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
        if (DIRECTORY/'unresolved-seek.json').exists():
            xbmcgui.Dialog().notification('Seek needs review','A previous seek result was uncertain. Nothing was retried.');return
        observer=PlaybackEpoch()
        try:session=ScrubSession(rpc,lambda:observer.value)
        except ScrubUnavailable:
            xbmcgui.Dialog().notification('Seeking unavailable','Use a seekable indexed film or episode. Nothing was changed.');return
        window=ScrubDialog('VideoScrub.xml',str(ROOT),'Default','1080i')
        window.session=session;window.ready=False;window.done=False
        try:window.doModal()
        finally:
            session.cancel();window.close()
            home=xbmcgui.Window(10000)
            for name in ('ScrubOpen','ScrubTarget'):home.clearProperty('AsterVideo.'+name)
            try:
                if read_state(rpc).key==session.preview.state.key and xbmcgui.getCurrentWindowId()==12005:
                    xbmc.executebuiltin('ActivateWindow(VideoOSD)')
            except ScrubUnavailable:pass
            del window
    finally:os.close(fd)

if __name__=='__main__':main()
