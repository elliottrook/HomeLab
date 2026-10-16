"""Fictional timing tests only; no live recovery or new production budget."""
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from recovery_margin_candidate import review

TZ = ZoneInfo('America/Vancouver')


class RecoveryMarginCandidateTests(unittest.TestCase):
    def trigger(self, hour, minute):
        return datetime(2026, 10, 16, hour, minute, tzinfo=TZ)

    def test_earlier_trigger_keeps_margin_but_grants_nothing(self):
        result = review(self.trigger(3, 50), recovery_seconds=900, trigger_lag_seconds=70)
        self.assertEqual(result['assumed_latest_completion_at'], '2026-10-16T04:06:10-07:00')
        self.assertEqual(result['trigger_must_be_before'], '2026-10-16T03:58:50-07:00')
        self.assertFalse(result['budgets_measured'])
        self.assertFalse(result['live_admission_authorized'])

    def test_old_0415_and_0405_triggers_fail(self):
        for hour, minute in ((4, 15), (4, 5)):
            with self.subTest(minute=minute), self.assertRaises(ValueError):
                review(self.trigger(hour, minute), recovery_seconds=900, trigger_lag_seconds=70)

    def test_timer_lag_and_strict_completion_deadline_count(self):
        trigger = self.trigger(3, 59)
        review(trigger, recovery_seconds=900, trigger_lag_seconds=1)
        with self.assertRaises(ValueError):
            review(trigger, recovery_seconds=900, trigger_lag_seconds=60)

    def test_does_not_mix_utc_with_local_cutoff(self):
        trigger = self.trigger(3, 50)
        self.assertEqual(review(trigger, recovery_seconds=900, trigger_lag_seconds=70),
                         review(trigger.astimezone(timezone.utc), recovery_seconds=900,
                                trigger_lag_seconds=70))

    def test_elapsed_budget_crossing_spring_dst_is_not_wall_clock_arithmetic(self):
        with self.assertRaises(ValueError):
            review(datetime(2026, 3, 8, 0, 30, tzinfo=TZ),
                   recovery_seconds=10800, trigger_lag_seconds=70)

    def test_naive_time_and_missing_or_invalid_bounds_rejected(self):
        with self.assertRaises(ValueError):
            review(datetime(2026, 10, 16, 3, 50), recovery_seconds=900, trigger_lag_seconds=70)
        for recovery, lag in ((None, 70), (True, 70), (899, 70), (900, None),
                              (900, True), (900, 0), (900, -1), (86400, 1)):
            with self.subTest(recovery=recovery, lag=lag), self.assertRaises(ValueError):
                review(self.trigger(3, 50), recovery_seconds=recovery, trigger_lag_seconds=lag)


if __name__ == '__main__':
    unittest.main()
