"""Manual HP local-generation preview. No delivery job or direct HA connection."""
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
from queue import SimpleQueue,Empty
import re
import sys
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
MEMBERS={'default.py','HomePreviewBase.py','resources/lib/home_refresh.py',
    'resources/lib/home_freshness.py','resources/lib/home_dashboard_model.py',
    'resources/skins/Default/1080i/HomePreview.xml'}
FEED=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home.json')


def verify(pin):
    if not re.fullmatch('[0-9a-f]{64}',pin):raise ValueError('home-refresh-pin')
    raw=(ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('home-refresh-manifest')
    manifest=json.loads(raw)
    if (manifest.get('kind')!='hp-home-refresh-preview.v1' or
        len(manifest['files'])!=len(MEMBERS) or {r['path'] for r in manifest['files']}!=MEMBERS
        or manifest.get('normal_entry') is not False or manifest.get('network') is not False
        or manifest.get('synthetic_fixture_support') is not True):raise ValueError('home-refresh-contract')
    for row in manifest['files']:
        path=ROOT/row['path']
        if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('home-refresh-linked')
        raw=path.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('home-refresh-member')


def run(pin,synthetic):
    verify(pin)  # No bundled imports until every member matches the external pin.
    sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'resources/lib'))
    import HomePreviewBase as base
    from home_refresh import Consumer

    class RefreshPreview(base.HomePreview):
        def onInit(self):
            super().onInit()
            self.getControl(504).setLabel('Synthetic HP refresh test · NOT household readings' if synthetic
                else 'HP preview · local delivery changes only · no direct Home Assistant access')
            self.getControl(505).setLabel('Synthetic files stay in this private test stage; real Home feed is untouched.'
                if synthetic else 'Delivered local status only · no camera images, timer actions or network refresh')
            self.repaint()

        def tick(self,force=False):
            if not force and time.monotonic()<self.next_tick:return
            self.consumer.update(datetime.now(timezone.utc),time.monotonic(),force=force)
            self.payload=self.consumer.payload
            super().tick(force=True)
            self.setProperty('HomeRefresh.Reads',str(self.consumer.reads))
            self.setProperty('HomeRefresh.Generations',str(self.consumer.generations))
            self.setProperty('HomeRefresh.LoadStatus',self.consumer.load_status)
            if self.consumer.load_status=='older-generation':
                self.getControl(503).setLabel('Older delivery ignored; waiting for a current generation.')
            counters=(self.consumer.reads,self.consumer.generations)
            if synthetic and counters!=getattr(self,'counters',None):
                self.getControl(506).setLabel('Synthetic test · file reads '+str(counters[0])+
                    ' · accepted revisions '+str(counters[1]))
                self.counters=counters;self.repaint()

        def process(self):
            for _ in range(32):
                try:kind,identity=self.commands.get_nowait()
                except Empty:break
                if kind=='back' or identity==200:
                    if base.idle():self.finished=True;self.close()
                elif identity==201:
                    self.tick(force=True)
                elif identity in (301,302,303,304):
                    self.getControl(503).setLabel('Read-only status · no device, camera or timer action was sent.')
                    self.repaint()
                if self.finished:break

    if not base.idle() or xbmcgui.getCurrentWindowId()!=10000:return
    home=xbmcgui.Window(10000);source_focus=home.getFocusId()
    if synthetic and not re.fullmatch('aster-home-refresh-preview[1-9][0-9]?',ROOT.name):
        raise ValueError('home-refresh-synthetic-stage')
    source=ROOT/'synthetic-home.json' if synthetic else FEED
    consumer=Consumer(source);consumer.update(datetime.now(timezone.utc),time.monotonic())
    if not base.idle() or xbmcgui.getCurrentWindowId()!=10000 or home.getFocusId()!=source_focus:return
    window=RefreshPreview('HomePreview.xml',str(ROOT),'Default','1080i')
    window.consumer=consumer;window.identity=None;window.finished=False;window.commands=SimpleQueue()
    window.show();monitor=xbmc.Monitor()
    try:
        for _ in range(80):
            if window.identity is not None:break
            if monitor.waitForAbort(.05):return
        if window.identity is None:raise ValueError('home-refresh-not-ready')
        while not window.finished and not monitor.waitForAbort(.1):
            if xbmcgui.getCurrentWindowId()==window.identity:
                window.process()
                if not window.finished:window.tick()
            elif base.idle():break
    finally:
        window.close();home.clearProperty('AsterHome.PreviewWindow')
        for _ in range(20):
            if xbmcgui.getCurrentWindowId()==10000:break
            xbmc.sleep(50)
        if base.idle() and xbmcgui.getCurrentWindowId()==10000 and source_focus:
            xbmc.executebuiltin('Control.SetFocus('+str(source_focus)+')')
        del window


def main():
    if os.uname().nodename!='AsterTV':return
    lock=None
    try:
        if len(sys.argv) not in (2,3) or (len(sys.argv)==3 and sys.argv[2]!='synthetic'):
            raise ValueError('home-refresh-arguments')
        verify(sys.argv[1])
        lock=os.open(str(ROOT/'entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(sys.argv[1],len(sys.argv)==3)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        xbmcgui.Dialog().notification('Aster Home preview','Local delivery view unavailable. No device action was sent.')
    finally:
        if lock is not None:os.close(lock)


if __name__=='__main__':main()
