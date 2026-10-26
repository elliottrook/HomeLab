"""HP published-summary preview: LAN read only, no playback or browser actions."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import textwrap
from queue import SimpleQueue, Empty
import urllib.request
from datetime import datetime
import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
BACK = {9, 10, 92, 216, 247, 257, 275}
MEMBERS = {'default.py', 'resources/lib/digest_read_model.py',
           'resources/lib/digest_read_pages.py',
           'resources/skins/Default/1080i/DigestReader.xml'}


def verify(pin):
    if not re.fullmatch('[a-f0-9]{64}', pin): raise ValueError('reader-pin')
    raw = (ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin: raise ValueError('reader-manifest')
    manifest = json.loads(raw)
    if (manifest.get('kind') != 'hp-digest-reader.v1' or
            any(manifest.get(k) is not False for k in ('playback', 'external_requests', 'normal_entry')) or
            len(manifest['files']) != len(MEMBERS) or
            {r['path'] for r in manifest['files']} != MEMBERS):
        raise ValueError('reader-members')
    for row in manifest['files']:
        path = ROOT/row['path']
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('reader-linked-path')
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('reader-member-drift')


def idle():
    def rpc(method, params=None):
        reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
                             method=method, params=params or {}))))
        if 'error' in reply: raise ValueError('reader-local-read')
        return reply['result']
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(
        playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): raise ValueError('reader-redirect')


def read():
    with urllib.request.build_opener(NoRedirect()).open(
            'http://192.168.70.13:8080/digest', timeout=8) as response:
        raw = response.read(1048577)
    if len(raw) > 1048576: raise ValueError('reader-response-size')
    return raw


def context(args, window, focus, ready):
    if not args and window == 10000:
        return 10000
    if args == ['news'] and window == 11111 and focus == 312 and ready == 'true':
        return 11111
    raise ValueError('reader-explicit-source-required')


class DigestReader(xbmcgui.WindowXML):
    def onInit(self):
        from digest_read_pages import Reader
        self.reader = Reader(self.snapshot)
        self.last = None
        self.revision = 0
        self.setProperty('Reading.Fetched', self.fetched)
        items = []
        for row in self.snapshot.cards:
            item = xbmcgui.ListItem(label=textwrap.shorten(row.title, width=70, placeholder='…'))
            item.setProperty('ReadingId', row.identity)
            items.append(item)
        self.getControl(300).reset()
        self.getControl(300).addItems(items)
        self.setFocusId(300)
        self.publish()
        self.identity = xbmcgui.getCurrentWindowId()
        xbmcgui.Window(10000).setProperty('AsterDigest.ReaderWindow', str(self.identity))

    def publish(self):
        index = self.getControl(300).getSelectedPosition()
        if not 0 <= index < len(self.snapshot.cards): return
        self.reader.select(index)
        key = (index, self.reader.page)
        if key == self.last: return
        reader = self.reader
        values = dict(Title=reader.card.title, Body=reader.current.body,
                Section=reader.current.heading, SelectedId=reader.card.identity,
                Page=str(reader.page+1)+' / '+str(len(reader.pages)),
                First='true' if reader.page == 0 else 'false',
                Last='true' if reader.page == len(reader.pages)-1 else 'false',
                Story=str(index+1)+' / '+str(len(self.snapshot.cards)), Ready='true')
        # These are this WindowXML's own controls, not cross-window diagnostics.
        # Property-only labels can retain cached text in Kodi's dirty renderer.
        self.getControl(501).setText(values['Title'])
        self.getControl(502).setLabel(values['Section'])
        self.getControl(503).setText(values['Body'])
        self.getControl(504).setLabel(values['Page'])
        self.getControl(505).setLabel('Stories · '+values['Story'])
        for key, value in values.items():
            self.setProperty('Reading.'+key, value)
        self.revision ^= 1
        self.setProperty('Reading.Revision', 'odd' if self.revision else 'even')
        self.last = (index, reader.page)

    def onClick(self, identity):
        self.commands.put(('click', identity))

    def apply_click(self, identity):
        if identity == 200: self.request_close()
        elif identity in (201, 202):
            self.publish()
            self.reader.move_page(-1 if identity == 201 else 1)
            self.publish()
            # Both paging controls stay focusable; the model clamps page ends.
        elif identity == 300:
            self.publish()
            self.setFocusId(202 if len(self.reader.pages)>1 else 200)

    def onAction(self, action):
        if action.getId() in BACK: self.commands.put(('back', None))

    def process(self):
        # All post-init model/UI changes occur on the script loop, in order.
        for _ in range(32):
            try: kind, identity = self.commands.get_nowait()
            except Empty: break
            if kind == 'back': self.request_close()
            elif kind == 'click': self.apply_click(identity)
            if self.finished: break

    def request_close(self):
        if idle():
            self.finished = True
            self.close()


def main():
    if os.uname().nodename != 'AsterTV': return
    handle = None
    try:
        if len(sys.argv) not in (2, 3): raise ValueError('reader-pin-required')
        verify(sys.argv[1])
        handle = os.open(str(ROOT/'entry.lock'), os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
        fcntl.flock(handle, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not idle(): return
        home = xbmcgui.Window(10000)
        source_id = xbmcgui.getCurrentWindowId()
        if source_id not in (10000, 11111): raise ValueError('reader-source-window')
        source = xbmcgui.Window(source_id)
        source_focus = source.getFocusId()
        context(sys.argv[2:], source_id, source_focus, source.getProperty('AsterHub.Ready'))
        sys.path.insert(0, str(ROOT/'resources/lib'))
        from digest_read_model import read_page
        snapshot = read_page(read())
        fetched = 'Loaded ' + datetime.now().astimezone().strftime('%d %b · %H:%M %Z')
        if not snapshot.cards: raise ValueError('reader-empty')
        if not idle() or xbmcgui.getCurrentWindowId() != source_id or source.getFocusId() != source_focus: return
        context(sys.argv[2:], source_id, source_focus, source.getProperty('AsterHub.Ready'))
        window = DigestReader('DigestReader.xml', str(ROOT), 'Default', '1080i')
        window.snapshot, window.identity, window.finished = snapshot, None, False
        window.fetched = fetched
        window.commands = SimpleQueue()
        window.show()
        monitor = xbmc.Monitor()
        try:
            for _ in range(80):
                if window.identity is not None: break
                if monitor.waitForAbort(.05): return
            if window.identity is None: raise ValueError('reader-not-ready')
            while not window.finished and not monitor.waitForAbort(.1):
                if xbmcgui.getCurrentWindowId() == window.identity:
                    window.process()
                    if not window.finished: window.publish()
                elif idle(): break
                # Do not destroy a hidden WindowXML under foreign playback.
        finally:
            return_to_news = (source_id == 11111 and window.finished and idle()
                              and xbmcgui.getCurrentWindowId() in (window.identity, source_id, 10000))
            window.close()
            home.clearProperty('AsterDigest.ReaderWindow')
            if return_to_news:
                xbmc.executebuiltin('ActivateWindow(1111)')
                for _ in range(100):
                    if (xbmcgui.getCurrentWindowId() == 11111 and
                            source.getProperty('AsterHub.Ready') == 'true' and
                            source.getProperty('AsterHub.RowsReady') == 'true'): break
                    if monitor.waitForAbort(.05): break
            for _ in range(20):
                if xbmcgui.getCurrentWindowId() in (source_id, 10000): break
                xbmc.sleep(50)
            if idle() and xbmcgui.getCurrentWindowId() == source_id and source_focus:
                xbmc.executebuiltin('Control.SetFocus('+str(source_focus)+')')
            del window
    except (OSError, ValueError, KeyError, RuntimeError):
        xbmcgui.Dialog().notification('Aster News reader', 'Published reading page unavailable. Nothing was played.')
    finally:
        if handle is not None: os.close(handle)


if __name__ == '__main__': main()
