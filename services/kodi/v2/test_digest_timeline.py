from copy import deepcopy
from datetime import datetime, timezone
import unittest
from digest_timeline import build

NOW = datetime(2026, 10, 25, 20, tzinfo=timezone.utc)


class DigestTimelineTests(unittest.TestCase):
    def setUp(self):
        self.feed = dict(digest_run='synthetic', generated_at=NOW.isoformat(), duration_seconds=120,
            story_count=2, chapters=[dict(index=1, title='First story', start=10), dict(index=2, title='Second story', start=60)])
        self.timeline = build(self.feed, 120, NOW)

    def test_source_unchanged_and_identity_stable(self):
        before = deepcopy(self.feed)
        self.assertEqual(self.timeline, build(self.feed, 120, NOW))
        self.assertEqual(before, self.feed)

    def test_opening_is_not_mislabelled_as_first_story(self):
        self.assertIsNone(self.timeline.chapter_at(0, self.timeline.identity))
        self.assertIsNone(self.timeline.chapter_at(9.999, self.timeline.identity))
        self.assertEqual(self.timeline.chapter_at(10, self.timeline.identity), 0)

    def test_exact_boundaries_and_completion(self):
        self.assertEqual(self.timeline.chapter_at(59.999, self.timeline.identity), 0)
        self.assertEqual(self.timeline.chapter_at(60, self.timeline.identity), 1)
        self.assertIsNone(self.timeline.chapter_at(120, self.timeline.identity))

    def test_neighbors_never_wrap(self):
        self.assertIsNone(self.timeline.neighbor(0, -1))
        self.assertEqual(self.timeline.neighbor(0, 1), 1)
        self.assertIsNone(self.timeline.neighbor(1, 1))

    def test_edition_change_invalidates_seek_and_highlight(self):
        with self.assertRaisesRegex(ValueError, 'edition-changed'): self.timeline.chapter_at(20, 'old')
        with self.assertRaisesRegex(ValueError, 'edition-changed'): self.timeline.seek_proposal(0, 'old')

    def test_proposal_has_no_url_or_playback_command(self):
        proposal = self.timeline.seek_proposal(1, self.timeline.identity)
        self.assertEqual(set(proposal), {'edition', 'chapter', 'start'})
        self.assertEqual(proposal['start'], 60)

    def test_voice_regeneration_and_changed_chapters_change_identity(self):
        for field, value in (('generated_at', '2026-10-25T19:59:59+00:00'), ('digest_run', 'other')):
            feed = deepcopy(self.feed)
            feed[field] = value
            self.assertNotEqual(self.timeline.identity, build(feed, 120, NOW).identity)
        self.feed['chapters'][1]['start'] = 61
        self.assertNotEqual(self.timeline.identity, build(self.feed, 120, NOW).identity)

    def test_invalid_order_duplicate_index_out_of_range(self):
        for field, value in (('start', 10), ('start', 121), ('index', 1)):
            feed = deepcopy(self.feed)
            feed['chapters'][1][field] = value
            with self.assertRaises(ValueError): build(feed, 120, NOW)

    def test_duration_mismatch_and_unknown_duration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duration-mismatch'): build(self.feed, 125, NOW)
        with self.assertRaises(ValueError): build(self.feed, 0, NOW)

    def test_timezone_and_staleness(self):
        for stamp in ('2026-10-25T20:00:00', '2026-10-20T20:00:00+00:00', '2026-10-26T20:00:00+00:00'):
            self.feed['generated_at'] = stamp
            with self.assertRaises(ValueError): build(self.feed, 120, NOW)

    def test_no_silent_truncation_or_missing_story(self):
        self.feed['story_count'] = 3
        with self.assertRaisesRegex(ValueError, 'incomplete-edition'): build(self.feed, 120, NOW)

    def test_no_fabricated_outro_chapter(self):
        self.assertEqual(len(self.timeline.chapters), 2)
        self.assertEqual(self.timeline.chapters[-1].end, 120)

    def test_invalid_numbers_rejected(self):
        for value in (True, float('nan'), float('inf'), -1):
            with self.assertRaises(ValueError): self.timeline.chapter_at(value, self.timeline.identity)

    def test_formatting_is_neutralized(self):
        self.feed['chapters'][0]['title'] = '[B]Headline[/B]'
        self.assertNotIn('[', build(self.feed, 120, NOW).chapters[0].title)


if __name__ == '__main__': unittest.main()
