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
        self.natural = False
        self.events = []

    def onAVStarted(self):
        self.starts += 1
        self.events.append('start')
    def onPlayBackStopped(self):
        self.finished = True
        self.events.append('stop')
    def onPlayBackEnded(self):
        self.natural = True
        self.finished = True
        self.events.append('end')


def rpc(method, params=None):
    if method not in ('Player.GetActivePlayers', 'Player.GetProperties', 'Playlist.GetItems'):
        raise ValueError('read-only-rpc')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    if 'error' in reply: raise ValueError('native-read-failed')
    return reply['result']


def queue_state():
    snapshots = []
    for playlist_id in (0, 1):
        result = rpc('Playlist.GetItems', dict(playlistid=playlist_id,
            properties=['file'], limits=dict(start=0, end=1000)))
        total = result['limits']['total']
        if total > 1000 or len(result['items']) != total:
            raise ValueError('bounded-playlist-snapshot-required')
        snapshots.append((total, tuple(item.get('file', '') for item in result['items'])))
    return tuple(snapshots)


def idle():
    # Kodi normally retains the last played item in a playlist after playback
    # stops. Readiness means no active player; queue preservation is enforced
    # independently by KodiPort.queue_snapshot.
    return not rpc('Player.GetActivePlayers')


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
        self.observed_duration = 0
        self.last_target = 0
        self.queue_before = None
        self.queue_snapshot = None

    def elapsed(self):
        value = self.player.getTime()
        # Kodi's decoder can report a small negative preroll at the opening.
        # Normalize only there, never invalid clocks at arbitrary story seeks.
        return 0 if self.last_target == 0 and -.25 <= value < 0 else value

    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.queue_before = queue_state()
        self.queue_snapshot = None
        self.opened = True
        self.player.play(str(self.path))

    def queue_unchanged(self):
        current = queue_state()
        if self.queue_snapshot is not None:
            return current == self.queue_snapshot
        if self.queue_before is None or current[1] != self.queue_before[1]:
            return False
        own_audio = (1, (str(self.path),))
        if current[0] not in (self.queue_before[0], own_audio):
            return False
        self.queue_snapshot = current
        return True

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
                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature
                and self.queue_unchanged())
        except (OSError, RuntimeError, ValueError): return False

    def duration(self):
        if not self.owned(): raise ValueError('native-ownership-lost')
        row = rpc('Player.GetProperties', dict(playerid=0, properties=['totaltime']))['totaltime']
        self.observed_duration = ((row['hours']*60+row['minutes'])*60+row['seconds']) + row['milliseconds']/1000
        return self.observed_duration

    def lost_or_ended(self):
        # Native flags, active-player list and Python callbacks can settle in
        # either order at EOF. Require the real end callback AND no player;
        # an explicit stop, second start or foreign player never counts as EOF.
        deadline = time.monotonic()+.75
        while self.player.starts == 1 and not self.stopping and time.monotonic() < deadline:
            active = rpc('Player.GetActivePlayers')
            if self.player.natural and not active:
                return Observation(self.session, self.media, self.edition, self.sequence, self.observed_duration, ended=True)
            if self.player.finished and not self.player.natural: break
            if self.player.isPlayingAudio():
                try:
                    if self.player.getPlayingFile() != str(self.path): break
                except RuntimeError: pass
            if any(row.get('type') != 'audio' for row in active): break
            xbmc.sleep(25)
        return Observation('foreign', self.media, self.edition, self.sequence, 0)

    def sample(self):
        self.sequence += 1
        if not self.owned():
            return self.lost_or_ended()
        elapsed = self.elapsed()
        speed = rpc('Player.GetProperties', dict(playerid=0, properties=['speed']))['speed']
        if not self.owned(): return self.lost_or_ended()
        return Observation(self.session, self.media, self.edition, self.sequence, elapsed, paused=speed == 0)

    def seek(self, seconds):
        if not self.owned(): raise ValueError('native-ownership-lost')
        self.last_target = seconds
        self.player.seekTime(seconds)
        # Bounded readback settlement, never a repeated seek.
        until = time.monotonic() + 3
        while time.monotonic() < until:
            if not self.owned(): raise ValueError('native-ownership-lost')
            # Decoder preroll can briefly report just before the marker; do not
            # publish the preceding story as successful seek readback.
            if 0 <= self.elapsed()-seconds <= 2: return
            xbmc.sleep(50)
        raise ValueError('seek-readback-timeout')

    def stop(self):
        if self.stopping or not self.owned(): raise ValueError('native-ownership-lost')
        self.stopping = True
        self.player.stop()

    def set_paused(self, value):
        if type(value) is not bool or not self.owned(): raise ValueError('native-ownership-lost')
        current = rpc('Player.GetProperties', dict(playerid=0, properties=['speed']))['speed'] == 0
        if current != value:
            if not self.owned(): raise ValueError('native-ownership-lost')
            self.player.pause()
        end = time.monotonic()+3
        last_clock = None
        stable_since = None
        while time.monotonic() < end:
            if not self.owned(): raise ValueError('native-ownership-lost')
            if (rpc('Player.GetProperties', dict(playerid=0, properties=['speed']))['speed'] == 0) == value:
                if not value: return
                elapsed = self.player.getTime()
                if last_clock is None or abs(elapsed-last_clock) > .03:
                    last_clock, stable_since = elapsed, time.monotonic()
                elif time.monotonic()-stable_since >= .25: return
            xbmc.sleep(50)
        raise ValueError('pause-readback-timeout')

    def idle(self):
        until = time.monotonic() + 8
        while time.monotonic() < until:
            if idle(): return True
            xbmc.sleep(50)
        return False
