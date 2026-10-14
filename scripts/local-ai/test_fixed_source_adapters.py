import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from fixed_source_adapters import FixedSourceAdapters, SourceAdapterError, _schedule_ok


class FixedSourceAdapterTests(unittest.TestCase):
    def test_schedule_requires_same_day_task_completion_and_arguments(self):
        items = []
        zone = ZoneInfo("America/Vancouver")
        for item_id, hour, started, finished in ((1, 1, 1791861000000, 1791861300000), (3, 2, 1791864600000, 1791864900000), (2, 3, 1791868200000, 1791868500000)):
            started = int(datetime(2026, 10, 13, hour, 5, tzinfo=zone).timestamp() * 1000)
            finished = int(datetime(2026, 10, 13, hour, 10, tzinfo=zone).timestamp() * 1000)
            items.append({"id": item_id, "enabled": True, "schedule": {"hour": hour, "minute": 0}, "job": {"state": "SUCCESS", "arguments": [item_id], "time_started": {"$date": started}, "time_finished": {"$date": finished}}})
        self.assertTrue(_schedule_ok(items, date_prefix="2026_10_13", artifact_ctimes=(int(datetime(2026, 10, 13, 0, 50, tzinfo=zone).timestamp()),), lease_issued_epoch=int(datetime(2026, 10, 13, 4, 0, tzinfo=zone).timestamp())))
        items[1]["job"]["arguments"] = [1]
        self.assertFalse(_schedule_ok(items, date_prefix="2026_10_13", artifact_ctimes=(int(datetime(2026, 10, 13, 0, 50, tzinfo=zone).timestamp()),), lease_issued_epoch=int(datetime(2026, 10, 13, 4, 0, tzinfo=zone).timestamp())))
        items[1]["job"]["arguments"] = [3]
        items[1]["job"]["time_finished"]["$date"] = int(datetime(2026, 10, 13, 11, 19, tzinfo=zone).timestamp() * 1000)
        self.assertFalse(_schedule_ok(items, date_prefix="2026_10_13", artifact_ctimes=(int(datetime(2026, 10, 13, 0, 50, tzinfo=zone).timestamp()),), lease_issued_epoch=int(datetime(2026, 10, 13, 12, 0, tzinfo=zone).timestamp())))

    def test_quiescence_uses_fixed_commands_and_two_samples(self):
        calls = []
        def runner(argv, timeout):
            calls.append(argv)
            if argv[:2] == ("pct", "exec") and "systemctl" in argv:
                return 0, "inactive\n10\n"
            if argv[:2] == ("pct", "exec") and "readlink" in argv:
                return 0, "/dev/null\n"
            if argv[:2] == ("pct", "exec"):
                return 3, "inactive\n"
            raise AssertionError(argv)
        adapter = FixedSourceAdapters(runner, sleep=lambda _: None, monotonic=iter((1, 2)).__next__)
        receipt = adapter.quiescence()
        self.assertTrue(receipt.source_observed)
        self.assertTrue(any("news-aggregator-digest.timer" in call for call in calls))

    def test_active_news_rejects_quiescence(self):
        def runner(argv, timeout):
            if "news-aggregator-digest.timer" in argv:
                return 0, "active\n"
            if argv[:2] == ("pct", "exec") and "systemctl" in argv:
                return 0, "inactive\n10\n"
            if argv[:2] == ("pct", "exec") and "readlink" in argv:
                return 0, "/dev/null\n"
            return 0, "active\n"
        with self.assertRaises(SourceAdapterError):
            FixedSourceAdapters(runner, sleep=lambda _: None, monotonic=iter((1, 2)).__next__).quiescence()


if __name__ == "__main__":
    unittest.main()
