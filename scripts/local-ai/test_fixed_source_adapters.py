import json
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fixed_source_adapters import FixedSourceAdapters, SourceAdapterError, _schedule_ok


class FixedSourceAdapterTests(unittest.TestCase):
    def test_retained_backup_requires_current_chain_and_root_receipt(self):
        zone = ZoneInfo("America/Vancouver")
        def sec(hour, minute):
            return int(datetime(2026, 10, 15, hour, minute, tzinfo=zone).timestamp())
        artifacts = []
        for vmid in (104, 110, 116):
            artifacts.append({"vmid": vmid, "volid": f"backups:backup/vzdump-lxc-{vmid}-2026_10_15-00_45_00.tar.zst",
                              "content": "backup", "format": "tar.zst", "size": vmid, "ctime": sec(0, 50)})
        tasks = []
        for task_id, hour in ((1, 1), (3, 2), (2, 3)):
            tasks.append({"id": task_id, "enabled": True,
                          "schedule": {"hour": hour, "minute": 0},
                          "job": {"state": "SUCCESS", "arguments": [task_id],
                                  "time_started": {"$date": sec(hour, 5) * 1000},
                                  "time_finished": {"$date": sec(hour, 6) * 1000}}})
        mirror_name = artifacts[1]["volid"].rsplit("/", 1)[-1]
        mirror = [{"name": mirror_name, "type": "FILE", "path": "/mnt/Recovery/guests/aster-lxc110/" + mirror_name, "size": 110}]
        calls = []
        def runner(argv, timeout):
            calls.append(argv)
            if argv[0] == "pvesh":
                return 0, json.dumps(artifacts)
            if "rsynctask.query" in argv:
                return 0, json.dumps(tasks)
            if "filesystem.listdir" in argv:
                return 0, json.dumps(mirror)
            raise AssertionError(argv)
        adapter = FixedSourceAdapters(runner, clock=lambda: datetime(2026, 10, 15, 3, 10, tzinfo=zone))
        with patch("fixed_source_adapters.load_root_owned", return_value={"synthetic": True}) as load, patch("fixed_source_adapters.verify_retained_integrity", return_value="retained-archive-integrity-sha256:" + "a" * 64) as verify:
            receipt = adapter.backup_from_retained(date_prefix="2026_10_15", lease_issued_epoch=sec(3, 10))
            self.assertTrue(receipt.integrity_verified)
            self.assertTrue(receipt.integrity_receipt.startswith("retained-archive-integrity-sha256:"))
            load.assert_called_once()
            verify.assert_called_once()
        self.assertFalse(any(call[0] == "zstd" for call in calls))
        tasks[2]["job"]["state"] = "FAILED"
        with patch("fixed_source_adapters.load_root_owned", return_value={"synthetic": True}), patch("fixed_source_adapters.verify_retained_integrity", return_value="retained-archive-integrity-sha256:" + "a" * 64):
            with self.assertRaises(SourceAdapterError):
                adapter.backup_from_retained(date_prefix="2026_10_15", lease_issued_epoch=sec(3, 10))

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

    def test_rejects_start_before_scheduled_slot(self):
        zone = ZoneInfo("America/Vancouver")
        def epoch(hour, minute):
            return int(datetime(2026, 10, 13, hour, minute, tzinfo=zone).timestamp() * 1000)
        items = []
        for item_id, hour in ((1, 1), (3, 2), (2, 3)):
            items.append({"id": item_id, "enabled": True, "schedule": {"hour": hour, "minute": 0}, "job": {"state": "SUCCESS", "arguments": [item_id], "time_started": {"$date": epoch(hour, 5)}, "time_finished": {"$date": epoch(hour, 10)}}})
        items[0]["job"]["time_started"]["$date"] = epoch(0, 59)
        self.assertFalse(_schedule_ok(items, date_prefix="2026_10_13", artifact_ctimes=(int(datetime(2026, 10, 13, 0, 30, tzinfo=zone).timestamp()),), lease_issued_epoch=int(datetime(2026, 10, 13, 4, 0, tzinfo=zone).timestamp())))

    def test_rejects_overlapping_chain_and_early_start_before_latest_artifact(self):
        zone = ZoneInfo("America/Vancouver")
        def epoch(hour, minute):
            return int(datetime(2026, 10, 13, hour, minute, tzinfo=zone).timestamp() * 1000)
        items = []
        for item_id, hour in ((1, 1), (3, 2), (2, 3)):
            items.append({"id": item_id, "enabled": True, "schedule": {"hour": hour, "minute": 0}, "job": {"state": "SUCCESS", "arguments": [item_id], "time_started": {"$date": epoch(hour, 5)}, "time_finished": {"$date": epoch(hour, 10)}}})
        items[1]["job"]["time_started"]["$date"] = epoch(2, 5)
        self.assertFalse(_schedule_ok(items, date_prefix="2026_10_13", artifact_ctimes=(int(datetime(2026, 10, 13, 0, 50, tzinfo=zone).timestamp()), int(datetime(2026, 10, 13, 1, 30, tzinfo=zone).timestamp())), lease_issued_epoch=int(datetime(2026, 10, 13, 4, 0, tzinfo=zone).timestamp())))
        items[1]["job"]["time_started"]["$date"] = epoch(1, 5)
        items[1]["job"]["time_finished"]["$date"] = epoch(2, 10)
        self.assertFalse(_schedule_ok(items, date_prefix="2026_10_13", artifact_ctimes=(int(datetime(2026, 10, 13, 0, 50, tzinfo=zone).timestamp()),), lease_issued_epoch=int(datetime(2026, 10, 13, 4, 0, tzinfo=zone).timestamp())))

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
