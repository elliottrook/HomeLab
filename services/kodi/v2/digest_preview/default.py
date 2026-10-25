"""Isolated HP Digest browsing preview; no playback or settings writes."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'resources/lib'))
from digest_preview_model import load, Selection, clock

BACK = {9, 10, 92, 216, 247, 257, 275}


def idle():
    def rpc(method, params=None):
        if method not in ('Player.GetActivePlayers', 'Playlist.GetItems'): raise ValueError('read-only-rpc')
        r = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
        if 'error' in r: raise ValueError('local-read-failed')
        return r['result']
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): raise ValueError('redirect-refused')


def read(path, limit):
    if (path, limit) not in (('/static/digest-audio/latest.json', 262144), ('/digest', 1048576)):
        raise ValueError('published-news-only')
    with urllib.request.build_opener(NoRedirect()).open('http://192.168.70.13:8080' + path, timeout=8) as response:
        data = response.read(limit + 1)
    if len(data) > limit: raise ValueError('response-too-large')
    return data


class DigestPreview(xbmcgui.WindowXML):
    def onInit(self):
        self.finished = False
        self.last = -1
        self.setProperty('Digest.Mode', 'HP PREVIEW · BROWSE ONLY · NO PLAYBACK')
        self.setProperty('Digest.Published', datetime.fromisoformat(self.snapshot.generated_at.replace('Z', '+00:00')).astimezone().strftime('%a %d %b · %H:%M %Z'))
        self.setProperty('Digest.Duration', clock(self.snapshot.duration) + ' · published duration')
        items = []
        for row in self.snapshot.entries:
            item = xbmcgui.ListItem(label=row.title)
            item.setProperty('EntryId', row.identity)
            item.setProperty('Clock', clock(row.start))
            items.append(item)
        self.getControl(300).reset()
        self.getControl(300).addItems(items)
        self.getControl(300).selectItem(0)
        self.setFocusId(300)
        self.identity = xbmcgui.getCurrentWindowId()
        xbmcgui.Window(10000).setProperty('AsterDigest.PreviewWindow', str(self.identity))
        self.publish()

    def publish(self):
        index = self.getControl(300).getSelectedPosition()
        if not 0 <= index < len(self.snapshot.entries) or index == self.last: return
        self.selection.select(index)
        row = self.selection.entry
        for key, value in dict(Title=row.title, Summary=row.summary, Source=row.source,
            Image=row.image or 'special://skin/media/30-aster-news-logo.png',
            Position=clock(row.start), Counter=str(index+1)+' / '+str(len(self.snapshot.entries)),
            First='true' if index == 0 else 'false', Last='true' if index == len(self.snapshot.entries)-1 else 'false',
            Ready='true', SelectedId=row.identity).items():
            self.setProperty('Digest.' + key, value)
        self.last = index

    def onClick(self, identity):
        if identity == 200: self.request_close()
        elif identity in (201, 202):
            self.publish()
            self.selection.move(-1 if identity == 201 else 1)
            self.getControl(300).selectItem(self.selection.index)
            self.publish()
            self.setFocusId(300)
        elif identity == 300:
            self.setProperty('Digest.Status', 'Preview only · use the current News page for playback.')

    def onAction(self, action):
        if action.getId() in BACK: self.request_close()

    def request_close(self):
        if idle():
            self.finished = True
            self.close()
        else:
            self.setProperty('Digest.Status', 'Other playback is active · it has not been stopped.')


def main():
    if os.uname().nodename != 'AsterTV': return
    handle = os.open(str(ROOT / 'entry.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not idle() or xbmcgui.getCurrentWindowId() != 10000: return
        home = xbmcgui.Window(10000)
        source_focus = home.getFocusId()
        snapshot = load(read, datetime.now(timezone.utc))
        if not idle() or xbmcgui.getCurrentWindowId() != 10000 or home.getFocusId() != source_focus: return
        window = DigestPreview('DigestPreview.xml', str(ROOT), 'Default', '1080i')
        window.snapshot = snapshot
        window.selection = Selection(snapshot)
        window.finished = False
        window.identity = None
        window.show()
        monitor = xbmc.Monitor()
        try:
            for _ in range(80):
                if window.identity is not None: break
                if monitor.waitForAbort(.05): return
            if window.identity is None: raise ValueError('preview-not-ready')
            while not window.finished and not monitor.waitForAbort(.1):
                if xbmcgui.getCurrentWindowId() == window.identity: window.publish()
                elif idle(): break
                # Never destroy a hidden scripted page beneath foreign media.
        finally:
            window.close()
            home.clearProperty('AsterDigest.PreviewWindow')
            for _ in range(20):
                if xbmcgui.getCurrentWindowId() == 10000: break
                xbmc.sleep(50)
            if idle() and xbmcgui.getCurrentWindowId() == 10000 and source_focus:
                xbmc.executebuiltin('Control.SetFocus(' + str(source_focus) + ')')
            del window
    except (OSError, ValueError, KeyError, RuntimeError):
        xbmcgui.Dialog().notification('Aster News preview', 'Published briefing unavailable or changed. Nothing was played.')
    finally:
        os.close(handle)


if __name__ == '__main__': main()
