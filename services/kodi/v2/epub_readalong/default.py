"""HP-only narrated synthetic EPUB proof; no network or shared progress."""
import fcntl,hashlib,json,os,re,stat,sys,time,uuid,wave
from pathlib import Path
from queue import SimpleQueue,Empty
import xbmc,xbmcgui

ROOT=Path(__file__).resolve().parent
BACK={9,10,92,216,247,257,275}
STATE=Path('/storage/.aster-state/aster-epub-readalong/word-groups-v1')
CACHE=Path('/storage/.aster-cache/aster-epub-readalong')
MEMBERS={'default.py','epub_chapter.py','epub_fixture.py','epub_pages.py','chapter_narration.py','word_alignment.py','word_group_narration.py',
 'epub_readalong_state.py','digest_kodi_port.py','digest_playback_state.py','digest_timeline.py',
 'sample.epub','sample.json','chapter.wav','resources/skins/Default/1080i/EpubReadAlong.xml'} | {
 'resources/skins/Default/media/'+name+'.png' for name in ('play','pause','stop','previous')}

def require(ok,code):
    if not ok:raise ValueError(code)
def verify(pin):
    require(re.fullmatch('[a-f0-9]{64}',pin),'epub-readalong-pin');raw=(ROOT/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==pin,'epub-readalong-manifest');m=json.loads(raw)
    require(m['kind']=='hp-epub-readalong.v2' and m['synthetic'] is True and m['network'] is False
            and m['shared_progress'] is False and m['normal_entry'] is False and m['word_timestamps'] is True
            and m['connected_phrase_cues'] is True,
            'epub-readalong-boundary')
    require(set(m['files'])==MEMBERS,'epub-readalong-members')
    require(m['files']['chapter.wav']==m['audio_sha256'],'epub-readalong-audio-manifest')
    for name,wanted in m['files'].items():
        path=ROOT/name;require(path.is_file() and not path.is_symlink() and path.stat().st_size<=32*1024*1024,'epub-readalong-file')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==wanted,'epub-readalong-drift')
    with wave.open(str(ROOT/'chapter.wav'),'rb') as item:
        require((item.getnchannels(),item.getframerate(),item.getsampwidth(),item.getnframes())==
                (1,24000,2,m['audio_frames']),'epub-readalong-audio-shape')
    return m

def reading_activity():
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.ExecuteAction","params":{"action":"noop"}}'))
    require('error' not in reply,'epub-readalong-activity')

