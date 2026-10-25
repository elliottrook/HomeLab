"""Isolated HP Digest player. Normal News and backend remain unchanged."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
from queue import SimpleQueue, Empty
import sys
import time
import uuid
import xbmc
import xbmcgui
import xbmcvfs

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'resources/lib'))
from digest_preview_source import read
from digest_preview_model import load, clock
from digest_timeline import build, build_preview
from digest_player_model import Presentation
from digest_kodi_port import KodiPort, idle
from digest_player_adapter import Adapter
import deploy_startup as guard

BACK = {9, 10, 92, 216, 247, 257, 275}


def require(value, code):
    if not value: raise ValueError(code)


def until(check, code, seconds=10):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise ValueError(code)


class DigestPlayer(xbmcgui.WindowXML):
    def onInit(self):
        self.last_display = None
        self.active_row = None
        self.last_row = None
        self.adapter = None
        self.port = None
        self.timeline = None
        self.mapping = None
        self.closing = False
        self.finished = False
        self.requests = SimpleQueue()
        self.setProperty('Digest.Mode', 'HP PLAYER PILOT · EXISTING BRIEFING AUDIO')
        self.setProperty('Digest.Published', datetime.fromisoformat(self.snapshot.generated_at.replace('Z', '+00:00')).astimezone().strftime('%a %d %b · %H:%M %Z'))
        self.setProperty('Digest.Duration', clock(self.snapshot.duration))
        self.setProperty('Digest.Status', 'Play the full briefing, or select a story.')
        control = self.getControl(300)
        control.reset()
        for row in self.snapshot.entries:
            item = xbmcgui.ListItem(label=row.title)
            item.setProperty('EntryId', row.identity)
            item.setProperty('Clock', clock(row.start))
            item.setProperty('Active', 'false')
            control.addItem(item)
        control.selectItem(0)
        self.setFocusId(300)
        self.identity = xbmcgui.getCurrentWindowId()
        xbmcgui.Window(10000).setProperty('AsterDigest.PlayerWindow', str(self.identity))
        self.publish(0)

    def publish(self, index):
        if index != self.last_display:
            row = self.snapshot.entries[index]
            for key, value in dict(Title=row.title, Summary=row.summary, Source=row.source,
                Image=row.image or 'special://skin/media/30-aster-news-logo.png',
                SelectedId=row.identity).items(): self.setProperty('Digest.'+key, value)
            self.last_display = index
        self.setProperty('Digest.Counter', str(index+1)+' / '+str(len(self.snapshot.entries)))
        self.setProperty('Digest.First', 'true' if index == 0 else 'false')
        self.setProperty('Digest.Last', 'true' if index == len(self.snapshot.entries)-1 else 'false')

    def start(self, row):
        require(idle(), 'other-playback-active')
        require(read('/static/digest-audio/latest.json', 262144) == self.feed_raw, 'edition-changed-reopen-player')
        require(xbmcgui.getCurrentWindowId() == self.identity, 'player-no-longer-visible')
        source = Path(xbmcvfs.translatePath('special://temp/skin.asterhome/digest')) / (
            'digest-' + hashlib.sha256(self.feed['generated_at'].encode()).hexdigest()[:16] + '.mp3')
        require(source.is_file() and not source.is_symlink() and 0 < source.stat().st_size <= 32*1024*1024, 'existing-audio-cache-required')
        media = source.read_bytes()
        target = self.checkpoint / ('session-'+uuid.uuid4().hex+'.mp3')
        with target.open('xb') as handle:
            os.chmod(target, 0o600)
            handle.write(media)
        require(read('/static/digest-audio/latest.json', 262144) == self.feed_raw, 'edition-changed-reopen-player')
        provisional = build_preview(self.feed, datetime.now(timezone.utc))
        self.port = KodiPort(target, hashlib.sha256(media).hexdigest(), provisional.identity)
        self.port.open()
        until(lambda:self.port.owned() and self.port.duration() > 0 and self.port.player.getTime() >= 0, 'owned-audio-not-ready')
        self.timeline = build(self.feed, self.port.duration(), datetime.now(timezone.utc))
        self.mapping = Presentation(self.snapshot, self.timeline)
        self.port.edition = self.timeline.identity
        self.adapter = Adapter(self.timeline, self.port.session, self.port.media, self.port)
        self.adapter.poll()
        if row != 0: self.adapter.seek(self.mapping.chapter(row))
        self.last_row = None

    def onClick(self, identity):
        if identity == 300: self.requests.put(('row', self.getControl(300).getSelectedPosition()))
        elif identity == 200: self.requests.put(('close', None))
        elif identity in (201, 202, 203, 204): self.requests.put((str(identity), None))

    def onAction(self, action):
        if action.getId() in BACK: self.requests.put(('close', None))

    def request_close(self):
        if self.closing: return
        self.closing = True
        try:
            stopped = self.stop_owned()
            if not stopped and not idle():
                self.setProperty('Digest.Status', 'Other or uncertain playback was not stopped.')
        finally: self.finished = True

    def stop_owned(self):
        # A failed seek is never retried. Explicit exit can still issue one
        # distinct Stop when the native port independently proves ownership.
        if self.adapter is not None and self.adapter.fenced:
            if self.port is not None and not self.port.stopping and self.port.owned():
                self.port.stop()
                return self.port.idle()
            return idle()
        if self.adapter is not None and not self.adapter.closed:
            return self.adapter.close()
        if self.adapter is None and self.port is not None and not self.port.stopping and self.port.owned():
            self.port.stop()
            return self.port.idle()
        return idle()

    def process(self, action, value):
        if action == 'close': self.request_close(); return
        if action == '204':
            stopped = self.stop_owned()
            require(stopped or idle(), 'stop-not-confirmed')
            self.setProperty('Digest.Status', 'Stopped')
            self.setProperty('Digest.Playing', 'false')
            self.adapter = None
            self.clear_active()
            return
        active = self.adapter is not None and not self.adapter.closed and self.adapter.state.view.phase in ('opening', 'story')
        if action == 'row':
            if active: self.adapter.seek(self.mapping.chapter(value))
            else: self.start(value)
        elif action == '203':
            if active: self.adapter.paused(not self.adapter.state.view.paused)
            else: self.start(0)
        elif action in ('201', '202'):
            index = self.active_row if active else self.getControl(300).getSelectedPosition()
            target = index+(-1 if action == '201' else 1)
            if 0 <= target < len(self.snapshot.entries):
                if active: self.adapter.seek(self.mapping.chapter(target))
                else: self.getControl(300).selectItem(target)

    def clear_active(self):
        for index in range(len(self.snapshot.entries)):
            self.getControl(300).getListItem(index).setProperty('Active', 'false')
        self.active_row = None
        self.last_row = None
        self.setProperty('Digest.ActiveId', '')
        self.setProperty('Digest.Paused', 'false')

    def tick(self):
        try:
            action, value = self.requests.get_nowait()
            self.process(action, value)
        except Empty: pass
        if self.finished: return
        selected = self.getControl(300).getSelectedPosition()
        if self.adapter is None:
            self.publish(selected)
            return
        view = self.adapter.poll()
        self.setProperty('Digest.StartEvents', str(self.port.player.starts))
        self.setProperty('Digest.Callbacks', ','.join(self.port.player.events))
        if self.adapter.fenced:
            if not self.getProperty('Digest.ErrorCode'):
                self.setProperty('Digest.ErrorCode', 'ownership-lost' if view.phase == 'lost' else 'readback-not-current')
            self.setProperty('Digest.Status', 'Playback ownership changed · controls disabled. Back to leave.')
            self.setProperty('Digest.Playing', 'false')
            self.clear_active()
            return
        row = self.mapping.row(view)
        self.setProperty('Digest.Position', clock(view.elapsed))
        self.setProperty('Digest.Paused', 'true' if view.paused else 'false')
        self.setProperty('Digest.Playing', 'true' if row is not None else 'false')
        self.setProperty('Digest.Status', 'Briefing complete' if view.phase == 'ended' else ('Paused' if view.paused else 'Playing'))
        if row is not None:
            self.active_row = row
            if row != self.last_row:
                for index in range(len(self.snapshot.entries)):
                    self.getControl(300).getListItem(index).setProperty('Active', 'true' if index == row else 'false')
                self.setProperty('Digest.ActiveId', self.snapshot.entries[row].identity)
                self.getControl(300).selectItem(row)
                self.last_row = row
            self.publish(row)
        elif view.phase == 'ended': self.clear_active()


def main():
    if os.uname().nodename != 'AsterTV': return
    lock = os.open(str(ROOT / 'entry.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    window = None
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(idle() and xbmcgui.getCurrentWindowId() == 10000, 'home-idle-required')
        source_focus = xbmcgui.Window(10000).getFocusId()
        raw = read('/static/digest-audio/latest.json', 262144)
        feed = json.loads(raw)
        snapshot = load(read, datetime.now(timezone.utc))
        require(snapshot.identity == build_preview(feed, datetime.now(timezone.utc)).identity
            and read('/static/digest-audio/latest.json', 262144) == raw, 'edition-changed')
        require(idle() and xbmcgui.getCurrentWindowId() == 10000
            and xbmcgui.Window(10000).getFocusId() == source_focus, 'source-changed')
        stage_raw = (ROOT / 'manifest.json').read_bytes()
        manifest = json.loads(stage_raw)
        for row in manifest['files']:
            require(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], 'stage-drift')
        checkpoint = Path('/storage/.aster-checkpoints') / ('aster-digest-player-'+str(time.time_ns()))
        checkpoint.mkdir(mode=0o700)
        (checkpoint / 'manifest.json').write_bytes(stage_raw)
        (checkpoint / 'before.json').write_text(json.dumps(guard.snapshot()))
        window = DigestPlayer('DigestPlayer.xml', str(ROOT), 'Default', '1080i')
        window.feed, window.feed_raw, window.snapshot, window.checkpoint = feed, raw, snapshot, checkpoint
        window.identity = None
        window.show()
        until(lambda:window.identity is not None, 'player-ui-not-ready', 4)
        monitor = xbmc.Monitor()
        while not window.finished and not monitor.waitForAbort(.1):
            try:
                if xbmcgui.getCurrentWindowId() == window.identity: window.tick()
                elif idle() or (window.port is not None and window.port.owned()): window.request_close()
                elif window.adapter is not None:
                    window.adapter.poll()  # Relinquish; never destroy a hidden page beneath foreign media.
            except (OSError, ValueError, KeyError, RuntimeError, TypeError) as error:
                code = str(error)
                code = code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__
                window.setProperty('Digest.ErrorCode', code)
                (checkpoint / ('error-'+str(time.time_ns())+'.json')).write_text(json.dumps(dict(
                    code=code, start_events=window.port.player.starts if window.port else 0,
                    fenced=window.adapter.fenced if window.adapter else False)))
                window.setProperty('Digest.Status', 'Action unavailable · Back to leave; no automatic retry.')
                window.requests = SimpleQueue()
        window.stop_owned()
    except (OSError, ValueError, KeyError, RuntimeError, TypeError):
        xbmcgui.Dialog().notification('Aster Digest pilot', 'Unavailable or changed. Current News is unchanged.')
    finally:
        if window is not None:
            try: window.stop_owned()
            except (OSError, ValueError, RuntimeError): pass
            window.close()
            xbmcgui.Window(10000).clearProperty('AsterDigest.PlayerWindow')
            if idle():
                until(lambda:xbmcgui.getCurrentWindowId() == 10000, 'home-not-restored', 4)
                xbmc.executebuiltin('Control.SetFocus('+str(source_focus)+')')
        os.close(lock)


if __name__ == '__main__': main()
