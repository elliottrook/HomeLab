"""Credential-free tests for Aster's combined genre catalogue."""

import unittest

from library import (canonical_genre, combined_items, continue_items, matches_genre,
                     next_up_item, recent_items, recommended_items, watching_items)


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

    def test_recent_movies_and_series_share_one_date_ordered_rail(self):
        movies = [
            {'movieid': 1, 'label': 'Older movie',
             'dateadded': '2026-10-20 10:00:00'},
            {'movieid': 2, 'label': 'Newest movie',
             'dateadded': '2026-10-22 10:00:00'},
        ]
        shows = [{'tvshowid': 7, 'label': 'New series',
                  'dateadded': '2026-10-21 10:00:00'}]
        rows = recent_items(movies, shows, limit=2)
        self.assertEqual([(row['label'], row['kind']) for row in rows],
                         [('Newest movie', 'movie'), ('New series', 'tvshow')])
        self.assertNotIn('kind', shows[0])

    def test_recent_items_require_a_real_identity_and_added_date(self):
        self.assertEqual(recent_items(
            [{'movieid': True, 'label': 'Boolean id', 'dateadded': '2026-10-20'},
             {'movieid': 1, 'label': 'No date'}],
            [{'tvshowid': 2, 'label': 'Valid', 'dateadded': '2026-10-21'}]),
            [{'tvshowid': 2, 'label': 'Valid', 'dateadded': '2026-10-21',
              'kind': 'tvshow', 'id': 2}])

    def test_recommendations_are_owned_local_and_preference_ranked(self):
        movies = [
            {'movieid': 1, 'label': 'Watched Comedy', 'genre': ['Comedy'],
             'playcount': 1, 'file': '/owned/one.mkv', 'dateadded': '2026-01-01',
             'art': {'fanart': 'one.jpg'}},
            {'movieid': 2, 'label': 'Comedy Candidate', 'genre': ['Comedy'],
             'playcount': 0, 'file': '/owned/two.mkv', 'dateadded': '2026-01-02',
             'rating': 7, 'art': {'fanart': 'two.jpg'}},
            {'movieid': 3, 'label': 'Drama Candidate', 'genre': ['Drama'],
             'playcount': 0, 'file': '/owned/three.mkv', 'dateadded': '2026-01-03',
             'rating': 10, 'art': {'fanart': 'three.jpg'}},
        ]
        rows = recommended_items(movies, [], recent_exclusion=0)
        self.assertEqual([row['label'] for row in rows],
                         ['Comedy Candidate', 'Drama Candidate'])
        self.assertTrue(all(row['file'].startswith('/owned/') for row in rows))

    def test_recommendations_exclude_recent_watched_unavailable_and_artless(self):
        movies = [
            {'movieid': 1, 'label': 'Newest', 'dateadded': '2026-10-02',
             'file': '/owned/new.mkv', 'art': {'fanart': 'new.jpg'}},
            {'movieid': 2, 'label': 'No file', 'dateadded': '2026-09-01',
             'file': '', 'art': {'fanart': 'missing.jpg'}},
            {'movieid': 3, 'label': 'Watched', 'dateadded': '2026-08-01',
             'file': '/owned/watched.mkv', 'playcount': 1,
             'art': {'fanart': 'watched.jpg'}},
            {'movieid': 4, 'label': 'No art', 'dateadded': '2026-07-01',
             'file': '/owned/no-art.mkv'},
            {'movieid': 5, 'label': 'Eligible', 'dateadded': '2026-06-01',
             'file': '/owned/eligible.mkv', 'art': {'fanart': 'eligible.jpg'}},
        ]
        shows = [
            {'tvshowid': 8, 'label': 'Caught Up', 'unwatchedepisodes': 0,
             'art': {'fanart': 'caught-up.jpg'}},
            {'tvshowid': 9, 'label': 'Series', 'unwatchedepisodes': 2,
             'art': {'fanart': 'series.jpg'}},
        ]
        rows = recommended_items(movies, shows, recent_exclusion=1)
        self.assertEqual({row['label'] for row in rows}, {'Eligible', 'Series'})
        self.assertTrue(all(row['kind'] in ('movie', 'tvshow') for row in rows))

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

    def episode(self, season, episode, watched=0, **extra):
        return dict(tvshowid=1, episodeid=season*100+episode, season=season,
                    episode=episode, playcount=watched, file='plugin://play',
                    showtitle='Series', lastplayed='2026-10-23' if watched else '',
                    **extra)

    def test_next_episode_advances_seasons_and_ignores_specials(self):
        show = {'tvshowid': 1, 'label': 'Series'}
        episodes = [self.episode(0, 99, 1), self.episode(1, 2, 1),
                    self.episode(1, 1), self.episode(2, 1), self.episode(2, 2)]
        row = next_up_item(show, episodes)
        self.assertEqual((row['season'], row['episode']), (2, 1))
        self.assertTrue(row['next_up'])
        self.assertIn('Up next', row['label'])
        self.assertNotIn('kind', episodes[3])

    def test_unstarted_series_is_not_promoted_to_up_next(self):
        self.assertIsNone(next_up_item({'tvshowid': 1}, [self.episode(1, 1)]))

    def test_caught_up_series_is_absent_until_an_episode_arrives(self):
        row = next_up_item({'tvshowid': 1, 'label': 'Series'},
                           [self.episode(1, 1, 1)])
        self.assertIsNone(row)

    def test_future_episode_does_not_create_a_placeholder(self):
        row = next_up_item({'tvshowid': 1, 'label': 'Series'},
                           [self.episode(1, 1, 1),
                            self.episode(1, 2, firstaired='2026-11-01')],
                           today='2026-10-23')
        self.assertIsNone(row)

    def test_missing_file_does_not_skip_to_a_later_playable_episode(self):
        missing = self.episode(1, 2)
        missing['file'] = ''
        row = next_up_item({'tvshowid': 1, 'label': 'Series'},
                           [self.episode(1, 1, 1), missing, self.episode(1, 3)])
        self.assertIsNone(row)

    def test_mobland_episode_seven_appears_only_when_available(self):
        from copy import deepcopy
        show = {'tvshowid': 1, 'label': 'MobLand'}
        rows = [self.episode(1, 6, 1)]
        original = deepcopy(rows)
        self.assertIsNone(next_up_item(show, rows))
        self.assertEqual(rows, original)
        rows.append(self.episode(1, 7, firstaired='2026-10-30'))
        self.assertIsNone(next_up_item(show, rows, today='2026-10-23'))
        result = next_up_item(show, rows, today='2026-10-30')
        self.assertEqual((result['season'], result['episode']), (1, 7))

    def test_morning_show_returns_only_when_next_season_exists(self):
        show = {'tvshowid': 1, 'label': 'The Morning Show'}
        rows = [self.episode(4, 10, 1)]
        self.assertIsNone(next_up_item(show, rows))
        rows.append(self.episode(5, 1))
        result = next_up_item(show, rows)
        self.assertEqual((result['season'], result['episode']), (5, 1))

    def test_missing_numbered_episode_or_season_does_not_jump_a_gap(self):
        show = {'tvshowid': 1}
        self.assertIsNone(next_up_item(show, [self.episode(1, 6, 1), self.episode(1, 8)]))
        self.assertIsNone(next_up_item(show, [self.episode(1, 6, 1), self.episode(3, 1)]))

    def test_unavailable_series_disappears_without_losing_movie_resume(self):
        movie = {'label': 'Movie', 'resume': {'position': 100, 'total': 1000}}
        result = watching_items([movie], [], [{'tvshowid': 1}],
                                {1: [self.episode(4, 10, 1)]})
        self.assertEqual([row['label'] for row in result], ['Movie'])

    def test_resuming_series_has_priority_over_its_next_episode(self):
        episode = self.episode(1, 2, resume={'position': 100, 'total': 1000})
        rows = watching_items([], [episode], [{'tvshowid': 1}],
                              {1: [self.episode(1, 1, 1), episode]})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['resume_position'], 100)
        self.assertNotIn('next_up', rows[0])

    def test_failed_or_truncated_series_read_does_not_claim_caught_up(self):
        self.assertEqual(watching_items([], [], [{'tvshowid': 1}], {}), [])

    def test_recent_playback_orders_resume_and_up_next_and_deduplicates(self):
        show = {'tvshowid': 1, 'label': 'Series'}
        movie = {'label': 'Movie', 'lastplayed': '2026-10-22',
                 'resume': {'position': 200, 'total': 1000}}
        rows = watching_items([movie], [], [show, show],
                              {1: [self.episode(1, 1, 1), self.episode(1, 2)]})
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]['next_up'])
        self.assertEqual(rows[1]['label'], 'Movie')

    def test_nonfinite_resume_points_are_not_in_progress(self):
        self.assertEqual(continue_items([
            {'resume': {'position': float('nan'), 'total': 10}},
            {'resume': {'position': 1, 'total': float('inf')}},
        ], []), [])


if __name__ == '__main__':
    unittest.main()
