import hashlib
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


class Player:
    def __init__(self): self.path = ''; self.audio = False; self.clock = 15; self.calls = []
    def play(self, path): self.path = path; self.audio = True; self.onAVStarted(); self.calls.append('play')
    def isPlayingAudio(self): return self.audio
    def getPlayingFile(self): return self.path
    def getTime(self): return self.clock
    def seekTime(self, seconds): self.clock = seconds; self.calls.append('seek')
    def stop(self): self.audio = False; self.onPlayBackStopped(); self.calls.append('stop')


class DigestKodiPortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'session-synthetic.mp3'
        self.path.write_bytes(b'synthetic-not-a-real-mp3')
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        spec = importlib.util.spec_from_file_location('isolated_digest_port', Path(__file__).with_name('digest_kodi_port.py'))
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', xbmc=types.SimpleNamespace(Player=Player, sleep=lambda ms:None)):
            spec.loader.exec_module(self.module)
        self.module.idle = lambda:True
        self.port = self.module.KodiPort(self.path, self.digest, 'edition')
        self.module.rpc = lambda method, params=None: ([dict(playerid=0, type='audio')] if method == 'Player.GetActivePlayers'
            else dict(speed=1, totaltime=dict(hours=0, minutes=2, seconds=0, milliseconds=0)))

    def test_single_open_and_exact_file_ownership(self):
        self.assertFalse(self.port.owned())
        self.port.open()
        self.assertTrue(self.port.owned())
        self.assertEqual(self.port.duration(), 120)
        self.assertEqual(self.port.sample().session, self.port.session)
        with self.assertRaises(ValueError): self.port.open()

    def test_same_file_replay_loses_callback_continuity(self):
        self.port.open()
        self.port.player.onAVStarted()
        self.assertFalse(self.port.owned())
        self.assertEqual(self.port.sample().session, 'foreign')
        with self.assertRaises(ValueError): self.port.stop()
        self.assertNotIn('stop', self.port.player.calls)

    def test_changed_file_or_player_never_seeked(self):
        self.port.open()
        self.port.player.path = '/another-file'
        with self.assertRaises(ValueError): self.port.seek(60)
        self.port.player.path = str(self.path)
        self.path.write_bytes(b'changed')
        self.assertFalse(self.port.owned())
        with self.assertRaises(ValueError): self.port.seek(60)
        self.assertNotIn('seek', self.port.player.calls)

    def test_seek_readback_and_stop_once(self):
        self.port.open()
        self.port.seek(60)
        self.assertEqual(self.port.sample().elapsed, 60)
        self.port.stop()
        self.assertTrue(self.port.idle())
        with self.assertRaises(ValueError): self.port.stop()
        self.assertEqual(self.port.player.calls, ['play', 'seek', 'stop'])

    def test_seek_waits_past_decoder_preroll_before_readback(self):
        self.port.open()
        clocks = iter((59.97, 60.02))
        self.port.player.getTime = lambda:next(clocks, 60.03)
        self.port.seek(60)
        self.assertGreaterEqual(self.port.sample().elapsed, 60)
        self.assertEqual(self.port.player.calls.count('seek'), 1)

    def test_non_unique_path_wrong_hash_and_symlink_refused(self):
        with self.assertRaises(ValueError): self.module.KodiPort(self.path, 'wrong', 'edition')
        ordinary = Path(self.temp.name) / 'cached.mp3'
        ordinary.write_bytes(self.path.read_bytes())
        with self.assertRaises(ValueError): self.module.KodiPort(ordinary, self.digest, 'edition')
        link = Path(self.temp.name) / 'session-link.mp3'
        link.symlink_to(self.path)
        with self.assertRaises(ValueError): self.module.KodiPort(link, self.digest, 'edition')

    def test_no_open_over_other_playback(self):
        self.module.idle = lambda:False
        with self.assertRaises(ValueError): self.port.open()
        self.assertEqual(self.port.player.calls, [])

    def test_native_player_type_schema_is_validated(self):
        self.port.open()
        self.module.rpc = lambda *args:[dict(playerid=0, type='audio', playertype='internal')]
        self.assertTrue(self.port.owned())
        self.module.rpc = lambda *args:[dict(playerid=0, type='audio', playertype='external')]
        self.assertFalse(self.port.owned())
        self.module.rpc = lambda *args:[dict(playerid=0, type='audio', unexpected=True)]
        self.assertFalse(self.port.owned())


if __name__ == '__main__': unittest.main()
