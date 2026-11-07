import importlib.util
from pathlib import Path
import unittest


PATH = Path(__file__).parent / "addon/service.asterremote/content_session.py"
SPEC = importlib.util.spec_from_file_location("content_session", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ContentSessionTests(unittest.TestCase):
    def test_identity_rotates_only_at_new_playback_start(self):
        tokens = iter(("a" * 32, "b" * 32, "c" * 32))
        session = MODULE.ContentSession(lambda: next(tokens))
        idle = session.observe("idle")
        playing = session.observe("playing")
        paused = session.observe("paused")
        resumed = session.observe("playing")
        stopped = session.observe("idle")
        next_play = session.observe("playing")
        self.assertEqual(idle, ("play-" + "a" * 32, 1))
        self.assertEqual(playing, ("play-" + "b" * 32, 1))
        self.assertEqual(paused, (playing[0], 2))
        self.assertEqual(resumed, (playing[0], 3))
        self.assertEqual(stopped, (playing[0], 4))
        self.assertEqual(next_play, ("play-" + "c" * 32, 1))

    def test_invalid_state_fails_closed(self):
        session = MODULE.ContentSession(lambda: "a" * 32)
        with self.assertRaisesRegex(ValueError, "playback-state"):
            session.observe("buffering")


if __name__ == "__main__":
    unittest.main()
