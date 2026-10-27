"""Pinned HP Lab Aster Books reader for compiler-ready narration."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
from queue import Empty, SimpleQueue
import re
import shutil
import stat
import sys
import time
import uuid

import xbmc
import xbmcgui


ROOT = Path(__file__).resolve().parent
BACK = {9, 10, 92, 216, 247, 257, 275}
STATE = Path("/storage/.aster-state/aster-books-compiler-reader-v1/progress")
CACHE = Path("/storage/.aster-cache/aster-books-compiler-reader-v1")
MEMBERS = {
    "default.py",
    "kodi_port.py",
    "reader_pages.py",
    "runtime/epub_narration/__init__.py",
    "runtime/epub_narration/aster_books.py",
    "runtime/epub_narration/publication.py",
    "resources/skins/Default/1080i/AsterBooksCompiler.xml",
} | {"resources/skins/Default/media/" + name + ".png" for name in (
    "play", "pause", "stop", "page-back", "page-next", "previous"
)}


def require(value, code):
    if not value:
        raise ValueError(code)


def verify(pin, identity):
    require(re.fullmatch("[a-f0-9]{64}", pin) is not None, "books-pin")
    require(re.fullmatch("[1-9][0-9]{0,9}", identity) is not None, "books-id")
    raw = (ROOT / "bundle.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin, "books-bundle-pin")
    manifest = json.loads(raw)
    require(
        manifest.get("kind") == "aster-books-compiler-reader-v1"
        and manifest.get("hp_only") is True
        and manifest.get("active") is True
        and manifest.get("normal_entry") is True
        and manifest.get("network") is False
        and manifest.get("shared_progress") is False,
        "books-bundle-boundary",
    )
    require(set(manifest.get("files", {})) == MEMBERS, "books-bundle-members")
    for name, wanted in manifest["files"].items():
        path = ROOT / name
        metadata = path.lstat()
        require(stat.S_ISREG(metadata.st_mode) and not path.is_symlink(), "books-bundle-file")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == wanted, "books-bundle-drift")
    return int(identity)


class Window(xbmcgui.WindowXML):
    def onInit(self):
        self.identity = xbmcgui.getCurrentWindowId()
        self.setFocusId(500)
        xbmcgui.Window(10000).setProperty("AsterBooksCompiler.Window", str(self.identity))
        self.publish()

    def onClick(self, identity):
        self.commands.put(identity)

    def onAction(self, action):
        if action.getId() in BACK:
            self.commands.put("close")

    def _status(self, state, active=None):
        self.status = state
        self.setProperty("Books.State", state)
        self.setProperty("Books.Chapter", str(self.session.chapter))
        self.setProperty("Books.Chapters", str(len(self.session.book.chapters)))
        self.setProperty("Books.Sample", str(self.session.sample))
        self.setProperty("Books.Active", str(-1 if active is None else self.session.current.cues.index(active)))

    def publish(self, active=None):
        if active is None:
            active = self.session.current.cue_at(self.session.sample)
        if active is not None:
            self.reader.go(active.source_start)
        span = None if active is None else (active.source_start, active.source_end)
        body = self.render(self.session.current.text, self.reader.current, span)
        for identity in (501, 502, 503):
            self.getControl(identity).setText(body)
        for size in (24, 30, 40):
            self.setProperty("Books.Size" + str(size), "true" if self.reader.size == size else "false")
        seconds = self.session.sample / self.session.current.sample_rate
        total = self.session.current.total_samples / self.session.current.sample_rate
        self.setProperty(
            "Books.Status",
            self.status + " · chapter " + str(self.session.chapter) + " / " + str(len(self.session.book.chapters))
            + " · " + time.strftime("%M:%S", time.gmtime(seconds))
            + " / " + time.strftime("%M:%S", time.gmtime(total)),
        )
        self._status(self.status, active)
        self.getControl(207).setLabel("Text " + str(self.reader.size))

    def _save(self, complete=False):
        self.session.progress.save(self.session.book, self.session.chapter, self.session.sample, complete)

    def _release(self):
        require(self.idle(), "books-cache-player-active")
        if self.cache is not None and self.cache.exists():
            metadata = self.cache.lstat()
            require(stat.S_ISREG(metadata.st_mode) and not self.cache.is_symlink(), "books-cache-ownership")
            self.cache.unlink()
        self.cache = None
        self.port = None

    def _begin(self):
        require(self.idle(), "books-start-not-idle")
        CACHE.mkdir(mode=0o700, parents=True, exist_ok=True)
        CACHE.chmod(0o700)
        self.cache = CACHE / ("session-" + uuid.uuid4().hex + ".opus")
        with self.cache.open("xb") as output:
            with self.session.current.audio.open("rb") as source:
                shutil.copyfileobj(source, output, 1024 * 1024)
        self.cache.chmod(0o600)
        self.port = self.KodiPort(self.cache, self.session.current.audio_sha256)
        self.port.open()
        self.pending_seek = self.session.sample / self.session.current.sample_rate
        self.deadline = time.monotonic() + 8
        self.status = "Starting"

    def _stop_owned(self, save=True):
        if self.port and self.port.owned():
            observation = self.port.sample()
            self.session.sample = round(max(0, observation.elapsed) * self.session.current.sample_rate)
            self.session.sample = min(self.session.sample, self.session.current.total_samples)
            if save:
                self._save()
            self.port.stop()
            require(self.port.settle_idle(), "books-stop-unsettled")
        elif self.port and self.port.player.starts == 1 and self.port.player.natural:
            require(self.port.settle_idle(), "books-end-unsettled")
            self._release()
        elif not self.idle():
            return False
        return True

    def _select_chapter(self, target):
        if not 1 <= target <= len(self.session.book.chapters):
            return
        require(self._stop_owned(), "books-chapter-foreign-player")
        if self.port:
            self._release()
        self.session.select_chapter(target)
        self.reader = self.Reader(self.session.current.text)
        self.status = "Ready"
        self.publish()

    def _observe(self, observation):
        require(observation.session == self.port.session and observation.media == self.port.media,
                "books-playback-ownership")
        if observation.ended:
            require(self.port.player.natural, "books-end-not-natural")
            require(self.port.settle_idle(), "books-end-unsettled")
            self._release()
            self.session.sample = self.session.current.total_samples
            if self.session.chapter == len(self.session.book.chapters):
                self._save(True)
                self.status = "Complete"
            else:
                self._save()
                self.session.select_chapter(self.session.chapter + 1)
                self.reader = self.Reader(self.session.current.text)
                self.status = "Next chapter ready"
            self.publish()
            return
        self.session.sample = round(max(0, observation.elapsed) * self.session.current.sample_rate)
        self.session.sample = min(self.session.sample, self.session.current.total_samples)
        self.status = "Paused" if observation.paused else "Reading"
        active = self.session.current.cue_at(self.session.sample)
        if active is not None:
            self.setProperty("Books.HighlightObserved", "true")
        self.publish(active)

    def tick(self):
        for _ in range(12):
            try:
                command = self.commands.get_nowait()
            except Empty:
                break
            if command == "close":
                if self._stop_owned():
                    self.finished = True
                return
            if command == 201:
                if self.port is None:
                    self._begin()
                elif self.port.owned():
                    paused = self.status == "Paused"
                    self.port.set_paused(not paused)
                    self.status = "Reading" if paused else "Paused"
                elif self.idle():
                    self._release()
                    self._begin()
            elif command == 202:
                if self._stop_owned():
                    self.status = "Stopped"
                    self.publish()
            elif command == 203:
                self._select_chapter(self.session.chapter - 1)
            elif command == 204:
                self._select_chapter(self.session.chapter + 1)
            elif command == 205 and self.port and self.port.owned():
                self.port.seek(0)
                self.session.sample = 0
                self._save()
            elif command == 206 and (self.port is None or not self.port.owned()) and self.idle():
                path = self.session.progress._path(self.session.book)
                if path.exists():
                    path.unlink()
                self.session.sample = 0
                self.status = "Progress cleared"
                self.publish()
            elif command == 207:
                self.reader.resize()
                self.publish()
        if not self.port:
            return
        if self.port.owned():
            if self.pending_seek is not None:
                target = self.pending_seek
                self.pending_seek = None
                self.port.duration()
                if target > 0:
                    self.port.seek(target)
            self._observe(self.port.sample())
        elif self.status == "Starting" and time.monotonic() < self.deadline:
            return
        elif self.port.player.starts == 1 and not self.port.stopping:
            self._observe(self.port.sample())
        elif self.idle():
            self.status = "Stopped"
            self.publish()
        else:
            raise ValueError("books-foreign-player")


def main():
    handle = None
    window = None
    previous = None
    previous_window = None
    try:
        os.umask(0o077)
        require(os.uname().nodename == "AsterTV" and len(sys.argv) == 3, "books-hp-only")
        book_id = verify(sys.argv[1], sys.argv[2])
        handle = os.open(str(ROOT / "entry.lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sys.path.insert(0, str(ROOT / "runtime"))
        sys.path.insert(0, str(ROOT))
        from epub_narration.aster_books import BetaSession, ProgressStore, load_ready_book, probe_opus
        from kodi_port import KodiPort, idle
        from reader_pages import Reader, render
        previous_window = xbmcgui.getCurrentWindowId()
        require(idle() and previous_window in (10000, 11110, 11118), "books-idle-entry")
        home = xbmcgui.Window(10000)
        require(not home.getProperty("AsterBooksCompiler.Window"), "books-already-open")
        previous = xbmcgui.Window(previous_window).getFocusId()
        book = load_ready_book(ROOT / "data", book_id, probe_opus)
        session = BetaSession(book, ProgressStore(STATE))
        window = Window("AsterBooksCompiler.xml", str(ROOT), "Default", "1080i")
        window.identity = None
        window.commands = SimpleQueue()
        window.finished = False
        window.session = session
        window.reader = Reader(session.current.text)
        window.render = render
        window.Reader = Reader
        window.KodiPort = KodiPort
        window.idle = idle
        window.port = None
        window.cache = None
        window.pending_seek = None
        window.status = "Complete" if session.progress.load(book)["complete"] else ("Resume ready" if session.sample else "Ready")
        window.show()
        monitor = xbmc.Monitor()
        ready = time.monotonic() + 5
        while not monitor.waitForAbort(0.05) and not window.finished:
            if window.identity is None:
                require(time.monotonic() < ready, "books-ready-timeout")
                continue
            if xbmcgui.getCurrentWindowId() != window.identity:
                if window._stop_owned():
                    break
                continue
            window.tick()
    except Exception as error:
        code = str(error)
        safe = code if re.fullmatch("[a-z0-9-]{1,100}", code) else type(error).__name__
        xbmc.log("Aster Books reader: " + safe, xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Aster Books", "Narrated edition unavailable. Nothing else was stopped.")
    finally:
        if window:
            while not window._stop_owned():
                xbmc.sleep(100)
            window.close()
            xbmc.sleep(200)
            window._release()
        if handle is not None:
            os.close(handle)
        xbmcgui.Window(10000).clearProperty("AsterBooksCompiler.Window")
        if (previous and previous_window is not None and
                xbmcgui.getCurrentWindowId() == previous_window and
                (not window or window.idle())):
            xbmc.executebuiltin("Control.SetFocus(" + str(previous) + ")")


if __name__ == "__main__":
    main()
