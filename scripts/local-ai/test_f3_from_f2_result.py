import json
import os
import stat
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import f3_from_f2_result as subject


class F3FromF2Tests(unittest.TestCase):
    cycle = "2026-10-26"

    def setUp(self):
        self.now = int(datetime(2026, 10, 26, 1, 45,
                                tzinfo=subject.LOCAL_ZONE).timestamp())
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state_root = self.root / "f2-scheduled"
        self.state_root.mkdir(mode=0o700)
        self.target_root = self.root / "state"
        self.target_root.mkdir(mode=0o700)
        self.backup_root = self.root / "dump"
        self.backup_root.mkdir()
        self.paths = {}
        self.inventory = []
        rows = []
        for index, vmid in enumerate(("104", "110", "116")):
            name = f"vzdump-lxc-{vmid}-2026_10_26-00_30_00.tar.zst"
            path = self.backup_root / name
            path.write_bytes((vmid * 10).encode())
            self.paths[f"backups:backup/{name}"] = str(path)
            ctime = self.now - 300 + index
            self.inventory.append({"vmid": int(vmid), "volid": f"backups:backup/{name}",
                                   "size": path.stat().st_size, "ctime": ctime,
                                   "content": "backup", "format": "tar.zst"})
            rows.append({"vmid": vmid, "volid": f"backups:backup/{name}",
                         "size": path.stat().st_size, "ctime": ctime,
                         "test_started_epoch": self.now - 200 + index * 10,
                         "test_finished_epoch": self.now - 195 + index * 10,
                         "test_elapsed_ms": 5000, "test_exit": 0})
        projection = {"schema": "aster-read-only-archive-timing.v1",
                      "state": "complete", "date": "2026_10_26",
                      "archives": rows, "admission_receipt_written": False}
        self.state = {"schema": subject.F2_SCHEMA, "cycle": self.cycle,
                      "phase": "final", "state": "complete", "error_class": "",
                      "first_failure_phase": "", "failure_class": "",
                      "result": projection}
        self.state_path = self.state_root / f"{self.cycle}.json"
        self.state_path.write_bytes(subject.canonical_bytes(self.state))
        self.state_path.chmod(0o600)

    def tearDown(self):
        self.temp.cleanup()

    def resolve(self, volid):
        return self.paths[volid]

    def build(self, state=None, now=None):
        with patch("retained_archive_integrity.BACKUP_ROOT", self.backup_root):
            return subject.build_receipt(
                self.state if state is None else state, cycle=self.cycle,
                now_epoch=self.now if now is None else now,
                inventory=self.inventory, resolve=self.resolve, lstat=os.lstat)

    def test_success_rebinds_exact_rows_and_current_identity(self):
        receipt = self.build()
        self.assertEqual([row["vmid"] for row in receipt["archives"]], ["104", "110", "116"])
        self.assertEqual(receipt["date"], "2026_10_26")
        self.assertTrue(all(row["test_exit"] == 0 for row in receipt["archives"]))

    def test_no_go_and_partial_states_are_rejected(self):
        for phase, state in (("prepare", "prepared"), ("final", "no_go")):
            changed = dict(self.state); changed["phase"] = phase; changed["state"] = state
            with self.subTest(phase=phase), self.assertRaises(subject.F3ConversionError):
                self.build(changed)

    def test_inventory_substitution_and_archive_change_are_rejected(self):
        changed = [dict(item) for item in self.inventory]
        changed[0]["size"] += 1
        with patch("retained_archive_integrity.BACKUP_ROOT", self.backup_root), \
                self.assertRaises(subject.F3ConversionError):
            subject.build_receipt(self.state, cycle=self.cycle, now_epoch=self.now,
                                  inventory=changed, resolve=self.resolve, lstat=os.lstat)
        Path(self.paths[self.inventory[1]["volid"]]).write_bytes(b"changed")
        with self.assertRaises(subject.F3ConversionError):
            self.build()

    def test_stale_result_and_duplicate_key_state_are_rejected(self):
        with self.assertRaises(subject.F3ConversionError):
            self.build(now=self.now + subject.MAX_F2_AGE_SECONDS + 1)
        raw = b'{"schema":"x","schema":"y"}\n'
        self.state_path.write_bytes(raw)
        with self.assertRaises(subject.F3ConversionError):
            subject.secure_read(self.state_path, required_uid=os.geteuid())

    def test_secure_reader_rejects_noncanonical_and_oversized(self):
        self.state_path.write_text(json.dumps(self.state) + "\n")
        with self.assertRaises(subject.F3ConversionError):
            subject.secure_read(self.state_path, required_uid=os.geteuid())
        self.state_path.write_bytes(b"{" + b" " * subject.MAX_STATE_BYTES + b"}")
        with self.assertRaises(subject.F3ConversionError):
            subject.secure_read(self.state_path, required_uid=os.geteuid())

    def test_write_once_is_owner_only_and_no_overwrite(self):
        receipt = self.build()
        target = self.target_root / "archive-integrity.json"
        digest = subject.write_once(target, receipt, required_uid=os.geteuid())
        self.assertEqual(digest, __import__("hashlib").sha256(target.read_bytes()).hexdigest())
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        with self.assertRaises(subject.F3ConversionError):
            subject.write_once(target, receipt, required_uid=os.geteuid())

    def test_produce_rejects_state_replacement_before_write(self):
        target = self.target_root / "archive-integrity.json"
        reads = [subject.secure_read(self.state_path, required_uid=os.geteuid())]
        changed = dict(self.state); changed["failure_class"] = "UNKNOWN"
        reads.append((changed, subject.canonical_bytes(changed)))
        cycle_epoch = int(datetime(2026, 10, 26, 1, 45, tzinfo=subject.LOCAL_ZONE).timestamp())
        with patch.object(subject, "F2_STATE_ROOT", self.state_root), \
                patch.object(subject, "secure_read", side_effect=reads), \
                patch("retained_archive_integrity.BACKUP_ROOT", self.backup_root):
            with self.assertRaises(subject.F3ConversionError):
                subject.produce(clock=lambda: cycle_epoch,
                                inventory=lambda: self.inventory,
                                resolve=self.resolve, lstat=os.lstat,
                                target=target, required_uid=os.geteuid())
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
