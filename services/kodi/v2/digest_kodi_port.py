"""Kodi port for an isolated, uniquely named local Digest trial copy.

Not the normal News entry. The caller checkpoints first and supplies a private
session-specific MP3 copy. Callback continuity AND exact local file identity
are required; the same ordinary cache path alone never establishes ownership.
"""
import hashlib
import json
from pathlib import Path
import stat
import time
import uuid
import xbmc
from digest_playback_state import Observation


class Events(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.starts = 0
        self.finished = False

    def onAVStarted(self): self.starts += 1
    def onPlayBackStopped(self): self.finished = True
    def onPlayBackEnded(self): self.finished = True


def rpc(method, params=None):
    if method not in ('Player.GetActivePlayers', 'Player.GetProperties', 'Playlist.GetItems'):
        raise ValueError('read-only-rpc')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    if 'error' in reply: raise ValueError('native-read-failed')
    return reply['result']


def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(playlistid=i,
        limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))


class KodiPort:
    def __init__(self, path, expected_hash, edition):
        self.path = Path(path)
        meta = self.path.lstat()
        if not stat.S_ISREG(meta.st_mode) or not 0 < meta.st_size <= 32*1024*1024:
            raise ValueError('private-bounded-media-required')
        if not self.path.name.startswith('session-') or self.path.suffix != '.mp3':
            raise ValueError('unique-session-copy-required')
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        if digest != expected_hash: raise ValueError('media-hash-mismatch')
        self.signature = (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns)
        self.media = digest
        self.edition = edition
        self.session = uuid.uuid4().hex
        self.player = Events()
        self.sequence = 0
        self.opened = False
        self.stopping = False

    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.opened = True
        self.player.play(str(self.path))

    def owned(self):
        try:
            meta = self.path.lstat()
            active = rpc('Player.GetActivePlayers')
            audio_only = (len(active) == 1 and active[0].get('playerid') == 0
                and active[0].get('type') == 'audio'
                and active[0].get('playertype', 'internal') == 'internal'
                and set(active[0]) <= {'playerid', 'type', 'playertype'})
            return (self.opened and self.player.starts == 1 and not self.player.finished
                and self.player.isPlayingAudio() and self.player.getPlayingFile() == str(self.path)
                and audio_only
                and stat.S_ISREG(meta.st_mode)
                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature)
        except (OSError, RuntimeError): return False

    def duration(self):
        if not self.owned(): raise ValueError('native-ownership-lost')
        row = rpc('Player.GetProperties', dict(playerid=0, properties=['totaltime']))['totaltime']
        return ((row['hours']*60+row['minutes'])*60+row['seconds']) + row['milliseconds']/1000

    def sample(self):
        self.sequence += 1
        if not self.owned():
            return Observation('foreign', self.media, self.edition, self.sequence, 0)
        elapsed = self.player.getTime()
        speed = rpc('Player.GetProperties', dict(playerid=0, properties=['speed']))['speed']
        if not self.owned(): return Observation('foreign', self.media, self.edition, self.sequence, 0)
        return Observation(self.session, self.media, self.edition, self.sequence, elapsed, paused=speed == 0)

    def seek(self, seconds):
        if not self.owned(): raise ValueError('native-ownership-lost')
        self.player.seekTime(seconds)
        # Bounded readback settlement, never a repeated seek.
        until = time.monotonic() + 3
        while time.monotonic() < until:
            if not self.owned(): raise ValueError('native-ownership-lost')
            # Decoder preroll can briefly report just before the marker; do not
            # publish the preceding story as successful seek readback.
            if 0 <= self.player.getTime()-seconds <= 2: return
            xbmc.sleep(50)
        raise ValueError('seek-readback-timeout')

    def stop(self):
        if self.stopping or not self.owned(): raise ValueError('native-ownership-lost')
        self.stopping = True
        self.player.stop()

    def idle(self):
        until = time.monotonic() + 8
        while time.monotonic() < until:
            if idle(): return True
            xbmc.sleep(50)
        return False
