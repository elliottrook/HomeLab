import unittest

from seerr_page_model import (PageUnavailable, action_label, complete, load,
                              request, requestable, select, toggle_season)


def raw(kind='movie', media_id=123, **changes):
    value = {'schema': 2, 'identity': f'seerr:{kind}:{media_id}',
             'media_type': kind, 'media_id': media_id, 'title': 'Example',
             'year': '2026', 'overview': 'Synthetic synopsis.',
             'poster': '/p.jpg', 'backdrop': '/b.jpg', 'owned': False,
             'availability': 'unknown', 'request_id': None,
             'request_state': 'none', 'seasons': [1, 2] if kind == 'tv' else []}
    value.update(changes)
    return value


class SeerrPageModelTests(unittest.TestCase):
    def test_results_select_without_stale_seasons(self):
        page = load({'schema': 1, 'query': 'Example',
                     'candidates': [raw('tv'), raw('movie', 456)]}, 'Example')
        page = toggle_season(page, 2)
        self.assertEqual(page.seasons, (2,))
        page = select(page, 1)
        self.assertEqual((page.item.media_type, page.seasons), ('movie', ()))

    def test_movie_and_tv_require_explicit_confirmation(self):
        movie = load({'schema': 1, 'query': 'Example', 'candidates': [raw()]}, 'Example')
        movie, proposal = request(movie)
        self.assertEqual((movie.phase, proposal.state), ('confirm', 'confirm'))
        movie, proposal = request(movie, True)
        self.assertEqual((movie.phase, proposal.payload['media_type']), ('submitting', 'movie'))
        tv = load({'schema': 1, 'query': 'Series', 'candidates': [raw('tv')]}, 'Series')
        with self.assertRaises(PageUnavailable):
            request(tv, True)
        tv = toggle_season(tv, 1)
        tv, proposal = request(tv, True)
        self.assertEqual(proposal.payload['seasons'], [1])

    def test_owned_existing_and_blocklisted_are_non_writes(self):
        for item, expected in ((raw(owned=True, availability='available', request_state='available'),
                                'unavailable'),
                               (raw(request_id=9, request_state='pending'), 'status'),
                               (raw(availability='blocklisted'), 'unavailable')):
            page = load({'schema': 1, 'query': 'Example', 'candidates': [item]}, 'Example')
            page, proposal = request(page, True)
            self.assertEqual((page.phase, proposal.state), (expected, expected))

    def test_action_label_and_seasons_are_truthful_before_press(self):
        partial = load({'schema': 1, 'query': 'Example', 'candidates': [
            raw('tv', owned=True, availability='partial')]}, 'Example')
        self.assertFalse(requestable(partial.item))
        self.assertEqual(action_label(partial), 'Partly in your library')
        with self.assertRaisesRegex(PageUnavailable, 'seerr-season-invalid'):
            toggle_season(partial, 1)
        pending = load({'schema': 1, 'query': 'Example', 'candidates': [
            raw('tv', request_id=9, request_state='pending')]}, 'Example')
        self.assertEqual(action_label(pending), 'View request status')
        fresh = load({'schema': 1, 'query': 'Example', 'candidates': [raw('tv')]},
                     'Example')
        self.assertTrue(requestable(fresh.item))
        self.assertEqual(action_label(fresh), 'Choose seasons')
        fresh = toggle_season(fresh, 1)
        self.assertEqual(action_label(fresh), 'Request selected seasons')

    def test_correlated_result_is_visible_and_mismatch_fails(self):
        page = load({'schema': 1, 'query': 'Example', 'candidates': [raw()]}, 'Example')
        page, _ = request(page, True)
        reply = {'schema': 1, 'candidate_id': 'seerr:movie:123',
                 'request_id': 88, 'state': 'pending', 'duplicate': False}
        page = complete(page, reply)
        self.assertEqual((page.phase, page.outcome['request_id']), ('complete', 88))
        with self.assertRaises(PageUnavailable):
            complete(page, reply)


if __name__ == '__main__':
    unittest.main()
