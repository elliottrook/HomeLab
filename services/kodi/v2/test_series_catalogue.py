import unittest

from series_catalogue import (merge_page, parse_catalogue, parse_season,
                              season_proposal, season_result)
from series_model import build_series
from test_series_model import episode


def catalogue():
    return {'schema': 1, 'candidate_id': 'seerr:tv:456', 'title': 'Series',
            'seasons': [
                {'number': 1, 'name': 'Season 1', 'episode_count': 2,
                 'state': 'partial', 'request_id': None,
                 'request_state': 'none', 'requestable': False},
                {'number': 2, 'name': 'Season 2', 'episode_count': 1,
                 'state': 'unknown', 'request_id': None,
                 'request_state': 'none', 'requestable': True}]}


def season(number, rows):
    summary = catalogue()['seasons'][number-1]
    return {'schema': 1, 'candidate_id': 'seerr:tv:456', 'title': 'Series',
            'season': summary, 'episodes': rows}


class SeriesCatalogueTests(unittest.TestCase):
    def test_local_episode_wins_and_missing_never_becomes_playable(self):
        page = build_series(12, [episode()], expected_total=1)
        cat = parse_catalogue(catalogue())
        detail = parse_season(season(1, [
            {'number': 1, 'title': 'Remote one', 'overview': '',
             'air_date': '2024-01-01', 'still': 'https://image.tmdb.org/t/p/w500/one.jpg'},
            {'number': 2, 'title': 'Missing two', 'overview': 'Remote synopsis',
             'air_date': '2024-01-08', 'still': 'https://image.tmdb.org/t/p/original/two.jpg'}]), cat, 1)
        merged = merge_page(page, cat, [detail])
        first, missing = merged.seasons[0].episodes
        self.assertEqual(first.episode_id, 1)
        self.assertFalse(first.catalogue)
        self.assertIsNone(missing.episode_id)
        self.assertTrue(missing.catalogue)
        self.assertFalse(missing.available)
        self.assertEqual(missing.selection_key, ('catalogue', 1, 2))

    def test_missing_season_is_visible_and_requestable_after_load(self):
        page = build_series(12, [episode()], expected_total=1)
        cat = parse_catalogue(catalogue())
        unloaded = merge_page(page, cat)
        self.assertEqual([row.number for row in unloaded.seasons], [1, 2])
        self.assertEqual(unloaded.seasons[1].episodes, ())
        detail = parse_season(season(2, [{
            'number': 1, 'title': 'New season', 'overview': '',
            'air_date': '2026-01-01', 'still': ''}]), cat, 2)
        loaded = merge_page(page, cat, [detail])
        row = loaded.seasons[1].episodes[0]
        self.assertTrue(row.requestable)
        self.assertEqual(row.request_state, 'none')

    def test_malformed_contract_fails_closed(self):
        value = catalogue(); value['seasons'][0]['extra'] = True
        with self.assertRaises(ValueError):
            parse_catalogue(value)

    def test_request_contract_is_exact_and_two_step(self):
        cat = parse_catalogue(catalogue())
        self.assertIsNone(season_proposal(cat, 2))
        payload = season_proposal(cat, 2, True)
        self.assertEqual(payload['season'], 2)
        result = {'schema': 1, 'candidate_id': 'seerr:tv:456', 'season': 2,
                  'request_id': 8, 'state': 'pending', 'duplicate': False}
        self.assertEqual(season_result(result, cat, 2), result)
        with self.assertRaises(ValueError):
            season_proposal(cat, 1, True)


if __name__ == '__main__':
    unittest.main()
