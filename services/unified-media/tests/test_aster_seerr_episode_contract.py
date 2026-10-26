import unittest

from aster_seerr_episode_contract import (ContractError, catalogue, season,
                                           season_proposal,
                                           season_request_result)


def detail():
    return {
        'id': 123, 'name': 'Example',
        'seasons': [
            {'seasonNumber': 0, 'name': 'Specials', 'episodeCount': 1},
            {'seasonNumber': 1, 'name': 'Season 1', 'episodeCount': 2},
            {'seasonNumber': 2, 'name': 'Season 2', 'episodeCount': 1},
        ],
        'mediaInfo': {
            'seasons': [
                {'seasonNumber': 1, 'status': 5},
                {'seasonNumber': 2, 'status': 1},
            ],
            'requests': [{'id': 8, 'status': 3,
                          'seasons': [{'seasonNumber': 2}]}],
        },
    }


def season_detail():
    return {'seasonNumber': 2, 'episodes': [
        {'id': 9, 'name': 'Two', 'airDate': '2026-02-02',
         'episodeNumber': 2, 'seasonNumber': 2,
         'stillPath': 'https://image.tmdb.org/t/p/original//two.jpg',
         'overview': 'Second.'},
        {'id': 8, 'name': 'One', 'airDate': '2026-02-01',
         'episodeNumber': 1, 'seasonNumber': 2,
         'stillPath': 'https://image.tmdb.org/t/p/original/one.jpg',
         'overview': 'First.'},
    ]}


class AsterSeerrEpisodeContractTests(unittest.TestCase):
    def test_catalogue_exposes_only_sanitized_season_state(self):
        value = catalogue(123, detail())
        self.assertEqual(value['candidate_id'], 'seerr:tv:123')
        self.assertEqual([row['number'] for row in value['seasons']], [0, 1, 2])
        self.assertEqual(value['seasons'][1]['state'], 'available')
        self.assertFalse(value['seasons'][1]['requestable'])
        self.assertEqual(value['seasons'][2]['request_state'], 'declined')
        self.assertTrue(value['seasons'][2]['requestable'])
        self.assertFalse(value['seasons'][0]['requestable'])

    def test_season_is_sorted_bounded_and_contains_no_upstream_identity(self):
        value = season(123, 2, detail(), season_detail())
        self.assertEqual([row['number'] for row in value['episodes']], [1, 2])
        self.assertEqual(value['episodes'][0]['title'], 'One')
        self.assertNotIn('id', value['episodes'][0])
        self.assertNotIn('mediaInfo', str(value))

    def test_malformed_or_cross_season_data_fails_closed(self):
        for changed in (
                {'seasonNumber': 3, 'episodes': []},
                {'seasonNumber': 2, 'episodes': [dict(
                    season_detail()['episodes'][0], seasonNumber=1)]},
                {'seasonNumber': 2, 'episodes': [dict(
                    season_detail()['episodes'][0], stillPath='http://evil/x')]},
                {'seasonNumber': 2, 'episodes': season_detail()['episodes'] * 2}):
            with self.assertRaises(ContractError):
                season(123, 2, detail(), changed)

    def test_season_request_is_exact_confirmed_and_scoped(self):
        value = {'schema': 1, 'action': 'request-season',
                 'authority': 'seerr', 'candidate_id': 'seerr:tv:123',
                 'media_id': 123, 'season': 2, 'confirmed': True}
        self.assertEqual(season_proposal(value), value)
        for update in ({'confirmed': False}, {'season': 0},
                       {'candidate_id': 'seerr:tv:124'}, {'extra': True}):
            changed = dict(value); changed.update(update)
            with self.assertRaises(ContractError):
                season_proposal(changed)
        self.assertEqual(
            season_request_result({'id': 88, 'status': 1}, 'seerr:tv:123', 2,
                                  duplicate=False),
            {'schema': 1, 'candidate_id': 'seerr:tv:123', 'season': 2,
             'request_id': 88, 'state': 'pending', 'duplicate': False})


if __name__ == '__main__':
    unittest.main()
