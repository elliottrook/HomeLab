import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import m3_k2_sealed_bundle_contract as contract
import m3_k2_sealed_runtime_inactive_install as candidate
import test_m3_k2_sealed_bundle_contract as fixture_builder


class K2SealedRuntimeInactiveInstallTests(unittest.TestCase):
    def fixture(self):
        raw, pins = fixture_builder.fixture(
            {"one.py": b"one\n", "two.py": b"two\n"})
        return raw, pins

    def patched(self, raw, pins):
        return (mock.patch.object(contract, "SOURCE_PINS", pins),
                mock.patch.object(contract, "BUNDLE_SHA256",
                                  hashlib.sha256(raw).hexdigest()))

    def test_exact_absent_install_and_rollback(self):
        raw, pins = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / "runtime"; checkpoint = root / "cp"
            first, second = self.patched(raw, pins)
            with first, second:
                result = candidate.install(target, checkpoint, raw)
                self.assertEqual("installed-inactive", result["state"])
                self.assertEqual(3, result["files"])
                self.assertEqual(0o700, target.stat().st_mode & 0o777)
                self.assertTrue(all((item.stat().st_mode & 0o777) == 0o600
                                    for item in target.iterdir()))
                result = candidate.rollback(target, checkpoint, raw)
                self.assertEqual("rolled-back", result["state"])
                self.assertFalse(target.exists()); self.assertTrue(checkpoint.exists())

    def test_existing_target_or_checkpoint_fails_closed(self):
        raw, pins = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / "runtime"; checkpoint = root / "cp"
            target.mkdir()
            first, second = self.patched(raw, pins)
            with first, second, self.assertRaisesRegex(candidate.InstallError, "TARGET_EXISTS"):
                candidate.install(target, checkpoint, raw)
            target.rmdir(); checkpoint.mkdir()
            first, second = self.patched(raw, pins)
            with first, second, self.assertRaisesRegex(candidate.InstallError,
                                                        "CHECKPOINT_EXISTS"):
                candidate.install(target, checkpoint, raw)

    def test_changed_install_refuses_rollback_and_retains_target(self):
        raw, pins = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / "runtime"; checkpoint = root / "cp"
            first, second = self.patched(raw, pins)
            with first, second:
                candidate.install(target, checkpoint, raw)
                (target / "one.py").write_bytes(b"changed\n")
                os.chmod(target / "one.py", 0o600)
                with self.assertRaisesRegex(candidate.InstallError, "INSTALLED_IDENTITY"):
                    candidate.rollback(target, checkpoint, raw)
                self.assertTrue(target.exists()); self.assertTrue(checkpoint.exists())

    def test_cli_is_inert_without_explicit_operation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = root / "bundle"; bundle.write_bytes(b"not-read")
            result = subprocess.run(
                (sys.executable, "-B", candidate.__file__, "--bundle", str(bundle),
                 "--target", str(root / "target"), "--checkpoint", str(root / "cp")),
                capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)
        self.assertIn('"state": "source-only"', result.stdout)


if __name__ == "__main__":
    unittest.main()
