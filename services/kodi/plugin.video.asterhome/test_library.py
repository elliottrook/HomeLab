"""Credential-free tests for Aster's combined genre catalogue."""

import unittest

from library import canonical_genre, combined_items, continue_items, matches_genre


class LibraryTests(unittest.TestCase):
    def test_only_known_genres_are_accepted(self):
        self.assertEqual(canonical_genre(' sci-fi '), 'Sci-Fi')
        self.assertIsNone(canonical_genre('../Drama'))
        self.assertIsNone(canonical_genre(''))

    def test_scifi_matches_common_kodi_labels(self):
        self.assertTrue(matches_genre({'genre': ['Sci-Fi & Fantasy']}, 'Sci-Fi'))
        self.assertTrue(matches_genre({'genre': ['Science Fiction']}, 'Sci-Fi'))
        self.assertFalse(matches_genre({'genre': ['Fantasy']}, 'Sci-Fi'))

    def test_movies_and_shows_are_merged_and_sorted(self):
        movies = [
            {'movieid': 2, 'label': 'Zulu', 'genre': ['Action']},
            {'movieid': 1, 'label': 'Bravo', 'genre': ['Comedy']},
        ]
        shows = [
            {'tvshowid': 4, 'label': 'Alpha', 'genre': ['Comedy', 'Drama']},
            {'tvshowid': 3, 'label': 'Skip', 'genre': ['Horror']},
        ]
        rows = combined_items(movies, shows, 'Comedy')
        self.assertEqual([(row['label'], row['kind'], row['id']) for row in rows],
                         [('Alpha', 'tvshow', 4), ('Bravo', 'movie', 1)])
        self.assertNotIn('kind', shows[0])

    def test_malformed_rows_fail_closed(self):
        self.assertEqual(combined_items('bad', [{'label': 'No id', 'genre': ['Drama']}],
                                        'Drama'), [])

    def test_continue_watching_merges_movies_and_episodes_by_last_played(self):
        movies = [{
            'movieid': 9, 'label': 'Movie', 'lastplayed': '2026-10-22 10:00:00',
            'resume': {'position': 300, 'total': 7200},
        }]
        episodes = [{
            'episodeid': 7, 'label': 'Episode', 'showtitle': 'Show',
            'season': 2, 'episode': 4, 'lastplayed': '2026-10-22 11:00:00',
            'resume': {'position': 600, 'total': 2700},
        }]
        rows = continue_items(movies, episodes)
        self.assertEqual([(row['label'], row['kind']) for row in rows],
                         [('Episode', 'episode'), ('Movie', 'movie')])
        self.assertEqual(rows[0]['resume_position'], 600)
        self.assertEqual(rows[0]['resume_total'], 2700)

    def test_continue_watching_rejects_invalid_and_complete_resume_points(self):
        rows = continue_items([
            {'label': 'No resume'},
            {'label': 'Complete', 'resume': {'position': 100, 'total': 100}},
            {'label': 'Bad', 'resume': {'position': 'nope', 'total': 100}},
            {'label': 'Valid', 'resume': {'position': 1, 'total': 100}},
        ], [], limit=1)
        self.assertEqual([row['label'] for row in rows], ['Valid'])


if __name__ == '__main__':
    unittest.main()
