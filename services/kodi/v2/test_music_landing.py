import unittest

from music_landing import fetch_albums, landing_rows
from owned_landing import normalize, recently_added, recommendations


def album(identity, title, **values):
    row = {'albumid': identity, 'label': title, 'artist': ['Example Artist'],
           'genre': ['Rock'], 'playcount': 0, 'dateadded': '',
           'thumbnail': 'image://cover', 'fanart': 'image://hero'}
    row.update(values)
    return row


class MusicLandingTests(unittest.TestCase):
    def test_complete_paginated_catalogue_is_required(self):
        calls = []
        rows = [album(index, f'Album {index}') for index in range(1, 4)]

        def rpc(method, params):
            calls.append((method, params))
            start, end = params['limits']['start'], params['limits']['end']
            return {'albums': rows[start:end],
                    'limits': {'start': start, 'end': min(end, 3), 'total': 3}}

        self.assertEqual(len(fetch_albums(rpc, page_size=2, maximum=4)), 3)
        self.assertEqual([call[1]['limits'] for call in calls],
                         [{'start': 0, 'end': 2}, {'start': 0, 'end': 3}])

    def test_incomplete_or_changing_pagination_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'pagination'):
            fetch_albums(lambda _method, _params:
                         {'albums': [], 'limits': {'total': 2}},
                         page_size=2, maximum=4)

        totals = iter((3, 4))
        with self.assertRaisesRegex(ValueError, 'page'):
            fetch_albums(lambda _method, params:
                         {'albums': [album(params['limits']['start'] + 1, 'A')],
                          'limits': {'total': next(totals)}},
                         page_size=2, maximum=4)

    def test_one_kodi_inaccessible_sentinel_is_bounded(self):
        rows = [album(1, 'One'), album(2, 'Two')]
        self.assertEqual(fetch_albums(
            lambda _method, params: {
                'albums': rows[params['limits']['start']:params['limits']['end']],
                'limits': {'total': 3}}, page_size=2, maximum=4), rows)

    def test_real_recent_albums_and_affinity_recommendations_are_separate(self):
        rows = landing_rows([
            album(1, 'Played rock', playcount=5, lastplayed='2026-09-01'),
            album(2, 'New rock', dateadded='2026-10-01T00:00:00Z'),
            album(3, 'Rediscover rock'),
            album(4, 'Jazz choice', genre=['Jazz'], userrating=8),
        ], recent_limit=1)
        items = normalize(rows, 'music')
        recent = recently_added(items, limit=1)
        suggested = recommendations(items, recent)
        self.assertEqual([item.title for item in recent], ['New rock'])
        self.assertEqual([item.title for item in suggested],
                         ['Jazz choice', 'Rediscover rock', 'Played rock'])
        self.assertEqual(suggested[1].recommendation_reason,
                         'Because you listen to Rock')

    def test_recommendations_require_art_and_exclude_holiday_tags(self):
        rows = landing_rows([
            album(1, 'Played', playcount=2),
            album(2, 'No art', thumbnail='', fanart=''),
            album(3, 'Seasonal', genre=['Christmas']),
        ])
        suggested = recommendations(normalize(rows, 'music'))
        self.assertEqual([item.title for item in suggested], ['Played'])

    def test_projection_contains_no_file_or_acquisition_identity(self):
        rows = landing_rows([album(7, 'Local', file='/private/music.flac',
                                   musicbrainzreleasegroupid='remote-id')])
        self.assertNotIn('file', rows[0])
        self.assertNotIn('musicbrainzreleasegroupid', rows[0])
        self.assertEqual(rows[0]['identity'], 'kodi:album-7')

    def test_naive_kodi_source_date_requires_explicit_local_offset(self):
        source = album(1, 'Local date', dateadded='2026-10-26 09:30:00')
        with self.assertRaisesRegex(ValueError, 'timezone'):
            landing_rows([source])
        rows = landing_rows([source], source_offset='-07:00')
        self.assertEqual(rows[0]['added_at'], '2026-10-26T09:30:00-07:00')

    def test_invalid_playcount_and_duplicate_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'playcount'):
            landing_rows([album(1, 'Bad', playcount=True)])
        with self.assertRaisesRegex(ValueError, 'album'):
            landing_rows([album(1, 'One'), album(1, 'Again')])


if __name__ == '__main__':
    unittest.main()
