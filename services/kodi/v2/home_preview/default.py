"""Manual HP Home status preview: one fixed local feed, no device/network I/O."""
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
FEED=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home.json')
MEMBERS={'default.py','resources/skins/Default/1080i/HomePreview.xml',
    'resources/lib/home_freshness.py','resources/lib/home_dashboard_model.py',
    'resources/lib/home_preview_source.py'}
BACK={9,10,92,216,247,257,275}


def verify(pin):
    if not re.fullmatch('[0-9a-f]{64}',pin):raise ValueError('home-preview-pin')
    raw=(ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('home-preview-manifest')
    manifest=json.loads(raw)
    if (manifest['kind']!='hp-home-preview.v1' or
            any(manifest.get(k) is not False for k in ('normal_entry','device_actions','network'))
            or len(manifest['files'])!=5 or {r['path'] for r in manifest['files']}!=MEMBERS):
        raise ValueError('home-preview-contract')
    for row in manifest['files']:
        path=ROOT/row['path']
        if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('home-preview-linked')
        raw=path.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('home-preview-member')


def idle():
    def rpc(method,params=None):
        reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
        if 'error' in reply:raise ValueError('home-preview-local-read')
        return reply['result']
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(
        playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))


class HomePreview(xbmcgui.WindowXML):
    def onInit(self):
        self.last=None;self.revision=0;self.next_tick=0
        self.tick()
        self.setFocusId(301)
        self.identity=xbmcgui.getCurrentWindowId()
        xbmcgui.Window(10000).setProperty('AsterHome.PreviewWindow',str(self.identity))

    def tick(self,force=False):
        if not force and time.monotonic()<self.next_tick:return
        self.next_tick=time.monotonic()+1
        from home_dashboard_model import project
        model=project(self.payload,datetime.now(timezone.utc))
        if model==self.last:return
        self.getControl(501).setLabel(model.notice)
        for index,group in enumerate(model.groups):
            self.getControl(401+index).setLabel(group.summary)
            self.getControl(411+index).setText('\n'.join(group.details))
            self.setProperty('HomePreview.Group'+str(index),group.state)
        self.getControl(502).setLabel((str(model.exceptions)+' sections need attention · ')+
            ('Export '+model.publication if model.publication else 'No current exported values displayed'))
        self.getControl(503).setLabel('Reload only rereads the local file; it does not refresh Home Assistant.')
        self.setProperty('HomePreview.State',model.state)
        self.repaint()
        self.setProperty('HomePreview.Ready','true')
        self.last=model

    def repaint(self):
        self.revision^=1
        self.setProperty('HomePreview.Revision','odd' if self.revision else 'even')

    def onClick(self,identity):self.commands.put(('click',identity))
    def onAction(self,action):
        if action.getId() in BACK:self.commands.put(('back',None))

    def process(self):
        for _ in range(32):
            try:kind,identity=self.commands.get_nowait()
            except Empty:break
            if kind=='back' or identity==200:
                if idle():self.finished=True;self.close()
            elif identity==201:
                from home_preview_source import read_payload
                self.payload=read_payload(FEED)
                self.last=None
                self.tick(force=True)
            elif identity in (301,302,303,304):
                self.getControl(503).setLabel('Read-only status · no device, camera or timer action was sent.')
                self.repaint()
            if self.finished:break


def main():
    if os.uname().nodename!='AsterTV':return
    lock=None
    try:
        if len(sys.argv)!=2:raise ValueError('home-preview-pin-required')
        verify(sys.argv[1])
        lock=os.open(str(ROOT/'entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not idle() or xbmcgui.getCurrentWindowId()!=10000:return
        home=xbmcgui.Window(10000);source_focus=home.getFocusId()
        sys.path.insert(0,str(ROOT/'resources/lib'))
        from home_preview_source import read_payload
        payload=read_payload(FEED)
        if not idle() or xbmcgui.getCurrentWindowId()!=10000 or home.getFocusId()!=source_focus:return
        window=HomePreview('HomePreview.xml',str(ROOT),'Default','1080i')
        window.payload=payload;window.identity=None;window.finished=False;window.commands=SimpleQueue()
        window.show();monitor=xbmc.Monitor()
        try:
            for _ in range(80):
                if window.identity is not None:break
                if monitor.waitForAbort(.05):return
            if window.identity is None:raise ValueError('home-preview-not-ready')
            while not window.finished and not monitor.waitForAbort(.1):
                if xbmcgui.getCurrentWindowId()==window.identity:
                    window.process()
                    if not window.finished:window.tick()
                elif idle():break
                # Never destroy a hidden WindowXML beneath foreign playback.
        finally:
            window.close();home.clearProperty('AsterHome.PreviewWindow')
            for _ in range(20):
                if xbmcgui.getCurrentWindowId()==10000:break
                xbmc.sleep(50)
            if idle() and xbmcgui.getCurrentWindowId()==10000 and source_focus:
                xbmc.executebuiltin('Control.SetFocus('+str(source_focus)+')')
            del window
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        xbmcgui.Dialog().notification('Aster Home preview','Status preview unavailable. No device action was sent.')
    finally:
        if lock is not None:os.close(lock)


if __name__=='__main__':main()
