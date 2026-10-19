import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from f2_preflight_snapshot import (F2PreflightError, PVE_ARTIFACTS, PVE_JOB,
                                   TRUENAS_MIRROR, TRUENAS_TASKS, LEASE_STATUS,
                                   collect_snapshot, final_guard)


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
        snapshot = collect_snapshot(self.runner(), cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(3, 10), exclusion_token="lease-1")
        final_guard(snapshot, now_epoch=self.epoch(3, 11), exclusion_token="lease-1")
        self.assertTrue(snapshot.archive_identity_verified)

    def test_final_guard_rejects_stale_or_changed_exclusion(self):
        snapshot = collect_snapshot(self.runner(), cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(3, 10), exclusion_token="lease-1")
        with self.assertRaisesRegex(F2PreflightError, "stale"):
            final_guard(snapshot, now_epoch=self.epoch(3, 12), exclusion_token="lease-1")
        with self.assertRaisesRegex(F2PreflightError, "exclusion"):
            final_guard(snapshot, now_epoch=self.epoch(3, 11), exclusion_token="other")

    def test_missing_or_failed_chain_fails_closed(self):
        def bad(command, timeout):
            if command == PVE_ARTIFACTS: return 0, "[]"
            return self.runner()(command, timeout)
        with self.assertRaises(F2PreflightError):
            collect_snapshot(bad, cycle="2026-10-19", lease_issued_epoch=self.epoch(4, 0), captured_epoch=self.epoch(3, 10), exclusion_token="lease-1")


if __name__ == "__main__":
    unittest.main()
