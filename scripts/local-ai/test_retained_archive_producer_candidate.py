import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import retained_archive_producer_candidate as producer
import retained_archive_integrity as archive


ZONE = producer.LOCAL_ZONE


def epoch(hour, minute):
    return int(datetime(2026, 10, 15, hour, minute, tzinfo=ZONE).timestamp())


class RetainedProducerTests(unittest.TestCase):
    def setUp(self):
        self.inventory = [
            {"vmid": vmid, "content": "backup", "format": "tar.zst", "size": 100,
             "ctime": epoch(0, 50),
             "volid": f"backups:backup/vzdump-lxc-{vmid}-2026_10_15-00_45_00.tar.zst"}
            for vmid in (104, 110, 116)
        ]
        self.tasks = [{"id": 1, "enabled": True,
                       "schedule": {"hour": 1, "minute": 0},
                       "job": {"state": "SUCCESS", "arguments": [1],
                               "time_started": {"$date": epoch(1, 1) * 1000},
                               "time_finished": {"$date": epoch(1, 5) * 1000}}}]
        self.saved = []
        self.calls = []
        self.job = {"id": "backup-49999802-1365", "enabled": 1,
                    "schedule": "00:30", "storage": "backups", "type": "vzdump", "all": 1}
        self.journal = [
            {"MESSAGE": "<root@pam> starting task UPID:proxmox:001A1462:02200811:6AD080FF:vzdump::root@pam:",
             "__REALTIME_TIMESTAMP": str(epoch(0, 30) * 1_000_000)},
            {"MESSAGE": "INFO: Backup job finished successfully",
             "__REALTIME_TIMESTAMP": str(epoch(0, 56) * 1_000_000)},
        ]

    def runner(self, argv, timeout):
        self.calls.append(argv)
        if argv[0] == "journalctl":
            return 0, "\n".join(json.dumps(row) for row in self.journal)
        if argv[0] == "pvesh":
            return 0, json.dumps(self.job if "/cluster/backup/" in argv[2] else self.inventory)
        return 0, json.dumps(self.tasks)

    def produce_candidate(self, *, now=None):
        with patch.object(producer, "capture", return_value={"synthetic": True}) as capture:
            result = producer.produce(
                self.runner, clock=lambda: epoch(1, 10) if now is None else now,
                save=self.saved.append,
                read_completion=lambda vmid: f"2026-10-15 00:55:00 INFO: Finished Backup of VM {vmid} (00:00:57)",
            )
        return result, capture

    def test_current_task_and_fixed_inventory_precede_scan_and_save(self):
        result, capture = self.produce_candidate()
        self.assertEqual(self.saved, [result])
        self.assertEqual(capture.call_args.kwargs["deadline_epoch"], epoch(1, 30))
        self.assertEqual(len(self.calls), 4)

    def test_failed_or_stale_task_and_outside_window_save_nothing(self):
        for change in ("FAILED", "stale", "wrong-args"):
            self.tasks[0]["job"]["state"] = "SUCCESS"
            self.tasks[0]["job"]["arguments"] = [1]
            self.tasks[0]["job"]["time_finished"]["$date"] = epoch(1, 5) * 1000
            if change == "FAILED":
                self.tasks[0]["job"]["state"] = "FAILED"
            elif change == "stale":
                self.tasks[0]["job"]["time_finished"]["$date"] = epoch(0, 59) * 1000
            else:
                self.tasks[0]["job"]["arguments"] = [3]
            with self.subTest(change=change), self.assertRaises(producer.IntegrityError):
                self.produce_candidate()
        with self.assertRaises(producer.IntegrityError):
            self.produce_candidate(now=epoch(1, 20))
        self.assertEqual(self.saved, [])

    def test_partial_scan_never_saves_and_cli_is_disabled(self):
        with patch.object(producer, "capture", side_effect=producer.IntegrityError("timeout")):
            with self.assertRaises(producer.IntegrityError):
                producer.produce(self.runner, clock=lambda: epoch(1, 10), save=self.saved.append,
                                 read_completion=lambda vmid: f"2026-10-15 00:55:00 INFO: Finished Backup of VM {vmid} (00:00:57)")
        self.assertEqual(self.saved, [])
        with patch.object(producer, "produce", side_effect=AssertionError("must stay disabled")):
            self.assertEqual(producer.main(), 0)

    def test_missing_guest_completion_or_wrong_job_blocks_scan(self):
        with patch.object(producer, "capture", side_effect=AssertionError("scan must not begin")):
            with self.assertRaises(producer.IntegrityError):
                producer.produce(self.runner, clock=lambda: epoch(1, 10), save=self.saved.append,
                                 read_completion=lambda vmid: "backup still running")
            self.job["schedule"] = "02:00"
            with self.assertRaises(producer.IntegrityError):
                self.produce_candidate()
        self.assertEqual(self.saved, [])

    def test_missing_whole_job_success_blocks_scan(self):
        self.journal[1]["MESSAGE"] = "TASK ERROR: failed"
        with patch.object(producer, "capture", side_effect=AssertionError("scan must not begin")):
            with self.assertRaisesRegex(producer.IntegrityError, "whole backup job"):
                self.produce_candidate()
        self.assertEqual(self.saved, [])

    def test_actual_capture_path_binds_all_three_files_and_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for item in self.inventory:
                (root / item["volid"].rsplit("/", 1)[-1]).write_bytes(b"x" * item["size"])
            with patch.object(archive, "BACKUP_ROOT", root):
                result = producer.produce(
                    self.runner, clock=lambda: epoch(1, 10),
                    resolve=lambda volid: str(root / volid.rsplit("/", 1)[-1]),
                    lstat=os.lstat, probe=lambda path, timeout: (0, 100),
                    save=self.saved.append,
                    read_completion=lambda vmid: f"2026-10-15 00:55:00 INFO: Finished Backup of VM {vmid} (00:00:57)",
                )
            self.assertEqual([row["vmid"] for row in result["archives"]], ["104", "110", "116"])
            self.assertEqual(self.saved, [result])


if __name__ == "__main__":
    unittest.main()