class Reading(xbmcgui.WindowXML):
    def onInit(self):
        self.identity=xbmcgui.getCurrentWindowId();self.setFocusId(500)
        xbmcgui.Window(10000).setProperty('AsterEpubReadAlong.Window',str(self.identity))
        self.publish()
    def onClick(self,identity):self.commands.put(identity)
    def onAction(self,action):
        identity=action.getId()
        if identity in BACK:self.commands.put('close')
        elif identity in (1,2) and self.getFocusId()==500 and (not self.port or not self.port.owned()):self.commands.put('previous-page' if identity==1 else 'next-page')
    def save_point(self,sample,complete=False):
        value=dict(schema=1,book=self.book.book_sha256,chapter=self.book.chapter_sha256,
                   audio=self.manifest['audio_sha256'],sample=max(0,min(self.plan.total_samples,int(sample))),complete=bool(complete))
        self.state_api.save(STATE,value,self.book.book_sha256,self.book.chapter_sha256,
                            self.manifest['audio_sha256'],self.plan.total_samples);self.saved=value
    def publish(self,active=None,elapsed=None):
        if active is None and not self.saved['complete']:
            active=self.plan.active(self.saved['sample'],self.manifest['audio_sha256'])
        if active is not None:self.reader.go(active.text_start)
        span=(active.text_start,active.text_end) if active is not None else None
        body=self.render(self.book.text,self.reader.current,span)
        for identity in (501,502,503):self.getControl(identity).setText(body)
        for size in (24,30,40):self.setProperty('EpubRead.Size'+str(size),'true' if self.reader.size==size else 'false')
        self.setProperty('EpubRead.State',self.status);self.setProperty('EpubRead.Page',str(self.reader.page+1))
        seconds=(self.saved['sample']/24000 if elapsed is None else elapsed)
        total=self.plan.total_samples/24000
        self.setProperty('EpubRead.Active',str(self.plan.units.index(active) if active is not None else -1))
        self.setProperty('EpubRead.Sample',str(round(max(0,seconds)*24000)))
        self.setProperty('EpubRead.Status',self.status+' · '+str(self.reader.page+1)+' / '+str(len(self.reader.pages))+
                         ' · '+time.strftime('%M:%S',time.gmtime(max(0,seconds)))+' / '+
                         time.strftime('%M:%S',time.gmtime(total)))
        self.getControl(205).setLabel('Text '+str(self.reader.size))
    def stop_owned(self,save=True):
        if self.port and self.port.owned():
            observation=self.port.sample()
            if save:self.save_point(round(max(0,observation.elapsed)*24000))
            self.port.stop();require(self.port.idle(),'epub-readalong-stop-unsettled')
        elif not self.idle():return False
        return True
    def release_session(self):
        require(self.idle(),'epub-readalong-cache-player-active')
        if self.session and self.session.exists():
            meta=self.session.lstat();require(stat.S_ISREG(meta.st_mode) and not self.session.is_symlink()
                and hashlib.sha256(self.session.read_bytes()).hexdigest()==self.manifest['audio_sha256'],
                'epub-readalong-cache-ownership')
            self.session.unlink()
        self.session=None;self.port=None
    def begin(self):
        require(self.idle(),'epub-readalong-start-not-idle')
        parent=CACHE.parent;meta=parent.lstat();require(stat.S_ISDIR(meta.st_mode) and not parent.is_symlink(),'epub-readalong-cache-parent')
        CACHE.mkdir(mode=0o700,exist_ok=True);CACHE.chmod(0o700)
        self.session=CACHE/('session-'+uuid.uuid4().hex+'.wav')
        with self.session.open('xb') as output:output.write((ROOT/'chapter.wav').read_bytes())
        self.session.chmod(0o600);self.port=self.KodiPort(self.session,self.manifest['audio_sha256'],'synthetic-epub-readalong')
        self.port.open();self.pending_seek=0 if self.saved['complete'] else self.saved['sample']/24000
        self.deadline=time.monotonic()+8;self.status='Starting'
    def observe(self,observation):
        require(observation.session==self.port.session and observation.media==self.port.media,'epub-readalong-ownership')
        if observation.ended:
            require(self.port.player.natural,'epub-readalong-end-not-natural')
            settled=time.monotonic()+3
            while not self.idle() and time.monotonic()<settled:xbmc.sleep(50)
            require(self.port.idle(),'epub-readalong-end-unsettled')
            self.save_point(self.plan.total_samples,True);self.status='Complete'
            self.publish(None,self.plan.total_samples/24000);return
        active=self.plan.active(round(max(0,observation.elapsed)*24000),self.port.media)
        self.status='Paused' if observation.paused else 'Reading';self.publish(active,observation.elapsed)
    def tick(self):
        for _ in range(12):
            try:command=self.commands.get_nowait()
            except Empty:break
            if command=='close':
                if self.stop_owned():self.finished=True
                return
            if command==201:
                if self.port is None:self.begin()
                elif self.port.owned():
                    paused=self.status=='Paused';self.port.set_paused(not paused);self.status='Reading' if paused else 'Paused'
                elif self.idle():self.release_session();self.begin()
            elif command==202:
                if self.stop_owned():self.status='Stopped';self.publish()
            elif command==203 and self.port and self.port.owned():self.port.seek(0);self.save_point(0);self.status='Reading'
            elif command==204 and (self.port is None or not self.port.owned()) and self.idle():
                self.state_api.clear(STATE,self.book.book_sha256,self.book.chapter_sha256,self.manifest['audio_sha256'],self.plan.total_samples)
                self.saved=self.state_api.load(STATE,self.book.book_sha256,self.book.chapter_sha256,self.manifest['audio_sha256'],self.plan.total_samples)
                self.status='Progress cleared';self.reader.go(0);self.publish(None,0)
            elif command==205:self.reader.resize();self.publish()
            elif command in ('previous-page','next-page'):
                self.reader.move(-1 if command=='previous-page' else 1);self.publish(None)
        if not self.port:return
        if self.port.owned():
            if self.pending_seek is not None:
                target=self.pending_seek;self.pending_seek=None
                if target>0:self.port.seek(target)
            self.observe(self.port.sample())
        elif self.status=='Starting' and time.monotonic()<self.deadline:return
        elif self.port.player.starts==1 and not self.port.stopping:
            self.observe(self.port.lost_or_ended())
        elif self.idle():self.status='Stopped';self.publish()
        else:raise ValueError('epub-readalong-foreign-player')

