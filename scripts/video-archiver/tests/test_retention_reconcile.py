"""M2 fixture checks for ambiguous path and household watch inputs."""

from unittest import TestCase

from video_archiver.retention_policy import UserWatch
from video_archiver.retention_reconcile import (
    ArrFileFact, CompleteUserView, JellyfinFileFact, PathMap,
    match_files, watch_for_item,
)


MOVIE_MAP = PathMap("/media/movie", "/media")


class FileIdentityTests(TestCase):
    def test_exact_path_and_physical_presence_required(self):
        arr = (ArrFileFact("tmdb:1", 10, "/media/movie/archive-movies/One/movie.mkv"),)
        present = (JellyfinFileFact("jf:1", "/media/archive-movies/One/movie.mkv", True),)
        self.assertEqual(match_files(arr, present, (MOVIE_MAP,))[0].provider_id, "tmdb:1")
        missing = (JellyfinFileFact("jf:1", "/media/archive-movies/One/movie.mkv", False),)
        self.assertIsNotNone(match_files(arr, missing, (MOVIE_MAP,))[0].reason)

    def test_ambiguous_arr_or_duplicate_jellyfin_item_holds(self):
        arr = (
            ArrFileFact("tmdb:1", 10, "/media/movie/archive-movies/One/movie.mkv"),
            ArrFileFact("tmdb:1", 11, "/media/movie/archive-movies/One/movie.mkv"),
        )
        item = JellyfinFileFact("jf:1", "/media/archive-movies/One/movie.mkv", True)
        self.assertIn("ambiguous", match_files(arr, (item,), (MOVIE_MAP,))[0].reason)
        self.assertIn("duplicate Jellyfin", match_files(arr[:1], (item, item), (MOVIE_MAP,))[0].reason)

    def test_prefix_collision_and_path_escape_do_not_match(self):
        self.assertIsNone(MOVIE_MAP.map("/media/movies/archive-movies/One/movie.mkv"))
        self.assertIsNone(MOVIE_MAP.map("/media/movie/../other/movie.mkv"))


class HouseholdViewTests(TestCase):
    def test_all_users_must_have_explicit_complete_item_result(self):
        expected = frozenset({"a", "b"})
        full = (
            CompleteUserView("a", True, {"jf:1": UserWatch("a")}),
            CompleteUserView("b", True, {"jf:1": UserWatch("b", favorite=True)}),
        )
        watch = watch_for_item("jf:1", full, expected)
        self.assertIsNotNone(watch)
        self.assertTrue(any(row.protected for row in watch))
        self.assertIsNone(watch_for_item("jf:other", full, expected))
        self.assertIsNone(watch_for_item("jf:1", full[:1], expected))
        self.assertIsNone(watch_for_item("jf:1", (full[0], CompleteUserView("b", False, full[1].item_watch)), expected))
