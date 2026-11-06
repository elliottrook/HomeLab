"""Movie-year preservation must use verified, unique household films."""

from datetime import date
from unittest import TestCase

from video_archiver.retention_years import MovieYearFact, count_verified_movie_years


USERS = frozenset({'a', 'b'})


def film(provider: str, item: str, path: str, year: int = 1939, **changes) -> MovieYearFact:
    values = dict(provider_id=provider, release_year=year, jellyfin_item_id=item,
                  path=path, physical_present=True, arr_identity_verified=True,
                  visible_user_ids=USERS)
    values.update(changes)
    return MovieYearFact(**values)


def inventory(*facts: MovieYearFact, complete=True):
    return count_verified_movie_years(facts, expected_user_ids=USERS,
                                      source_scan_complete=complete, today=date(2026, 11, 6))


class MovieYearTests(TestCase):
    def test_distinct_present_movies_count_across_library_roots(self):
        result = inventory(film('tmdb:1', 'jf-1', '/media/movies/a.mkv'),
                           film('tmdb:2', 'jf-2', '/media/archive-movies/b.mkv'))
        self.assertEqual(result.counts, {1939: 2})
        self.assertEqual(result.held, 0)

    def test_duplicate_provider_or_path_never_inflates_count(self):
        result = inventory(film('tmdb:1', 'jf-1', '/media/movies/a.mkv'),
                           film('tmdb:1', 'jf-2', '/media/archive-movies/a.mkv'),
                           film('tmdb:3', 'jf-3', '/media/movies/c.mkv'),
                           film('tmdb:4', 'jf-4', '/media/movies/c.mkv'))
        self.assertEqual(result.counts, {})
        self.assertEqual(result.held, 4)

    def test_missing_file_identity_year_or_user_visibility_is_held(self):
        result = inventory(
            film('tmdb:1', 'jf-1', '/a', physical_present=False),
            film('tmdb:2', 'jf-2', '/b', arr_identity_verified=False),
            film('tmdb:3', 'jf-3', '/c', release_year=None),
            film('tmdb:4', 'jf-4', '/d', visible_user_ids=frozenset({'a'})),
        )
        self.assertEqual(result.counts, {})

    def test_incomplete_listing_cannot_certify_any_year(self):
        result = inventory(film('tmdb:1', 'jf-1', '/a'), complete=False)
        self.assertEqual(result.counts, {})
        self.assertFalse(result.complete_source_scan)
