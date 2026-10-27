import unittest

from books_landing import landing_rows, recommend_audio


def item(identity, kind='audiobook', authors=None, genres=None, progress=None):
    return {'authority': 'audiobookshelf', 'media_type': kind,
            'authority_id': identity, 'title': identity,
            '_authors': authors or [], '_genres': genres or [],
            '_progress': progress}


class BooksLandingTests(unittest.TestCase):
    def test_real_household_progress_creates_same_kind_affinity(self):
        progress = {'duration': 100, 'currentTime': 40, 'isFinished': False,
                    'hideFromContinueListening': False}
        rows = recommend_audio([
            item('played', authors=[{'name': 'Writer'}], genres=['Mystery'], progress=progress),
            item('author-match', authors=[{'name': 'Writer'}], genres=['Drama']),
            item('genre-match', authors=[{'name': 'Other'}], genres=['Mystery']),
            item('podcast', kind='podcast', genres=['Mystery']),
        ])
        self.assertNotIn('recommendation_score', rows[0])
        self.assertEqual(rows[1]['recommendation_reason'], 'Because you listen to Writer')
        self.assertEqual(rows[2]['recommendation_reason'], 'Because you listen to Mystery')
        self.assertNotIn('recommendation_score', rows[3])
        self.assertTrue(all(not any(key.startswith('_') for key in row) for row in rows))

    def test_finished_and_visible_history_is_a_signal_but_hidden_is_not(self):
        finished = {'duration': 0, 'currentTime': 0, 'isFinished': True,
                    'hideFromContinueListening': False}
        hidden = {'duration': 100, 'currentTime': 50, 'isFinished': False,
                  'hideFromContinueListening': True}
        rows = recommend_audio([
            item('finished', genres=['History'], progress=finished),
            item('hidden', genres=['Fantasy'], progress=hidden),
            item('history', genres=['History']), item('fantasy', genres=['Fantasy'])])
        self.assertIn('recommendation_score', rows[2])
        self.assertNotIn('recommendation_score', rows[3])

    def test_invalid_progress_or_duplicate_identity_fails_closed(self):
        with self.assertRaises(ValueError):
            recommend_audio([item('same'), item('same')])
        with self.assertRaises(ValueError):
            recommend_audio([item('bad', progress={'duration': 10, 'currentTime': 20,
                'isFinished': False, 'hideFromContinueListening': False})])

    def test_owned_projection_never_invents_art_or_reason(self):
        records = [{'kind': 'ebook', 'id': '42', 'title': 'Book',
                    'detail': 'Ebook · Calibre', 'synopsis': 'Synopsis',
                    'added_at': '2026-01-01T00:00:00Z',
                    'recommendation_score': None, 'recommendation_reason': ''}]
        rows = landing_rows(records, lambda _row: None)
        self.assertEqual(rows[0]['identity'], 'calibre:42')
        self.assertEqual(rows[0]['artwork'], '')
        self.assertIsNone(rows[0]['recommendation_score'])


if __name__ == '__main__':
    unittest.main()
