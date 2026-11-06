from datetime import datetime, timezone
from unittest import TestCase

from video_archiver.lifecycle_policy import FileAgeSize
from video_archiver.view_plan import ArrSeason, ArrSeries, KodiSeries, plan_tv_views


class TvViewPlanTests(TestCase):
    now = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)
    file = FileAgeSize(datetime(2026, 10, 1, tzinfo=timezone.utc), 1_000_000_000, True)

    def test_legacy_archive_and_new_episode_split_seasons(self):
        old = FileAgeSize(datetime(2026, 10, 1, tzinfo=timezone.utc), 1_000_000_000, True)
        new = FileAgeSize(datetime(2026, 11, 5, tzinfo=timezone.utc), 1_000_000_000)
        arr = (ArrSeries(3, 12345, (
            ArrSeason(0, (old,)), ArrSeason(1, (old,)), ArrSeason(2, (old, new)),
        )),)
        plan = plan_tv_views(arr, (KodiSeries(7, 12345, "Example"),), self.now)
        self.assertFalse(plan.held)
        self.assertEqual([(s.number, s.archive) for s in plan.require_complete()[0].seasons],
                         [(0, True), (1, True), (2, False)])

    def test_oversize_legacy_episode_keeps_season_current(self):
        over = FileAgeSize(datetime(2026, 10, 1, tzinfo=timezone.utc), 5_000_000_001, True)
        plan = plan_tv_views((ArrSeries(3, 12345, (ArrSeason(1, (over,)),)),),
                             (KodiSeries(7, 12345, "Example"),), self.now)
        self.assertFalse(plan.require_complete()[0].seasons[0].archive)

    def test_missing_or_duplicate_provider_identity_blocks_publication(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),)),
               ArrSeries(2, 200, (ArrSeason(1, (self.file,)),)))
        kodi = (KodiSeries(10, 100, "One"), KodiSeries(11, 100, "Duplicate"))
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual({h.arr_id for h in plan.held}, {1, 2})
        with self.assertRaises(ValueError):
            plan.require_complete()

    def test_duplicate_display_title_is_safe_with_kodi_ids(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),)),
               ArrSeries(2, 200, (ArrSeason(1, (self.file,)),)))
        kodi = (KodiSeries(10, 100, "Same"), KodiSeries(11, 200, "same"))
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual({show.kodi_id for show in plan.require_complete()}, {10, 11})

    def test_duplicate_arr_id_and_season_are_held(self):
        arr = (
            ArrSeries(1, 100, (ArrSeason(1, (self.file,)),)),
            ArrSeries(1, 200, (ArrSeason(1, (self.file,)),)),
            ArrSeries(3, 300, (ArrSeason(1, (self.file,)), ArrSeason(1, (self.file,)))),
        )
        kodi = (KodiSeries(10, 100, "One"), KodiSeries(11, 200, "Two"), KodiSeries(12, 300, "Three"))
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual(len(plan.held), 3)

    def test_missing_monitored_series_without_media_does_not_block_view(self):
        plan = plan_tv_views((ArrSeries(5, 500, ()),), (), self.now)
        self.assertEqual(plan.skipped_empty, (5,))
        self.assertEqual(plan.require_complete(), ())

    def test_exact_host_path_resolves_duplicate_tvdb_ids(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),), "/media/archive-tv/one"),)
        kodi = (
            KodiSeries(10, 100, "One", "/media/archive-tv/one"),
            KodiSeries(11, 100, "Other", "/media/media/tv/other"),
        )
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual(plan.require_complete()[0].kodi_id, 10)

    def test_exact_host_path_resolves_missing_kodi_tvdb_id(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),), "/media/archive-tv/one"),)
        kodi = (KodiSeries(10, None, "One", "/media/archive-tv/one"),)
        self.assertEqual(plan_tv_views(arr, kodi, self.now).require_complete()[0].kodi_id, 10)

    def test_conflicting_tvdb_ids_at_same_path_are_held(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),), "/media/archive-tv/one"),)
        kodi = (KodiSeries(10, 200, "One", "/media/archive-tv/one"),)
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual(plan.held[0].reason, "ARR and Kodi TVDB IDs conflict for the same host path")

    def test_same_tvdb_id_with_different_known_paths_is_held(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),), "/media/archive-tv/one"),)
        kodi = (KodiSeries(10, 100, "One", "/media/media/tv/one"),)
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual(plan.held[0].reason, "missing or duplicate Kodi host path")

    def test_duplicate_arr_host_path_is_held(self):
        arr = (
            ArrSeries(1, 100, (ArrSeason(1, (self.file,)),), "/media/one"),
            ArrSeries(2, 200, (ArrSeason(1, (self.file,)),), "/media/one"),
        )
        kodi = (KodiSeries(10, 100, "One", "/media/one"),)
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual({h.reason for h in plan.held}, {"invalid or duplicate ARR host path"})

    def test_duplicate_title_with_unmatched_kodi_show_is_safe(self):
        arr = (ArrSeries(1, 100, (ArrSeason(1, (self.file,)),), "/media/archive-tv/one"),)
        kodi = (
            KodiSeries(10, 100, "Same", "/media/archive-tv/one"),
            KodiSeries(11, 200, "same", "/media/media/tv/other"),
        )
        plan = plan_tv_views(arr, kodi, self.now)
        self.assertEqual(plan.require_complete()[0].kodi_id, 10)
