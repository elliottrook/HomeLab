"""Isolated HP synthetic EPUB preview. No network, audio, bookmarks or settings."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
from queue import SimpleQueue, Empty
import re
import sys
import time
import xbmc
import xbmcgui
ROOT = Path(__file__).resolve().parent
BACK = {9,10,92,216,247,257,275}
MEMBERS = {'default.py','epub_chapter.py','epub_pages.py','sample.epub',
           'resources/skins/Default/1080i/EpubReader.xml'}

def verify(pin):
    if not re.fullmatch('[a-f0-9]{64}', pin): raise ValueError('epub-reader-pin')
    raw = (ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin: raise ValueError('epub-reader-manifest')
    manifest = json.loads(raw)
    if manifest['kind'] != 'hp-epub-reader.v1' or manifest['synthetic'] is not True or any(manifest[k] is not False for k in ('network','playback','progress','normal_entry')):
        raise ValueError('epub-reader-boundary')
    if set(manifest['files']) != MEMBERS: raise ValueError('epub-reader-members')
    for name, wanted in manifest['files'].items():
        path = ROOT/name
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file() or path.stat().st_size > 2097152:
            raise ValueError('epub-reader-member-type')
        if hashlib.sha256(path.read_bytes()).hexdigest() != wanted: raise ValueError('epub-reader-member-drift')

def idle():
    def rpc(method, params):
        reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
        if 'error' in reply: raise ValueError('epub-reader-state')
        return reply['result']
    return not rpc('Player.GetActivePlayers', {}) and all(rpc('Playlist.GetItems', dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))

class Book(xbmcgui.WindowXML):
    def onInit(self):
        self.identity = xbmcgui.getCurrentWindowId(); self.setFocusId(202)
        xbmcgui.Window(10000).setProperty('AsterEpub.Window', str(self.identity))
        self.publish()
    def publish(self):
        reader = self.reader
        self.revision ^= 1
        self.setProperty('Epub.Revision', str(self.revision))
        for size, identity in ((24,501),(30,502),(40,503)):
            self.setProperty('Epub.Size'+str(size), 'true' if reader.size==size else 'false')
            self.getControl(identity).setText(reader.current.body)
        self.getControl(504).setLabel('Page '+str(reader.page+1)+' of '+str(len(reader.pages)))
        self.getControl(203).setLabel('Text size · '+str(reader.size))
        for key, value in dict(Ready='true',Page=reader.page+1,Pages=len(reader.pages),Size=reader.size,
                              Anchor=reader.anchor,Start=reader.current.start,End=reader.current.end,
                              Body=reader.current.body,Chapter=reader.chapter.chapter_sha256).items():
            self.setProperty('Epub.'+key, str(value))
    def onAction(self, action):
        identity = action.getId()
        if identity in BACK: self.commands.put(('close',0))
        elif identity in (1,2): self.commands.put(('page',-1 if identity==1 else 1))
    def onClick(self, identity): self.commands.put(('click',identity))
    def process(self):
        for _ in range(16):
            try: kind, value = self.commands.get_nowait()
            except Empty: break
            if kind=='close' or (kind=='click' and value==200): self.finished=True; self.close(); return
            if kind=='page': self.reader.move(value)
            elif kind=='click' and value in (201,202): self.reader.move(-1 if value==201 else 1)
            elif kind=='click' and value==203: self.reader.resize()
            self.publish()

def main():
    handle = None; window = None
    try:
        if os.uname().nodename!='AsterTV' or len(sys.argv)!=2: raise ValueError('epub-reader-hp-only')
        verify(sys.argv[1])
        handle=os.open(str(ROOT/'entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not idle() or xbmcgui.getCurrentWindowId()!=10000: return
        home=xbmcgui.Window(10000)
        if home.getProperty('AsterEpub.Window'): return
        previous=home.getFocusId()
        sys.path.insert(0,str(ROOT))
        from epub_chapter import chapter
        from epub_pages import Reader
        book=chapter((ROOT/'sample.epub').read_bytes())
        if not idle() or xbmcgui.getCurrentWindowId()!=10000: return
        window=Book('EpubReader.xml',str(ROOT),'Default','1080i')
        window.reader=Reader(book);window.identity=None;window.finished=False
        window.commands=SimpleQueue();window.revision=0;window.show()
        monitor=xbmc.Monitor();ready_deadline=time.monotonic()+5
        while not monitor.waitForAbort(.1) and not window.finished:
            if window.identity is not None:
                # Do not destroy a hidden WindowXML under unrelated playback.
                if idle():
                    if xbmcgui.getCurrentWindowId()!=window.identity: break
                    window.process()
            elif time.monotonic()>ready_deadline: raise ValueError('epub-reader-not-ready')
    except (OSError,ValueError,KeyError,RuntimeError):
        xbmcgui.Dialog().notification('Aster Books', 'Reading preview unavailable. Nothing was played.')
    finally:
        if window is not None:
            window.close();xbmcgui.Window(10000).clearProperty('AsterEpub.Window')
            for _ in range(20):
                if xbmcgui.getCurrentWindowId()==10000: break
                xbmc.sleep(50)
            if idle() and xbmcgui.getCurrentWindowId()==10000 and previous:
                xbmc.executebuiltin('Control.SetFocus('+str(previous)+')')
            del window
        if handle is not None: os.close(handle)

if __name__=='__main__': main()
