"""A movie or whole season must hold on any matching playback or download."""

from unittest import TestCase

from video_archiver.retention_queue_live import QueueEvidence
from video_archiver.retention_scope_activity import scope_has_active_work


class ScopeActivityTests(TestCase):
    def test_exact_movie_and_season_activity(self):
        no_movies = QueueEvidence("radarr", frozenset(), 0, True)
        self.assertTrue(scope_has_active_work(
            kind="movie", arr_id=1, jellyfin_item_ids=("film",),
            active_jellyfin_item_ids=frozenset({"film"}), queue=no_movies))
        no_series = QueueEvidence("sonarr", frozenset(), 0, True)
        self.assertTrue(scope_has_active_work(
            kind="season", arr_id=2,
            jellyfin_item_ids=("episode1", "episode2", "season", "series"),
            active_jellyfin_item_ids=frozenset({"episode2"}), queue=no_series))
        self.assertFalse(scope_has_active_work(
            kind="season", arr_id=2,
            jellyfin_item_ids=("episode1", "episode2", "season", "series"),
            active_jellyfin_item_ids=frozenset(), queue=no_series))

    def test_queue_identity_and_kind_mismatch(self):
        unknown = QueueEvidence("sonarr", frozenset(), 1, False)
        self.assertTrue(scope_has_active_work(
            kind="season", arr_id=2, jellyfin_item_ids=("episode1",),
            active_jellyfin_item_ids=frozenset(), queue=unknown))
        with self.assertRaisesRegex(ValueError, "kind"):
            scope_has_active_work(kind="movie", arr_id=2,
                                  jellyfin_item_ids=("film",),
                                  active_jellyfin_item_ids=frozenset(), queue=unknown)
