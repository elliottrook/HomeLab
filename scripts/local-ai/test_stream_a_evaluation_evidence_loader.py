import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import stream_a_evaluation_evidence_loader as subject
from lease_contract import ACCEPTED_BACKEND, ACCEPTED_MODEL, LeaseReceipt
from lease_watchdog import EXPECTED_SCHEDULES, Observation
from pre_acquire_receipt import encode as encode_f4
from stream_a_evaluation_admission import (
    ADMISSION_PREFIX, ADMISSION_SCHEMA, EXPECTED_AUTH_IDENTITY,
    EXPECTED_BACKEND as ADMISSION_BACKEND, EXPECTED_BINARY_SHA256,
    EXPECTED_D4_DIGEST, EXPECTED_M3_DIGEST, EXPECTED_MODEL as ADMISSION_MODEL,
    EXPECTED_UNIT_SHA256, F5_SCHEMA, canonical_bytes,
)


class EvidenceLoaderTests(unittest.TestCase):
    cycle = "2026-10-26"
    nonce = "0123456789abcdef"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paths = subject.EvidencePaths(
            f2_root=self._dir("f2"), f3=self._dir("f3") / "receipt.json",
            f4=self._dir("f4") / "receipt.json", runtime=self._dir("runtime"),
        )
        self.now = int(datetime(2026, 10, 26, 1, 35,
                                tzinfo=subject.LOCAL_ZONE).timestamp())
        self.now_minute = 95
        self.inventory = []
        self.resolved = {}
        archives = []
        for index, vmid in enumerate(("104", "110", "116")):
            name = f"vzdump-lxc-{vmid}-2026_10_26-00_30_00.tar.zst"
            path = self.root / name
            path.write_bytes(b"archive" if index == 0 else vmid.encode())
            if index == 0:
                self.archive = path
            volid = f"backups:backup/{name}"
            ctime = self.now - 900 + index
            self.inventory.append({"vmid": int(vmid), "volid": volid,
                                   "size": path.stat().st_size, "ctime": ctime,
                                   "content": "backup", "format": "tar.zst"})
            self.resolved[volid] = str(path)
            info = os.lstat(path)
            archives.append({
                "vmid": vmid, "volid": volid, "size": info.st_size,
                "ctime": ctime, "path": str(path), "device": info.st_dev,
                "inode": info.st_ino, "mtime_ns": info.st_mtime_ns,
                "ctime_ns": info.st_ctime_ns,
                "test_started_epoch": self.now - 700 + index,
                "test_finished_epoch": self.now - 690 + index,
                "test_elapsed_ms": 100, "test_exit": 0,
            })
        f3 = {"schema": "aster-retained-archive-integrity.v1",
              "date": "2026_10_26", "started_epoch": self.now - 710,
              "finished_epoch": self.now - 680, "archives": archives}
        self._write(self.paths.f3, json.dumps(
            f3, sort_keys=True, separators=(",", ":")).encode())
        self.f3_raw = self.paths.f3.read_bytes()
        self.backup = "retained-archive-integrity-sha256:" + hashlib.sha256(self.f3_raw).hexdigest()

        f2 = {"schema": "aster-f2-scheduled.v1", "cycle": self.cycle,
              "phase": "final", "state": "complete", "error_class": "",
              "first_failure_phase": "", "failure_class": "",
              "result": {"schema": "aster-read-only-archive-timing.v1",
                         "state": "complete", "date": "2026_10_26",
                         "archives": [{k: row[k] for k in (
                             "vmid", "volid", "size", "ctime", "test_started_epoch",
                             "test_finished_epoch", "test_elapsed_ms", "test_exit")}
                             for row in archives],
                         "admission_receipt_written": False}}
        self.f2_raw = canonical_bytes(f2)
        self._write(self.paths.f2_root / f"{self.cycle}.json", self.f2_raw)

        lease_id = f"stream-a-evaluation-{self.cycle}-{self.nonce}"
        f4_raw = encode_f4(
            LeaseReceipt(lease_id, 1, self.now_minute, self.now_minute + 90,
                         self.backup, ACCEPTED_MODEL, ACCEPTED_BACKEND, False, False),
            Observation(self.now_minute, True, True, True, True, True,
                        EXPECTED_SCHEDULES, True, True, True, True, True),
            captured_epoch=self.now - 30,
        )
        self._write(self.paths.f4, f4_raw)
        f5 = {
            "schema": F5_SCHEMA, "cycle_date": self.cycle,
            "observed_epoch": self.now - 20, "expires_epoch": self.now + 600,
            "f2_result_sha256": hashlib.sha256(self.f2_raw).hexdigest(),
            "f3_receipt_sha256": hashlib.sha256(self.f3_raw).hexdigest(),
            "f4_receipt_sha256": hashlib.sha256(f4_raw).hexdigest(),
            "lxc110_mirror_identity": "task2:success",
            "schedule_set_sha256": "e" * 64, "model": ADMISSION_MODEL,
            "binary_sha256": EXPECTED_BINARY_SHA256,
            "unit_sha256": EXPECTED_UNIT_SHA256,
            "auth_identity": EXPECTED_AUTH_IDENTITY,
            "consumer_baseline_sha256": "f" * 64,
            "conflicting_lease": False, "conflicting_job": False,
        }
        f5_raw = canonical_bytes(f5); self._write(self.paths.f5, f5_raw)
        admission = {
            "schema": ADMISSION_SCHEMA, "cycle_date": self.cycle,
            "lease_id": lease_id, "generation": 1,
            "created_epoch": self.now - 10, "expires_epoch": self.now + 600,
            "backup_receipt": self.backup,
            "f2_result_sha256": hashlib.sha256(self.f2_raw).hexdigest(),
            "f3_receipt_sha256": hashlib.sha256(self.f3_raw).hexdigest(),
            "f4_receipt_sha256": hashlib.sha256(f4_raw).hexdigest(),
            "f5_observation_sha256": hashlib.sha256(f5_raw).hexdigest(),
            "d4_run_digest": EXPECTED_D4_DIGEST,
            "m3_manifest_sha256": EXPECTED_M3_DIGEST,
            "model": ADMISSION_MODEL, "backend": ADMISSION_BACKEND,
        }
        admission_raw = canonical_bytes(admission)
        self._write(self.paths.admission, admission_raw)
        self.expectation = subject.EvidenceExpectation(
            self.cycle, self.nonce,
            ADMISSION_PREFIX + hashlib.sha256(admission_raw).hexdigest())

    def tearDown(self):
        self.temp.cleanup()

    def _dir(self, name):
        path = self.root / name; path.mkdir(mode=0o700); path.chmod(0o700)
        return path

    def _write(self, path, raw):
        path.write_bytes(raw); path.chmod(0o600)

    def load(self, **changes):
        args = dict(now_epoch=self.now, now_minute=self.now_minute,
                    paths=self.paths, inventory=lambda: self.inventory,
                    resolve=lambda volid: self.resolved[volid], lstat=os.lstat,
                    required_uid=os.geteuid())
        args.update(changes)
        with patch("retained_archive_integrity.BACKUP_ROOT", self.root):
            return subject.load_accepted_evidence(self.expectation, **args)

    def test_loads_exact_current_cycle_into_content_free_evidence(self):
        accepted = self.load()
        self.assertEqual(accepted.cycle_date, self.cycle)
        self.assertEqual(accepted.backup_receipt, self.backup)
        self.assertEqual(accepted.admission_receipt, self.expectation.admission_receipt)

    def test_changed_f2_f3_or_f4_fails_closed(self):
        for path in (self.paths.f2_root / f"{self.cycle}.json", self.paths.f3, self.paths.f4):
            with self.subTest(path=path.name):
                original = path.read_bytes(); path.write_bytes(original + b" ")
                with self.assertRaises(subject.EvidenceLoadError):
                    self.load()
                path.write_bytes(original)

    def test_f2_f3_archive_rows_must_match_directly(self):
        f2 = json.loads(self.f2_raw)
        f3 = json.loads(self.f3_raw)
        f2["result"]["archives"][1]["test_elapsed_ms"] += 1
        with self.assertRaisesRegex(subject.EvidenceLoadError, "do not match"):
            subject._cross_bind_archives(f2, f3)

    def test_foreign_lease_stale_cycle_and_admission_digest_fail(self):
        foreign = subject.EvidenceExpectation(self.cycle, "f" * 16,
                                              self.expectation.admission_receipt)
        with self.assertRaises(subject.EvidenceLoadError):
            subject.load_accepted_evidence(
                foreign, now_epoch=self.now, now_minute=self.now_minute,
                paths=self.paths, inventory=lambda: self.inventory,
                resolve=lambda volid: self.resolved[volid],
                required_uid=os.geteuid())
        with self.assertRaises(subject.EvidenceLoadError):
            self.load(now_epoch=self.now + 86400)
        bad = subject.EvidenceExpectation(self.cycle, self.nonce,
                                          ADMISSION_PREFIX + "0" * 64)
        with self.assertRaises(subject.EvidenceLoadError):
            subject.load_accepted_evidence(
                bad, now_epoch=self.now, now_minute=self.now_minute,
                paths=self.paths, inventory=lambda: self.inventory,
                resolve=lambda volid: self.resolved[volid],
                required_uid=os.geteuid())

    def test_weak_custody_and_archive_identity_drift_fail(self):
        self.paths.f4.chmod(0o644)
        with self.assertRaises(subject.EvidenceLoadError):
            self.load()
        self.paths.f4.chmod(0o600)
        self.archive.write_bytes(b"changed")
        with self.assertRaises(subject.EvidenceLoadError):
            self.load()


if __name__ == "__main__":
    unittest.main()
