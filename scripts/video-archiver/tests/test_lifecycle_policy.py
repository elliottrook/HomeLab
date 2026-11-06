from datetime import datetime, timezone
from unittest import TestCase
from zoneinfo import ZoneInfo

from video_archiver.lifecycle_policy import (
    FileAgeSize,
    age_size_eligibility,
    calendar_months_before,
)


class CalendarAgeTests(TestCase):
    def test_four_calendar_months_not_120_days(self):
        now = datetime(2026, 11, 6, 9, 0, tzinfo=ZoneInfo("America/Vancouver"))
        self.assertEqual(
            calendar_months_before(now, 4),
            datetime(2026, 7, 6, 9, 0, tzinfo=ZoneInfo("America/Vancouver")),
        )

    def test_month_end_clamps(self):
        now = datetime(2027, 3, 31, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(calendar_months_before(now, 4), datetime(2026, 11, 30, 12, 0, tzinfo=timezone.utc))


class ArchiveEligibilityTests(TestCase):
    now = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)

    def record(self, month, day, size=5_000_000_000):
        return FileAgeSize(datetime(2026, month, day, 9, 0, tzinfo=timezone.utc), size)

    def test_exact_age_and_size_ceiling_pass(self):
        self.assertTrue(age_size_eligibility([self.record(7, 6)], self.now).eligible)

    def test_one_byte_over_ceiling_keeps_movie_current(self):
        result = age_size_eligibility([self.record(7, 6, 5_000_000_001)], self.now)
        self.assertFalse(result.eligible)
        self.assertIn("ceiling", result.reason)

    def test_new_episode_resets_only_its_season(self):
        older = [self.record(3, 1), self.record(7, 5)]
        newer = [self.record(3, 1), self.record(8, 1)]
        self.assertTrue(age_size_eligibility(older, self.now).eligible)
        self.assertFalse(age_size_eligibility(newer, self.now).eligible)

    def test_oversize_episode_keeps_whole_season_current(self):
        result = age_size_eligibility([self.record(3, 1), self.record(4, 1, 5_000_000_001)], self.now)
        self.assertFalse(result.eligible)

    def test_legacy_archive_survives_arr_migration_date(self):
        legacy = FileAgeSize(datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc), 1_000_000_000, True)
        self.assertTrue(age_size_eligibility([legacy], self.now).eligible)

    def test_new_episode_resets_grandfathered_season(self):
        legacy = FileAgeSize(datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc), 1_000_000_000, True)
        new = self.record(11, 1)
        self.assertFalse(age_size_eligibility([legacy, new], self.now).eligible)

    def test_grandfathered_oversize_file_stays_current(self):
        legacy = FileAgeSize(datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc), 5_000_000_001, True)
        self.assertFalse(age_size_eligibility([legacy], self.now).eligible)

    def test_missing_metadata_fails_closed(self):
        self.assertFalse(age_size_eligibility([], self.now).eligible)
        self.assertFalse(age_size_eligibility([self.record(3, 1, 0)], self.now).eligible)
        naive = FileAgeSize(datetime(2026, 3, 1, 9, 0), 1_000_000_000)
        self.assertFalse(age_size_eligibility([naive], self.now).eligible)
