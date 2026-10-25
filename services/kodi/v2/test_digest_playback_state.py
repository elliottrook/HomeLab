from datetime import datetime, timezone
from dataclasses import replace
import unittest
from digest_timeline import build, build_preview
from digest_playback_state import Observation, PlaybackState

NOW = datetime(2026, 10, 25, 20, tzinfo=timezone.utc)


class DigestPlaybackStateTests(unittest.TestCase):
    def setUp(self):
        self.feed = dict(digest_run='synthetic', generated_at=NOW.isoformat(), duration_seconds=120,
            story_count=2, chapters=[dict(index=1, title='First', start=10), dict(index=2, title='Second', start=60)])
        self.timeline = build(self.feed, 120, NOW)
        self.state = PlaybackState(self.timeline, 'session-1', 'media-fingerprint')
        self.observation = Observation('session-1', 'media-fingerprint', self.timeline.identity, 0, 0)

    def at(self, sequence, elapsed, **changes):
        return replace(self.observation, sequence=sequence, elapsed=elapsed, **changes)

    def test_requires_verified_media_not_preview_duration(self):
        with self.assertRaisesRegex(ValueError, 'verified-timeline'):
            PlaybackState(build_preview(self.feed, NOW), 'session-1', 'media-fingerprint')

    def test_opening_story_boundaries_and_completion(self):
        for seq, elapsed, phase, chapter in ((0, 0, 'opening', None), (1, 9.9, 'opening', None),
                (2, 10, 'story', 0), (3, 59.9, 'story', 0), (4, 60, 'story', 1), (5, 120, 'ended', None)):
            view = self.state.observe(self.at(seq, elapsed))
            self.assertEqual((view.phase, view.chapter), (phase, chapter))

    def test_pause_and_backwards_seek_follow_observation(self):
        self.state.observe(self.at(0, 70))
        view = self.state.observe(self.at(1, 15, paused=True))
        self.assertEqual((view.chapter, view.elapsed, view.paused), (0, 15, True))

    def test_late_callback_does_not_rewind_highlight(self):
        view = self.state.observe(self.at(2, 70))
        self.assertEqual(self.state.observe(self.at(1, 15)), view)

    def test_replacement_relinquishes_ownership_permanently(self):
        for field in ('session', 'media', 'edition'):
            state = PlaybackState(self.timeline, 'session-1', 'media-fingerprint')
            state.observe(self.at(0, 15))
            self.assertEqual(state.observe(self.at(1, 70, **{field:'other'})).phase, 'lost')
            self.assertEqual(state.observe(self.at(2, 70)).phase, 'lost')
            self.assertIsNone(state.close(self.at(3, 70)))

    def test_seek_proposal_is_fenced_by_latest_observation(self):
        observation = self.at(0, 15)
        self.state.observe(observation)
        intent = self.state.seek(1)
        self.assertEqual(intent.start, 60)
        self.assertTrue(self.state.current(intent, observation))
        self.assertFalse(self.state.current(intent, replace(observation, media='other')))
        self.assertFalse(self.state.current(intent, replace(observation, ended=True)))
        self.state.observe(self.at(1, 20))
        self.assertFalse(self.state.current(intent, self.at(1, 20)))

    def test_no_seek_before_start_after_end_or_invalid_index(self):
        with self.assertRaises(ValueError): self.state.seek(0)
        self.state.observe(self.at(0, 15))
        for chapter in (True, -1, 2):
            with self.assertRaises(ValueError): self.state.seek(chapter)
        self.state.observe(self.at(1, 120))
        with self.assertRaises(ValueError): self.state.seek(0)

    def test_close_proposes_stop_once_and_never_stops_foreign_media(self):
        self.state.observe(self.at(0, 20))
        intent = self.state.close(self.at(1, 25))
        self.assertEqual((intent.kind, intent.session, intent.media), ('stop', 'session-1', 'media-fingerprint'))
        self.assertIsNone(self.state.close(self.at(2, 25)))
        foreign = PlaybackState(self.timeline, 'session-1', 'media-fingerprint')
        foreign.observe(self.at(0, 20))
        self.assertIsNone(foreign.close(self.at(1, 25, session='foreign')))

    def test_stale_exit_observation_never_proposes_stop(self):
        self.state.observe(self.at(2, 25))
        self.assertIsNone(self.state.close(self.at(1, 20)))

    def test_natural_end_does_not_propose_stop_or_reopen(self):
        self.state.observe(self.at(0, 100, ended=True))
        self.assertEqual(self.state.observe(self.at(1, 1)).phase, 'ended')
        self.assertIsNone(self.state.close(self.at(2, 1)))

    def test_invalid_observations_do_not_advance_authority(self):
        self.state.observe(self.at(0, 15))
        for changes in (dict(elapsed=True), dict(elapsed=float('nan')), dict(elapsed=123),
                dict(paused=1), dict(ended=1), dict(sequence=True)):
            observation = replace(self.at(1, 20), **changes)
            with self.assertRaises(ValueError): self.state.observe(observation)
            self.assertEqual(self.state.sequence, 0)

    def test_no_raw_urls_as_binding_identity(self):
        with self.assertRaises(ValueError): PlaybackState(self.timeline, 'session', 'http://private/audio')


if __name__ == '__main__': unittest.main()
