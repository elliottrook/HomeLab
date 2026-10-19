import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from f2_preflight_snapshot import (CLOCK, F2Coordinator, F2PreflightError, LOADAVG,
                                   LEASE_STATUS, LOCK_ABSENCE, PVE_ARTIFACTS,
                                   PVE_JOB, QUIET_PROCESSES, RECEIPT_ABSENCE,
                                   STATE_ABSENCE, TRUENAS_MIRROR, TRUENAS_TASKS,
                                   collect_snapshot, final_guard, read_snapshot,
                                   write_snapshot)


class F2PreflightSnapshotTests(unittest.TestCase):
    def epoch(self, hour, minute):
        return int(datetime(2026, 10, 19, hour, minute, tzinfo=ZoneInfo("America/Vancouver")).timestamp())

    def sources(self):
        artifacts = [{"vmid": vmid, "volid": f"backups:backup/vzdump-lxc-{vmid}-2026_10_19-00_45_00.tar.zst", "content": "backup", "format": "tar.zst", "size": vmid, "ctime": self.epoch(0, 50)} for vmid in (104, 110, 116)]
        tasks = [{"id": item_id, "enabled": True, "schedule": {"hour": hour, "minute": 0}, "job": {"state": "SUCCESS", "arguments": [item_id], "time_started": {"$date": self.epoch(hour, 5) * 1000}, "time_finished": {"$date": self.epoch(hour, 6) * 1000}}} for item_id, hour in ((1, 1), (3, 2), (2, 3))]
        mirror = [{"name": artifacts[1]["volid"].rsplit("/", 1)[-1], "type": "FILE", "path": "/mnt/Recovery/guests/aster-lxc110/" + artifacts[1]["volid"].rsplit("/", 1)[-1], "size": 110}]
        return artifacts, tasks, mirror

    def runner(self):
        artifacts, tasks, mirror = self.sources()
        def run(command, timeout):
            if command == PVE_ARTIFACTS: return 0, json.dumps(artifacts)
            if command == PVE_JOB: return 0, json.dumps({"id": "backup-49999802-1365", "enabled": 1, "schedule": "00:30", "storage": "backups", "type": "vzdump", "all": 1})
            if command == TRUENAS_TASKS: return 0, json.dumps(tasks)
            if command == TRUENAS_MIRROR: return 0, json.dumps(mirror)
            if command == LEASE_STATUS: return 0, '{"state": "ready"}\n'
            raise AssertionError(command)
        return run

    def test_collects_slow_chain_and_final_guard_accepts_fresh_exclusion(self):
        snapshot = collect_snapshot(self.runner(), cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(1, 10))
        def guard(command, timeout):
            if command == CLOCK: return 0, str(self.epoch(1, 11))
            if command in (LOCK_ABSENCE, STATE_ABSENCE, RECEIPT_ABSENCE): return 0, ""
            if command == LEASE_STATUS: return 0, '{"state":"ready"}'
            if command == QUIET_PROCESSES: return 1, ""
            if command == LOADAVG: return 0, "1.0 0.5 0.2 1/100 1\n"
            if command == ("sha256sum", "/pin"): return 0, "pin  /pin\n"
            raise AssertionError(command)
        with tempfile.TemporaryDirectory() as tmp, F2Coordinator(Path(tmp)) as coordinator:
            final_guard(snapshot, runner=guard, expected_pins={"/pin": "pin"}, coordinator=coordinator)
        self.assertTrue(snapshot.archive_identity_verified)

    def test_final_guard_rejects_stale_or_changed_exclusion(self):
        snapshot = collect_snapshot(self.runner(), cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(1, 10))
        def guard(command, timeout):
            if command == CLOCK: return 0, str(self.epoch(1, 12))
            if command in (LOCK_ABSENCE, STATE_ABSENCE, RECEIPT_ABSENCE): return 0, ""
            if command == LEASE_STATUS: return 0, '{"state":"ready"}'
            if command == QUIET_PROCESSES: return 1, ""
            if command == LOADAVG: return 0, "1.0 0.5 0.2 1/100 1\n"
            if command == ("sha256sum", "/pin"): return 0, "pin  /pin\n"
            raise AssertionError(command)
        with self.assertRaisesRegex(F2PreflightError, "stale"):
            with tempfile.TemporaryDirectory() as tmp, F2Coordinator(Path(tmp)) as coordinator:
                final_guard(snapshot, runner=guard, expected_pins={"/pin": "pin"}, coordinator=coordinator)
        def changed(command, timeout):
            if command == CLOCK: return 0, str(self.epoch(1, 11))
            if command in (LOCK_ABSENCE, STATE_ABSENCE, RECEIPT_ABSENCE): return 0, ""
            if command == LEASE_STATUS: return 0, '{"state":"ready"}'
            if command == QUIET_PROCESSES: return 1, ""
            if command == LOADAVG: return 0, "1.0 0.5 0.2 1/100 1\n"
            if command == ("sha256sum", "/pin"): return 0, "pin  /pin\n"
            raise AssertionError(command)
        with self.assertRaisesRegex(F2PreflightError, "exclusion"):
            with tempfile.TemporaryDirectory() as tmp:
                final_guard(snapshot, runner=changed, expected_pins={"/pin": "pin"}, coordinator=F2Coordinator(Path(tmp)))

    def test_f2_window_allows_task_one_before_tasks_two_and_three(self):
        artifacts, tasks, mirror = self.sources()
        tasks[1]["job"] = {}
        tasks[2]["job"] = {}
        def run(command, timeout):
            if command == PVE_ARTIFACTS: return 0, json.dumps(artifacts)
            if command == PVE_JOB: return 0, json.dumps({"id": "backup-49999802-1365", "enabled": 1, "schedule": "00:30", "storage": "backups", "type": "vzdump", "all": 1})
            if command == TRUENAS_TASKS: return 0, json.dumps(tasks)
            if command == TRUENAS_MIRROR: return 0, json.dumps(mirror)
            if command == LEASE_STATUS: return 0, '{"state":"ready"}'
            raise AssertionError(command)
        snapshot = collect_snapshot(run, cycle="2026-10-19", lease_issued_epoch=self.epoch(1, 7), captured_epoch=self.epoch(1, 7))
        self.assertTrue(snapshot.archive_identity_verified)

    def test_missing_or_failed_chain_fails_closed(self):
        def bad(command, timeout):
            if command == PVE_ARTIFACTS: return 0, "[]"
            return self.runner()(command, timeout)
        with self.assertRaises(F2PreflightError):
            collect_snapshot(bad, cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(3, 10))

    def test_snapshot_reader_rejects_untrusted_custody(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(F2PreflightError, "custody|unreadable"):
                read_snapshot(Path(tmp) / "snapshot.json")

    def test_snapshot_reader_rejects_insecure_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "snapshots"
            parent.mkdir(mode=0o755)
            with self.assertRaisesRegex(F2PreflightError, "custody"):
                read_snapshot(parent / "snapshot.json")

    @unittest.skipUnless(os.geteuid() == 0, "root-custody positive test requires root")
    def test_snapshot_round_trip_under_root_custody(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "snapshots"
            directory.mkdir(mode=0o700)
            os.chmod(directory, 0o700)
            snapshot = collect_snapshot(self.runner(), cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(3, 10))
            path = directory / "lease-1.json"
            write_snapshot(path, snapshot)
            self.assertEqual(read_snapshot(path), snapshot)


if __name__ == "__main__":
    unittest.main()
