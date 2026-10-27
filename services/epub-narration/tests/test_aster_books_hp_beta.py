from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "kodi"))

from build_aster_books_hp_beta import build
from reader_pages import Reader, paginate, render


class Player:
    def __init__(self):
        self.path = ""
        self.audio = False
        self.clock = 0.0
        self.speed = 1

    def play(self, path):
        self.path = path
        self.audio = True
        self.onAVStarted()

    def isPlayingAudio(self):
        return self.audio

    def getPlayingFile(self):
        return self.path

    def getTime(self):
        return self.clock

    def seekTime(self, value):
        self.clock = value

    def pause(self):
        self.speed = 0 if self.speed else 1

    def stop(self):
        self.audio = False
        self.onPlayBackStopped()


class HpBetaTests(unittest.TestCase):
    def test_bundle_is_repeatable_hp_only_and_direct_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "first", root / "second"
            self.assertEqual(build(first), build(second))
            manifest = json.loads((first / "bundle.json").read_text())
            self.assertTrue(manifest["hp_only"])
            self.assertTrue(manifest["active"])
            self.assertFalse(manifest["normal_entry"])
            self.assertFalse(manifest["network"])
            self.assertFalse(manifest["shared_progress"])
            self.assertNotIn("selection.json", manifest["files"])
            self.assertFalse((first / "selection.json").exists())
            for name, wanted in manifest["files"].items():
                self.assertEqual(wanted, hashlib.sha256((first / name).read_bytes()).hexdigest())
            source = (first / "default.py").read_text()
            self.assertIn("books-idle-home", source)
            self.assertIn("AsterBooksCompiler.Window", source)
            self.assertNotIn("http://", source)
            self.assertNotIn("https://", source)

    def test_exact_sentence_render_escapes_untrusted_markup(self):
        text = "One [unsafe] sentence. Another exact sentence."
        pages = paginate(text)
        rendered = render(text, pages[0], (0, 22))
        self.assertIn("［unsafe］", rendered)
        self.assertIn("[COLOR ffc2a06b]", rendered)
        reader = Reader(text)
        reader.go(25)
        self.assertLessEqual(reader.current.start, 25)

    def test_kodi_port_requires_unique_hash_bound_opus_and_ownership(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "session-test.opus"
            path.write_bytes(b"private-opus-fixture")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            spec = importlib.util.spec_from_file_location("isolated_books_port", ROOT / "kodi" / "kodi_port.py")
            module = importlib.util.module_from_spec(spec)
            fake = types.SimpleNamespace(Player=Player, sleep=lambda milliseconds: None)
            with patch.dict("sys.modules", xbmc=fake):
                spec.loader.exec_module(module)
            port = module.KodiPort(path, digest)
            module.idle = lambda: True
            module._rpc = lambda method, params=None: (
                [{"playerid": 0, "type": "audio"}]
                if method == "Player.GetActivePlayers"
                else {"speed": port.player.speed, "totaltime": {"hours": 0, "minutes": 1, "seconds": 0, "milliseconds": 0}}
            )
            port.open()
            self.assertTrue(port.owned())
            port.seek(12)
            self.assertEqual(port.sample().elapsed, 12)
            ordinary = Path(temporary) / "ordinary.opus"
            ordinary.write_bytes(path.read_bytes())
            with self.assertRaisesRegex(ValueError, "books-unique-session-copy"):
                module.KodiPort(ordinary, digest)
            path.write_bytes(b"changed")
            self.assertFalse(port.owned())


if __name__ == "__main__":
    unittest.main()
