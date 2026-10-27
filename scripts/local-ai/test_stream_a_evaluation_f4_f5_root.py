import os
import tempfile
import unittest
from pathlib import Path

from lease_watchdog import EXPECTED_SCHEDULES, Observation
from stream_a_evaluation_f4_f5_root import (
    CollectedSources, EvidencePaths, RootTransactionError, produce,
)


class RootF4F5Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = EvidencePaths(
            f2_root=self._dir(root / "f2"),
            f3=self._dir(root / "f3") / "receipt.json",
            f4=self._dir(root / "f4") / "receipt.json",
            f5=self._dir(root / "runtime") / "f5-observation.json",
            admission=root / "runtime" / "admission.json",
            whole_host_root=self._dir(root / "whole"),
            runtime_root=root / "runtime",
        )
        self.uid = os.geteuid()

    def tearDown(self):
        self.temp.cleanup()

    def _dir(self, path):
        path.mkdir(mode=0o700); path.chmod(0o700)
        return path

    def sources(self, *, unchanged=True):
        return CollectedSources(
            cycle_date="2026-10-27", observed_epoch=1793095500,
            observed_minute=190, f2_bytes=b'{"f2":"fixed"}\n',
            f3_bytes=b'{"f3":"fixed"}',
            backup_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            observation=Observation(
                190, False, True, True, True, True, EXPECTED_SCHEDULES,
                True, True, True, True, True),
            lxc110_mirror_identity="truenas-task-3:fixed:123:456",
            unchanged=lambda: unchanged,
        )

    def run_produce(self, source=None):
        source = source or self.sources()
        return produce(
            paths=self.paths, clock=lambda: source.observed_epoch,
            nonce_factory=lambda: "0123456789abcdef",
            collector=lambda **_kwargs: source, required_uid=self.uid)

    def test_success_publishes_exact_write_once_set(self):
        result = self.run_produce()
        self.assertEqual(self.paths.f4.read_bytes(), result.f4_bytes)
        self.assertEqual(self.paths.f5.read_bytes(), result.f5_bytes)
        self.assertEqual(self.paths.admission.read_bytes(), result.admission_bytes)
        for path in (self.paths.f4, self.paths.f5, self.paths.admission):
            info = path.stat()
            self.assertEqual(info.st_mode & 0o777, 0o600)
            self.assertEqual(info.st_nlink, 1)

    def test_preexisting_target_rejects_before_any_write(self):
        self.paths.f5.write_text("foreign")
        self.paths.f5.chmod(0o600)
        with self.assertRaisesRegex(RootTransactionError, "already exists"):
            self.run_produce()
        self.assertFalse(self.paths.f4.exists())
        self.assertFalse(self.paths.admission.exists())
        self.assertEqual(self.paths.f5.read_text(), "foreign")

    def test_source_drift_rejects_before_publication(self):
        with self.assertRaisesRegex(RootTransactionError, "changed"):
            self.run_produce(self.sources(unchanged=False))
        self.assertFalse(self.paths.f4.exists())
        self.assertFalse(self.paths.f5.exists())
        self.assertFalse(self.paths.admission.exists())

    def test_symlink_target_and_weak_parent_fail_closed(self):
        self.paths.f4.symlink_to(self.paths.f3)
        with self.assertRaises(RootTransactionError):
            self.run_produce()
        self.paths.f4.unlink()
        self.paths.f4.parent.chmod(0o755)
        with self.assertRaisesRegex(RootTransactionError, "custody"):
            self.run_produce()
        self.assertFalse(self.paths.admission.exists())

    def test_mid_publish_failure_removes_partial_set(self):
        # Making the final target a directory passes lexists rejection, so use
        # a patched hard-link operation to model an I/O failure after F4.
        original = os.link
        calls = 0
        def failing_link(source, target, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic publish failure")
            return original(source, target, **kwargs)
        from unittest.mock import patch
        with patch("stream_a_evaluation_f4_f5_root.os.link", side_effect=failing_link):
            with self.assertRaises(OSError):
                self.run_produce()
        self.assertFalse(self.paths.f4.exists())
        self.assertFalse(self.paths.f5.exists())
        self.assertFalse(self.paths.admission.exists())


if __name__ == "__main__":
    unittest.main()
