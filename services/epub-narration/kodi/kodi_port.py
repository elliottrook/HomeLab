"""Ownership-checked Kodi port for one private, uniquely named Opus copy."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import stat
import time
import uuid

import xbmc


@dataclass(frozen=True)
class Observation:
    session: str
    media: str
    sequence: int
    elapsed: float
    paused: bool = False
    ended: bool = False


class Events(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.starts = 0
        self.finished = False
        self.natural = False

    def onAVStarted(self):
        self.starts += 1

    def onPlayBackStopped(self):
        self.finished = True

    def onPlayBackEnded(self):
        self.natural = True
        self.finished = True


def _rpc(method, params=None):
    if method not in ("Player.GetActivePlayers", "Player.GetProperties", "Playlist.GetItems"):
        raise ValueError("books-read-only-rpc")
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in reply:
        raise ValueError("books-native-read-failed")
    return reply["result"]


def idle():
    return not _rpc("Player.GetActivePlayers") and all(
        _rpc("Playlist.GetItems", {"playlistid": index, "limits": {"start": 0, "end": 1}})["limits"]["total"] == 0
        for index in (0, 1)
    )


class KodiPort:
    def __init__(self, path, expected_hash):
        self.path = Path(path)
        metadata = self.path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or self.path.is_symlink() or not 0 < metadata.st_size <= 1024 ** 3:
            raise ValueError("books-private-bounded-media")
        if not self.path.name.startswith("session-") or self.path.suffix != ".opus":
            raise ValueError("books-unique-session-copy")
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        if digest != expected_hash:
            raise ValueError("books-media-hash")
        self.signature = (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns)
        self.media = digest
        self.session = uuid.uuid4().hex
        self.player = Events()
        self.sequence = 0
        self.opened = False
        self.stopping = False
        self.observed_duration = 0.0
        self.last_target = 0.0

    def open(self):
        if self.opened or not idle():
            raise ValueError("books-idle-single-open")
        self.opened = True
        self.player.play(str(self.path))

    def owned(self):
        try:
            metadata = self.path.lstat()
            active = _rpc("Player.GetActivePlayers")
            audio_only = (
                len(active) == 1
                and active[0].get("playerid") == 0
                and active[0].get("type") == "audio"
                and active[0].get("playertype", "internal") == "internal"
                and set(active[0]) <= {"playerid", "type", "playertype"}
            )
            return (
                self.opened
                and self.player.starts == 1
                and not self.player.finished
                and self.player.isPlayingAudio()
                and self.player.getPlayingFile() == str(self.path)
                and audio_only
                and stat.S_ISREG(metadata.st_mode)
                and not self.path.is_symlink()
                and (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns) == self.signature
            )
        except (OSError, RuntimeError):
            return False

    def _elapsed(self):
        value = self.player.getTime()
        return 0.0 if self.last_target == 0 and -0.25 <= value < 0 else value

    def duration(self):
        if not self.owned():
            raise ValueError("books-native-ownership")
        row = _rpc("Player.GetProperties", {"playerid": 0, "properties": ["totaltime"]})["totaltime"]
        self.observed_duration = ((row["hours"] * 60 + row["minutes"]) * 60 + row["seconds"]) + row["milliseconds"] / 1000
        return self.observed_duration

    def sample(self):
        self.sequence += 1
        if self.owned():
            speed = _rpc("Player.GetProperties", {"playerid": 0, "properties": ["speed"]})["speed"]
            if self.owned():
                return Observation(self.session, self.media, self.sequence, self._elapsed(), paused=speed == 0)
        deadline = time.monotonic() + 5
        while self.player.starts == 1 and not self.stopping and time.monotonic() < deadline:
            active = _rpc("Player.GetActivePlayers")
            if self.player.natural and not active:
                return Observation(self.session, self.media, self.sequence, self.observed_duration, ended=True)
            if self.player.finished and not self.player.natural:
                break
            xbmc.sleep(25)
        return Observation("foreign", self.media, self.sequence, 0)

    def seek(self, seconds):
        if not self.owned() or not isinstance(seconds, (int, float)) or seconds < 0:
            raise ValueError("books-native-ownership")
        self.last_target = float(seconds)
        self.player.seekTime(float(seconds))
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if not self.owned():
                raise ValueError("books-native-ownership")
            if 0 <= self._elapsed() - seconds <= 2:
                return
            xbmc.sleep(50)
        raise ValueError("books-seek-readback")

    def set_paused(self, wanted):
        if type(wanted) is not bool or not self.owned():
            raise ValueError("books-native-ownership")
        paused = _rpc("Player.GetProperties", {"playerid": 0, "properties": ["speed"]})["speed"] == 0
        if paused != wanted:
            self.player.pause()
        deadline = time.monotonic() + 3
        stable = None
        prior = None
        while time.monotonic() < deadline:
            if not self.owned():
                raise ValueError("books-native-ownership")
            current = _rpc("Player.GetProperties", {"playerid": 0, "properties": ["speed"]})["speed"] == 0
            if current == wanted:
                if not wanted:
                    return
                clock = self.player.getTime()
                if prior is None or abs(clock - prior) > 0.03:
                    prior, stable = clock, time.monotonic()
                elif time.monotonic() - stable >= 0.25:
                    return
            xbmc.sleep(50)
        raise ValueError("books-pause-readback")

    def stop(self):
        if self.stopping or not self.owned():
            raise ValueError("books-native-ownership")
        self.stopping = True
        self.player.stop()

    def settle_idle(self):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if idle():
                return True
            xbmc.sleep(50)
        return False
