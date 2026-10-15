import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import retained_archive_integrity as archive


class RetainedArchiveIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = int(datetime(2026, 10, 15, 1, 12, tzinfo=archive.LOCAL_ZONE).timestamp())
        self.day = archive._day(self.now)
        self.items = []
        for vmid in ("104", "110", "116"):
            name = f"vzdump-lxc-{vmid}-2026_10_15-00_45_00.tar.zst"
            path = self.root / name
            path.write_bytes((vmid + "synthetic").encode())
            self.items.append({"vmid": int(vmid), "volid": "backups:backup/" + name,
                               "content": "backup", "format": "tar.zst",
                               "size": path.stat().st_size, "ctime": self.now - 1200})
        self.root_patch = patch.object(archive, "BACKUP_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def resolve(self, volid):
        return str(self.root / volid.rsplit("/", 1)[-1])

    def captured(self):
        self.probe_timeouts = []
        def successful_probe(path, timeout):
            self.probe_timeouts.append(timeout)
            return 0, 100
        return archive.capture(self.items, date=self.day, resolve=self.resolve,
                               lstat=os.lstat, probe=successful_probe,
                               clock=lambda: self.now)

    def verify(self, receipt, *, now=None, items=None):
        return archive.verify(receipt, self.items if items is None else items,
                              date=self.day, now_epoch=self.now if now is None else now,
                              resolve=self.resolve, lstat=os.lstat)

    def test_three_exact_current_archives_pass_and_bind(self):
        receipt = self.captured()
        self.assertEqual([row["vmid"] for row in receipt["archives"]], ["104", "110", "116"])
        self.assertEqual(self.probe_timeouts, [120, 900, 120])
        self.assertTrue(self.verify(receipt).startswith("retained-archive-integrity-sha256:"))

    def test_replaced_same_path_and_stale_receipt_fail(self):
        receipt = self.captured()
        path = self.root / receipt["archives"][1]["path"].rsplit("/", 1)[-1]
        path.unlink()
        path.write_bytes(b"110synthetiC")
        with self.assertRaises(archive.IntegrityError):
            self.verify(receipt)
        with self.assertRaises(archive.IntegrityError):
            self.verify(receipt, now=self.now + 10_801)

    def test_partial_wrong_cycle_and_timed_out_scan_fail(self):
        receipt = self.captured()
        receipt["archives"].pop()
        with self.assertRaises(archive.IntegrityError):
            self.verify(receipt)
        other = self.captured()
        changed = [dict(row) for row in self.items]
        changed[1]["volid"] = changed[1]["volid"].replace("2026_10_15", "2026_10_14")
        with self.assertRaises(archive.IntegrityError):
            self.verify(other, items=changed)
        with self.assertRaises(archive.IntegrityError):
            archive.capture(self.items, date=self.day, resolve=self.resolve,
                            lstat=os.lstat, probe=lambda path, timeout: (124, timeout * 1000),
                            clock=lambda: self.now)

    def test_outer_deadline_rejects_insufficient_budget_and_overrun(self):
        with self.assertRaisesRegex(archive.IntegrityError, "insufficient"):
            archive.capture(self.items, date=self.day, resolve=self.resolve,
                            lstat=os.lstat, probe=lambda path, timeout: (0, 10),
                            clock=lambda: self.now, deadline_epoch=self.now + 1139)
        ticks = iter((self.now,) * 6 + (self.now + 1201,))
        with self.assertRaises(archive.IntegrityError):
            archive.capture(self.items, date=self.day, resolve=self.resolve,
                            lstat=os.lstat, probe=lambda path, timeout: (0, 10),
                            clock=lambda: next(ticks), deadline_epoch=self.now + 1200)

    def test_symlink_and_file_change_during_test_fail(self):
        path = self.root / self.items[0]["volid"].rsplit("/", 1)[-1]
        path.unlink()
        path.symlink_to(self.root / self.items[1]["volid"].rsplit("/", 1)[-1])
        with self.assertRaises(archive.IntegrityError):
            self.captured()
        path.unlink()
        path.write_bytes(b"104synthetic")
        def modify(path, timeout):
            with open(path, "ab") as stream:
                stream.write(b"x")
            return 0, 100
        with self.assertRaises(archive.IntegrityError):
            archive.capture(self.items, date=self.day, resolve=self.resolve,
                            lstat=os.lstat, probe=modify, clock=lambda: self.now)

    def test_receipt_custody_rejects_weak_parent_and_symlink_destination(self):
        owner = os.getuid()
        parent = self.root / "custody"
        parent.mkdir(mode=0o700)
        receipt = parent / "receipt.json"
        archive._check_receipt_parent(receipt, expected_uid=owner)
        parent.chmod(0o755)
        with self.assertRaises(archive.IntegrityError):
            archive._check_receipt_parent(receipt, expected_uid=owner)
        parent.chmod(0o700)
        receipt.symlink_to(self.root / "other")
        with self.assertRaises(archive.IntegrityError):
            archive._check_existing_receipt(receipt, expected_uid=owner)
        receipt.unlink()
        receipt.write_text("{}")
        receipt.chmod(0o644)
        with self.assertRaises(archive.IntegrityError):
            archive._check_existing_receipt(receipt, expected_uid=owner)


if __name__ == "__main__":
    unittest.main()
