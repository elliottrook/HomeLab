from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest
from build_digest_adapter_trial import build as build_trial
from digest_timeline import build
from digest_playback_state import Observation
from digest_player_adapter import Adapter


class Port:
    def __init__(self, edition):
        self.observation = Observation('session', 'media', edition, 0, 10)
        self.actions = []
        self.failure = False
        self.stopped = False
        self.replacement = False
        self.samples = 0

    def sample(self):
        self.samples += 1
        self.observation = replace(self.observation, sequence=self.observation.sequence+1)
        if self.replacement and self.samples == 2:
            self.observation = replace(self.observation, session='foreign')
        return self.observation

    def seek(self, seconds):
        self.actions.append(('seek', seconds))
        if self.failure: raise OSError('uncertain')
        self.observation = replace(self.observation, elapsed=seconds)

    def stop(self):
        self.actions.append(('stop',))
        if self.failure: raise OSError('uncertain')
        self.stopped = True

    def idle(self): return self.stopped


class DigestAdapterTests(unittest.TestCase):
    def setUp(self):
        now = datetime(2026, 10, 25, 20, tzinfo=timezone.utc)
        feed = dict(digest_run='synthetic', generated_at=now.isoformat(), duration_seconds=120,
            story_count=2, chapters=[dict(index=1, title='First', start=10), dict(index=2, title='Second', start=60)])
        timeline = build(feed, 120, now)
        self.port = Port(timeline.identity)
        self.adapter = Adapter(timeline, 'session', 'media', self.port)

    def test_seek_requires_actual_readback(self):
        self.adapter.seek(1)
        self.assertIsNotNone(self.adapter.pending)
        self.assertEqual(self.adapter.poll().chapter, 1)
        self.assertIsNone(self.adapter.pending)
        self.assertEqual(self.port.actions, [('seek', 60)])

    def test_foreign_media_between_check_and_command_is_not_touched(self):
        self.port.replacement = True
        with self.assertRaises(ValueError): self.adapter.seek(1)
        self.assertEqual(self.port.actions, [])
        self.assertTrue(self.adapter.fenced)

    def test_uncertain_seek_is_never_retried(self):
        self.port.failure = True
        with self.assertRaises(OSError): self.adapter.seek(1)
        with self.assertRaises(ValueError): self.adapter.seek(1)
        self.assertFalse(self.adapter.close())
        self.assertEqual(self.port.actions, [('seek', 60)])

    def test_command_ack_without_seek_readback_fences(self):
        self.adapter.seek(1)
        self.port.observation = replace(self.port.observation, elapsed=10)
        self.adapter.poll()
        self.assertTrue(self.adapter.fenced)
        self.assertIsNotNone(self.adapter.pending)

    def test_no_second_seek_until_first_verified(self):
        self.adapter.seek(1)
        with self.assertRaises(ValueError): self.adapter.seek(0)
        self.adapter.poll()
        self.adapter.seek(0)
        self.assertEqual(self.port.actions, [('seek', 60), ('seek', 10)])

    def test_close_stops_once_and_checks_idle(self):
        self.assertTrue(self.adapter.close())
        self.assertFalse(self.adapter.close())
        self.assertEqual(self.port.actions, [('stop',)])

    def test_foreign_player_on_exit_never_stopped(self):
        self.port.replacement = True
        self.assertFalse(self.adapter.close())
        self.assertEqual(self.port.actions, [])

    def test_stop_ack_without_idle_is_not_success(self):
        self.port.idle = lambda:False
        self.assertFalse(self.adapter.close())
        self.assertTrue(self.adapter.fenced)
        self.assertFalse(self.adapter.close())
        self.assertEqual(self.port.actions, [('stop',)])

    def test_uncertain_stop_never_retried(self):
        self.port.failure = True
        with self.assertRaises(OSError): self.adapter.close()
        self.assertFalse(self.adapter.close())
        self.assertEqual(self.port.actions, [('stop',)])

    def test_ended_playback_not_stopped(self):
        self.port.observation = replace(self.port.observation, ended=True)
        self.assertFalse(self.adapter.close())
        self.assertEqual(self.port.actions, [])

    def test_invalid_sample_fences_without_mutation(self):
        self.port.sample = lambda:None
        with self.assertRaises(ValueError): self.adapter.poll()
        self.assertTrue(self.adapter.fenced)
        self.assertEqual(self.port.actions, [])

    def test_native_trial_bundle_is_immutable_and_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'trial'
            self.assertEqual(len(build_trial(output)), 64)
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(len(manifest['files']), 6)
            self.assertEqual(manifest['kind'], 'hp-digest-adapter-trial.v1')
            self.assertNotIn('session-', ' '.join(row['path'] for row in manifest['files']))
            with self.assertRaisesRegex(ValueError, 'immutable'): build_trial(output)


if __name__ == '__main__': unittest.main()
