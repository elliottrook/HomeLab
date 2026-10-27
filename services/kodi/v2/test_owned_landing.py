from datetime import datetime, timezone
import unittest

from owned_landing import (OwnedHeroState, normalize, recently_added,
                           recommendations)


def row(identity, media_type='album', title='Example', added_at=None,
        score=None, reason=''):
    return {
        'identity': identity,
        'media_type': media_type,
        'title': title,
        'detail': 'Owned local title',
        'synopsis': 'A real local-library record.',
        'artwork': 'image://cover',
        'backdrop': 'image://hero',
        'added_at': added_at,
        'recommendation_score': score,
        'recommendation_reason': reason,
    }


class OwnedLandingTests(unittest.TestCase):
    def test_recent_requires_real_dates_and_sorts_newest_first(self):
        items = normalize([
            row('kodi:album-1', title='Older', added_at='2026-01-01T10:00:00Z'),
            row('kodi:album-2', title='Undated'),
            row('kodi:album-3', title='Newest', added_at='2026-10-01T10:00:00-07:00'),
        ], 'music')
        self.assertEqual([item.title for item in recently_added(items)],
                         ['Newest', 'Older'])
        with self.assertRaisesRegex(ValueError, 'added-at'):
            normalize([row('kodi:album-4', added_at='2026-10-01')], 'music')

    def test_recommendations_need_real_signal_and_exclude_recent(self):
        items = normalize([
            row('kodi:album-1', title='Recent signal', added_at='2026-10-01T10:00:00Z',
                score=95, reason='Matches frequently played local genres'),
            row('kodi:album-2', title='Recommended', score=85,
                reason='Matches frequently played local genres'),
            row('kodi:album-3', title='Owned but unsupported'),
        ], 'music')
        recent = recently_added(items, limit=1)
        self.assertEqual([item.title for item in recommendations(items, recent)],
                         ['Recommended'])

    def test_score_without_reason_and_reason_without_score_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'reason'):
            normalize([row('kodi:album-1', score=50)], 'music')
        with self.assertRaisesRegex(ValueError, 'reason'):
            normalize([row('kodi:album-1', reason='Unscored claim')], 'music')

    def test_domain_action_and_identity_are_pinned(self):
        items = normalize([
            row('calibre:42', 'ebook'),
            row('audiobookshelf:abc', 'audiobook'),
            row('audiobookshelf:pod-1', 'podcast'),
        ], 'books')
        self.assertEqual([item.primary_action for item in items],
                         ['read', 'play', 'play'])
        with self.assertRaisesRegex(ValueError, 'identity'):
            normalize([row('openlibrary:/works/OL1W', 'ebook')], 'books')

    def test_duplicate_owned_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            normalize([row('kodi:album-1'), row('kodi:album-1')], 'music')

    def test_idle_rotation_never_steals_focused_tile(self):
        items = normalize([
            row('kodi:album-1', title='One', score=90, reason='Signal one'),
            row('kodi:album-2', title='Two', score=80, reason='Signal two'),
        ], 'music')
        candidates = recommendations(items)
        state = OwnedHeroState(candidates, 0)
        self.assertEqual(state.visible.title, 'One')
        self.assertEqual(state.tick(12).title, 'Two')
        self.assertEqual(state.focus(candidates[0], 13).title, 'One')
        self.assertEqual(state.tick(60).title, 'One')
        self.assertEqual(state.clear_focus(61).title, 'Two')

    def test_invalid_time_movement_is_rejected_under_optimized_python(self):
        items = normalize([row('kodi:album-1', score=90, reason='Signal')], 'music')
        state = OwnedHeroState(recommendations(items), 10)
        with self.assertRaisesRegex(ValueError, 'hero-time'):
            state.tick(9)


if __name__ == '__main__':
    unittest.main()
