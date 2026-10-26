"""Private synthetic read-along only. No service, book or progress access."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
from queue import SimpleQueue, Empty
import re
import sys
import time
import uuid
import wave
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
BACK={9,10,92,216,247,257,275}
MEMBERS={'default.py','digest_kodi_port.py','digest_playback_state.py','digest_timeline.py','narration_frames.py','narration_timeline.py',
         'sample.json','resources/skins/Default/1080i/ReadAlong.xml'} | {'resources/skins/Default/media/'+n+'.png' for n in ('play','pause','stop','previous')}

def verify(pin):
    if not re.fullmatch('[a-f0-9]{64}',pin):raise ValueError('readalong-pin')
    raw=(ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('readalong-manifest')
    m=json.loads(raw)
    if m['kind']!='hp-readalong.v1' or m['synthetic'] is not True or any(m[k] is not False for k in ('network','progress','normal_entry')):
        raise ValueError('readalong-boundary')
    if set(m['files'])!=MEMBERS:raise ValueError('readalong-members')
    for name,wanted in dict(m['files'],**{'sample.wav':m['audio_sha256']}).items():
        p=ROOT/name
        if any(v.is_symlink() for v in (p,*p.parents)) or not p.is_file() or p.stat().st_size>2097152:raise ValueError('readalong-file')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=wanted:raise ValueError('readalong-drift')
    if (ROOT/'sample.wav').stat().st_size!=440204:raise ValueError('readalong-size')
    with wave.open(str(ROOT/'sample.wav'),'rb') as w:
        if (w.getnchannels(),w.getframerate(),w.getsampwidth(),w.getnframes())!=(1,24000,2,220080):raise ValueError('readalong-format')
    return m

class Reading(xbmcgui.WindowXML):
    def onInit(self):
        self.identity=xbmcgui.getCurrentWindowId();self.setFocusId(201)
        xbmcgui.Window(10000).setProperty('AsterReadAlong.Window',str(self.identity))
        self.setProperty('ReadAlong.Ready','true');self.status='Ready';self.publish()
    def onClick(self,identity):self.commands.put(identity)
    def onAction(self,action):
        if action.getId() in BACK:self.commands.put('close')
    def publish(self,active=-1,elapsed=0):
        self.setProperty('ReadAlong.Active',str(active));self.setProperty('ReadAlong.Elapsed',str(elapsed))
        self.setProperty('ReadAlong.State',self.status)
        self.setProperty('ReadAlong.Status',self.status+' · '+format(elapsed,'.2f')+' / 9.17 seconds')
    def stop_owned(self):
        if self.port and self.port.owned():
            self.port.stop()
            if not self.port.idle():raise ValueError('readalong-stop-unsettled')
        elif not idle():return False
        return True
    def observe(self,observation):
        if observation.session!=self.port.session or observation.media!=self.port.media:raise ValueError('readalong-ownership')
        if observation.ended:
            # PAPlayer can emit Ended before its transient playlist entry is
            # cleared. Await read-only idle settlement; do not clear a queue.
            if not self.port.player.natural or not self.port.idle():raise ValueError('readalong-end-unsettled')
            self.status='Ended';self.publish(-1,9.17);return
        self.status='Paused' if observation.paused else 'Playing'
        elapsed=observation.elapsed
        span=self.plan.active(round(max(0,elapsed)*24000),self.port.media)
        active=self.plan.sentences.index(span) if span else -1
        self.publish(active,elapsed)
        self.trace.append(dict(at=round(time.monotonic()-self.epoch,3),state=self.status,active=active,elapsed=round(elapsed,3)))
    def settled_sample(self):
        # The shared port deliberately fences a .75s EOF callback race. This
        # isolated PCM preview may wait a further bounded interval read-only;
        # it never infers end from duration or stops an unowned player.
        deadline=time.monotonic()+3
        observation=self.port.sample()
        while observation.session!=self.port.session and self.port.player.starts==1 and not self.port.stopping and time.monotonic()<deadline:
            xbmc.sleep(50);observation=self.port.sample()
        return observation
    def tick(self):
        for _ in range(8):
            try:command=self.commands.get_nowait()
            except Empty:break
            if command=='close':
                if self.stop_owned():self.finished=True
                return
            if command==201:
                if self.port is None:
                    if not idle():raise ValueError('readalong-start-not-idle')
                    path=self.cp/('session-'+uuid.uuid4().hex+'.wav')
                    with path.open('xb') as f:f.write((ROOT/'sample.wav').read_bytes())
                    path.chmod(0o600);self.port=KodiPort(path,self.manifest['audio_sha256'],'synthetic-readalong')
                    self.port.open();self.start_deadline=time.monotonic()+6;self.status='Starting'
                elif self.port.owned():
                    paused=self.status=='Paused';self.port.set_paused(not paused);self.status='Playing' if paused else 'Paused'
            elif command==202:
                if self.stop_owned():self.status='Stopped';self.publish()
            elif command==203 and self.port and self.port.owned():self.port.seek(0)
        if not self.port:self.publish();return
        if self.port.owned():
            self.observe(self.settled_sample())
        elif self.status=='Starting' and time.monotonic()<self.start_deadline:return
        elif self.port.player.natural and idle():self.status='Ended';self.publish(-1,9.17)
        elif idle():self.status='Stopped';self.publish()
        else:self.observe(self.settled_sample())

def main():
    lock=None;window=None;cp=None;result={'passed':False,'synthetic':True};previous=None
    try:
        if os.uname().nodename!='AsterTV' or len(sys.argv)!=2:raise ValueError('readalong-hp-only')
        manifest=verify(sys.argv[1])
        lock=os.open(str(ROOT/'entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        sys.path.insert(0,str(ROOT))
        global KodiPort,idle
        from digest_kodi_port import KodiPort,idle
        from narration_frames import SentenceAudio
        from narration_timeline import build
        if not idle() or xbmcgui.getCurrentWindowId()!=10000:return
        home=xbmcgui.Window(10000)
        if home.getProperty('AsterReadAlong.Window'):return
        previous=home.getFocusId();config=json.loads((ROOT/'sample.json').read_text())
        units=(SentenceAudio(0,0,87360),SentenceAudio(1,87360,132720))
        plan=build(' '.join(config['sentences']),config['sentences'],units,manifest['audio_sha256'],config['text_sha256'])
        cp=Path('/storage/.aster-checkpoints')/('aster-readalong-'+str(time.time_ns()));cp.mkdir(mode=0o700)
        window=Reading('ReadAlong.xml',str(ROOT),'Default','1080i')
        window.identity=None;window.commands=SimpleQueue();window.port=None;window.finished=False
        window.cp=cp;window.manifest=manifest;window.plan=plan;window.trace=[];window.epoch=time.monotonic();window.show()
        monitor=xbmc.Monitor();deadline=time.monotonic()+60
        while not monitor.waitForAbort(.05) and not window.finished:
            if window.identity is None:
                if time.monotonic()-window.epoch>5:raise ValueError('readalong-ready-timeout')
                continue
            if xbmcgui.getCurrentWindowId()!=window.identity or time.monotonic()>deadline:
                if window.stop_owned():break
                # Never destroy this hidden WindowXML under foreign media.
                continue
            window.tick()
        result['passed']=window.stop_owned()
    except Exception as error:
        code=str(error);result['error']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
    finally:
        if window:
            # Only this session's independently proven sample may be stopped.
            while not window.stop_owned():xbmc.sleep(100)
            result.update(trace=window.trace,events=window.port.player.events if window.port else [],idle=idle())
            window.close()
            xbmc.sleep(200)
            if previous and idle() and xbmcgui.getCurrentWindowId()==10000:xbmc.executebuiltin('Control.SetFocus('+str(previous)+')')
        if cp:
            p=cp/'session.json';p.write_text(json.dumps(result,indent=2)+'\n');p.chmod(0o600)
        if lock is not None:os.close(lock)
        # Publish closure only after the private journal/focus/lock settle, so
        # an immediate second preview cannot race the previous entry lock.
        if window:xbmcgui.Window(10000).clearProperty('AsterReadAlong.Window')

if __name__=='__main__':main()
