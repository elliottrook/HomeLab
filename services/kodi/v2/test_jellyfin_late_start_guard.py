"""Exercise the actual patched callback with no Kodi/server side effects."""
import ast
from pathlib import Path
import types
import unittest

from jellyfin_late_start_guard import ANCHOR, GUARD, patched_source


def exercise_callback(source, initialized):
    tree = ast.parse(source)
    player = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Player')
    method = next(n for n in player.body if isinstance(n, ast.FunctionDef) and n.name == 'onPlayBackStarted')
    reports = []
    item = dict(Path='synthetic', Id='fixture', MediaSourceId='fixture', PlayMethod='DirectPlay',
                CurrentPosition=0, PlaySessionId='fixture', AudioStreamIndex=0, SubtitleStreamIndex=-1)
    monitor = types.SimpleNamespace(waitForAbort=lambda seconds: True)
    env = dict(xbmc=types.SimpleNamespace(Monitor=lambda: monitor),
               window=lambda *args: [item] if len(args) == 1 else None,
               settings=lambda key: False)
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<actual-callback>', 'exec', optimize=2), env)
    state = types.SimpleNamespace(played={'synthetic': {'stale': True}},
        stop_playback=lambda: None, _reset_state=lambda **kw: None,
        getPlayingFile=lambda: 'synthetic', detect_audio_subs=lambda value: None)
    def setup(file, value):
        if initialized:
            value.update(Volume=50, Paused=False, Muted=False,
                Server=types.SimpleNamespace(jellyfin=types.SimpleNamespace(session_playing=reports.append)))
            state.played[file] = value
    state.set_item = setup
    env['onPlayBackStarted'](state)
    return reports


class LateStartGuardTests(unittest.TestCase):
    def test_refuses_other_source(self):
        with self.assertRaises(ValueError):
            patched_source(b'not the pinned installed addon')

    def test_guard_fails_closed_on_stale_same_file_item(self):
        fixture = 'class Player:\n    def check(self, current_file, item):\n' + ANCHOR + GUARD + '        return "initialized"\n'
        ns = {}
        exec(compile(fixture, '<guard>', 'exec', optimize=2), ns)
        obj = ns['Player']()
        obj.played = {'synthetic': {}}
        obj.set_item = lambda file, item: None
        item = {}
        self.assertIsNone(obj.check('synthetic', item))
        obj.played.clear()
        self.assertIsNone(obj.check('synthetic', item))
        obj.played['synthetic'] = item
        self.assertEqual(obj.check('synthetic', item), 'initialized')

    def test_actual_pinned_source_when_available(self):
        source = Path('/tmp/aster-jellyfin-player-before.py')
        if not source.exists():
            self.skipTest('private installed-source fixture unavailable')
        patched = patched_source(source.read_bytes())
        self.assertEqual(exercise_callback(patched, False), [])
        reports = exercise_callback(patched, True)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]['VolumeLevel'], 50)
        self.assertEqual(reports[0]['ItemId'], 'fixture')
