"""Disposable-dir proof for every partial staging boundary; no host access."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import host_exclusion_disabled_rollback_v2 as candidate


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PartialRollbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "state"
        self.root.mkdir(mode=0o700)
        self.l = Path(self.tmp.name) / "whole"
        self.a = Path(self.tmp.name) / "app"
        self.l.mkdir()
        self.a.mkdir()
        self.paths = [
            self.l / "host_exclusion.py", self.a / "host_exclusion.py",
            self.l / "retained_archive_timing_observer.py",
            self.l / "retained_archive_producer_candidate.py",
            self.l / "lease_controller_candidate.py",
            self.l / "full_stop_acquire_candidate.py",
            self.a / "application_b60_controller.py",
        ]
        self.old_bytes = {p: ("old-" + str(i)).encode() for i, p in enumerate(self.paths[3:], 3)}
        self.new_bytes = {p: ("new-" + str(i)).encode() for i, p in enumerate(self.paths)}
        self.checkpoint = self.root / "host-exclusion-v2-checkpoint.test"
        self.checkpoint.mkdir(mode=0o700)
        for path, raw in self.old_bytes.items():
            path.write_bytes(raw)
            label = ("L-" if path.parent == self.l else "A-") + path.name
            (self.checkpoint / label).write_bytes(raw)
        self.patches = [
            patch.object(candidate, "ROOT", self.root),
            patch.object(candidate, "CHECKPOINT_OWNER_UID", os.getuid()),
            patch.object(candidate, "L", self.l),
            patch.object(candidate, "A", self.a),
            patch.object(candidate, "OLD", {p: digest(raw) for p, raw in self.old_bytes.items()}),
            patch.object(candidate, "NEW", {p: digest(raw) for p, raw in self.new_bytes.items()}),
            patch.object(candidate, "STATE", (self.root / "lease.json", self.root / "lease.lock")),
            patch.object(candidate.os, "geteuid", return_value=0),
            patch.object(candidate.os, "fchown"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_every_partial_stage_restores_all_originals(self):
        for count in range(len(self.paths) + 1):
            with self.subTest(count=count):
                for path in self.paths[:count]:
                    path.write_bytes(self.new_bytes[path])
                result = candidate.rollback()
                self.assertEqual(result["state"], "rolled-back")
                for path, raw in self.old_bytes.items():
                    self.assertEqual(path.read_bytes(), raw)
                for path in self.paths[:3]:
                    self.assertFalse(os.path.lexists(path))

    def test_symlink_and_unknown_bytes_refuse_without_mutation(self):
        target = self.root / "target"
        target.write_bytes(self.new_bytes[self.paths[0]])
        self.paths[0].symlink_to(target)
        with self.assertRaisesRegex(RuntimeError, "added file differs"):
            candidate.rollback()
        self.assertTrue(self.paths[0].is_symlink())
        self.paths[0].unlink()
        self.paths[3].write_bytes(b"unexpected")
        with self.assertRaisesRegex(RuntimeError, "replacement differs"):
            candidate.rollback()
        self.assertEqual(self.paths[3].read_bytes(), b"unexpected")

    def test_lease_and_checkpoint_drift_refuse(self):
        (self.root / "lease.json").write_text("active")
        with self.assertRaisesRegex(RuntimeError, "lease state"):
            candidate.rollback()
        (self.root / "lease.json").unlink()
        (self.checkpoint / ("L-" + self.paths[3].name)).write_bytes(b"drift")
        with self.assertRaisesRegex(RuntimeError, "checkpoint file changed"):
            candidate.rollback()


if __name__ == "__main__":
    unittest.main()