def main():
    handle=None;window=None;previous=None
    try:
        require(os.uname().nodename=='AsterTV' and len(sys.argv)==2,'epub-readalong-hp-only');manifest=verify(sys.argv[1])
        handle=os.open(str(ROOT/'entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sys.path.insert(0,str(ROOT))
        from epub_chapter import chapter
        from epub_pages import Reader,render,FONT_SHA256
        import epub_readalong_state as state_api
        from word_group_narration import build as timeline
        from digest_kodi_port import KodiPort,idle
        require(hashlib.sha256(Path('/usr/share/kodi/media/Fonts/arial.ttf').read_bytes()).hexdigest()==FONT_SHA256,'epub-readalong-font-drift')
        require(idle() and xbmcgui.getCurrentWindowId()==10000,'epub-readalong-idle-home');home=xbmcgui.Window(10000)
        require(not home.getProperty('AsterEpubReadAlong.Window'),'epub-readalong-already-open');previous=home.getFocusId()
        book=chapter((ROOT/'sample.epub').read_bytes());config=json.loads((ROOT/'sample.json').read_text())
        plan=timeline(book,config,manifest['audio_sha256'])
        saved=state_api.load(STATE,book.book_sha256,book.chapter_sha256,manifest['audio_sha256'],plan.total_samples)
        window=Reading('EpubReadAlong.xml',str(ROOT),'Default','1080i');window.identity=None;window.commands=SimpleQueue();window.finished=False
        window.manifest=manifest;window.book=book;window.plan=plan;window.reader=Reader(book);window.reader.size=30
        window.saved=saved;window.state_api=state_api;window.render=render;window.KodiPort=KodiPort;window.idle=idle
        window.port=None;window.session=None;window.pending_seek=None;window.status='Complete' if saved['complete'] else ('Resume ready' if saved['sample'] else 'Ready')
        window.show();monitor=xbmc.Monitor();ready=time.monotonic()+5;activity_deadline=time.monotonic()+60
        while not monitor.waitForAbort(.05) and not window.finished:
            if window.identity is None:
                require(time.monotonic()<ready,'epub-readalong-ready-timeout');continue
            if xbmcgui.getCurrentWindowId()!=window.identity:
                if window.stop_owned():break
                continue
            window.tick()
            if time.monotonic()>=activity_deadline:
                reading_activity();activity_deadline=time.monotonic()+60
    except Exception as error:
        code=str(error);safe=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
        xbmc.log('Aster EPUB read-along: '+safe,xbmc.LOGERROR)
        xbmcgui.Dialog().notification('Aster Books','Read-along preview unavailable. Nothing else was stopped.')
    finally:
        if window:
            while not window.stop_owned():xbmc.sleep(100)
            window.close();xbmc.sleep(200)
            window.release_session()
        if handle is not None:os.close(handle);handle=None
        xbmcgui.Window(10000).clearProperty('AsterEpubReadAlong.Window')
        if previous and xbmcgui.getCurrentWindowId()==10000 and (not window or window.idle()):xbmc.executebuiltin('Control.SetFocus('+str(previous)+')')

if __name__=='__main__':main()
