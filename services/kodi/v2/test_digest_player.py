from dataclasses import replace
from datetime import datetime, timezone
import ast
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET
from build_digest_player import build as package
from digest_timeline import build
from digest_player_model import Presentation
from digest_playback_state import View
sys.path.insert(0, str(Path(__file__).parent.parent / 'skin.asterhome/tools'))
from digest_preview_model import load


class DigestPlayerTests(unittest.TestCase):
    def setUp(self):
        now = datetime(2026, 10, 25, 20, tzinfo=timezone.utc)
        self.feed = dict(digest_run='synthetic', generated_at=now.isoformat(), duration_seconds=120,
            story_count=2, chapters=[dict(index=1, title='First', start=10), dict(index=2, title='Second', start=60)])
        self.snapshot = load(lambda path, size:json.dumps(self.feed).encode() if path.endswith('.json') else b'', now)
        self.timeline = build(self.feed, 120.05, now)
        self.model = Presentation(self.snapshot, self.timeline)

    def test_observed_duration_identity_change_maps_exact_stories(self):
        self.assertNotEqual(self.snapshot.identity, self.timeline.identity)
        self.assertEqual(self.model.row(View('opening')), 0)
        self.assertEqual(self.model.row(View('story', 0)), 1)
        self.assertEqual(self.model.row(View('story', 1)), 2)
        self.assertIsNone(self.model.row(View('ended')))
        self.assertIsNone(self.model.row(View('lost')))

    def test_opening_and_no_wrap(self):
        self.assertIsNone(self.model.chapter(0))
        self.assertEqual(self.model.chapter(1), 0)
        self.assertIsNone(self.model.neighbor(0, -1))
        self.assertIsNone(self.model.neighbor(2, 1))
        self.assertEqual(self.model.neighbor(1, -1), 0)
        with self.assertRaises(ValueError): self.model.chapter(True)

    def test_mismatched_stories_refused_not_guessed(self):
        wrong = replace(self.snapshot, entries=(self.snapshot.entries[0], self.snapshot.entries[2], self.snapshot.entries[1]))
        with self.assertRaises(ValueError): Presentation(wrong, self.timeline)
        with self.assertRaises(ValueError): Presentation(replace(self.snapshot, duration=500), self.timeline)

    def test_immutable_player_bundle_and_active_vs_focus(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'player'
            self.assertEqual(len(package(output)), 64)
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertFalse(manifest['normal_news'])
            ast.parse((output/'default.py').read_text())
            root = ET.parse(output/'resources/skins/Default/1080i/DigestPlayer.xml').getroot()
            self.assertEqual(root.findtext(".//control[@id='300']/ondown"), 'noop')
            active = root.findtext(".//control[@id='300']/itemlayout/control/visible")
            self.assertIn('Active', active)
            for identity in ('200', '201', '202', '203', '204', '300'):
                self.assertIsNotNone(root.find(".//control[@id='"+identity+"']"))
            with self.assertRaisesRegex(ValueError, 'immutable'): package(output)

    def stop_method(self, name='stop_owned'):
        tree = ast.parse((Path(__file__).parent/'digest_player/default.py').read_text())
        method = next(node for node in next(node for node in tree.body if isinstance(node, ast.ClassDef)).body
            if isinstance(node, ast.FunctionDef) and node.name == name)
        namespace = dict(idle=lambda:False)
        def require(value, code):
            if not value: raise ValueError(code)
        namespace['require'] = require
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<owned-stop-test>', 'exec'), namespace)
        return namespace[name]

    def test_fenced_seek_allows_one_distinct_owned_exit_stop(self):
        calls = []
        port = types.SimpleNamespace(stopping=False, owned=lambda:True, idle=lambda:True)
        def stop():
            port.stopping = True
            calls.append('stop')
        port.stop = stop
        owner = types.SimpleNamespace(adapter=types.SimpleNamespace(fenced=True), port=port)
        self.assertTrue(self.stop_method()(owner))
        self.assertFalse(self.stop_method()(owner))
        self.assertEqual(calls, ['stop'])

    def test_fenced_foreign_exit_never_stops(self):
        calls = []
        port = types.SimpleNamespace(stopping=False, owned=lambda:False, stop=lambda:calls.append('stop'))
        owner = types.SimpleNamespace(adapter=types.SimpleNamespace(fenced=True), port=port)
        self.assertFalse(self.stop_method()(owner))
        self.assertEqual(calls, [])

    def test_stop_not_reported_when_unconfirmed(self):
        labels = []
        owner = types.SimpleNamespace(stop_owned=lambda:False, setProperty=lambda *args:labels.append(args))
        with self.assertRaisesRegex(ValueError, 'stop-not-confirmed'):
            self.stop_method('process')(owner, '204', None)
        self.assertEqual(labels, [])


if __name__ == '__main__': unittest.main()
