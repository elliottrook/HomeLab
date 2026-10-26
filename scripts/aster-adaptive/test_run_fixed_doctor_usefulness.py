import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_fixed_doctor_usefulness as runner


ROOT = Path(__file__).parent
FIXTURE = ROOT / "fixtures" / "fixed-doctor-usefulness-v1.json"
PROFILE = ROOT / "fixtures" / "fixed-doctor-usefulness-profile-v1.json"


def key_pipe(raw=b"test-only-local-key"):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, raw)
    os.close(write_fd)
    return read_fd


class RunFixedDoctorUsefulnessTests(unittest.TestCase):
    def test_descriptor_key_and_exact_profile_feed_journaled_capture(self):
        descriptor = key_pipe()
        observed = {}

        def fake_capture(fixture_raw, profile_sha, invoke, directory, **kwargs):
            observed.update(
                fixture_sha=hashlib.sha256(fixture_raw).hexdigest(),
                profile_sha=profile_sha,
                directory=directory,
                kwargs=kwargs,
                answer=invoke({
                    "id": "fd-use-01", "question": "question",
                    "observation": {}, "expected": {},
                }, timeout_s=60),
            )
            return {"planned": 8, "completed": 8, "failed": 0,
                    "not_attempted": 0, "raw_attempts_sha256": "a" * 64,
                    "attempt_journal_sha256": "b" * 64,
                    "profile_sha256": profile_sha}

        with tempfile.TemporaryDirectory() as root, \
                patch.object(runner.adapter, "invoke", return_value="bounded answer") as invoke, \
                patch.object(runner.journaled, "capture_journaled", side_effect=fake_capture):
            try:
                result = runner.run(FIXTURE, PROFILE, Path(root) / "run", descriptor)
            finally:
                os.close(descriptor)
        self.assertEqual(8, result["completed"])
        self.assertEqual(runner.PROFILE_SHA256, observed["profile_sha"])
        self.assertEqual(600, observed["kwargs"]["max_wall_s"])
        self.assertEqual(60, observed["kwargs"]["min_call_s"])
        invoke.assert_called_once()
        self.assertEqual(60, invoke.call_args.kwargs["timeout"])

    def test_profile_drift_fails_before_key_read_or_capture(self):
        with tempfile.TemporaryDirectory() as root:
            changed = Path(root) / "profile.json"
            changed.write_bytes(PROFILE.read_bytes() + b"\n")
            with patch.object(runner, "read_key_fd") as read_key, \
                    patch.object(runner.journaled, "capture_journaled") as capture:
                with self.assertRaisesRegex(ValueError, "profile digest"):
                    runner.run(FIXTURE, changed, Path(root) / "run", 99)
            read_key.assert_not_called()
            capture.assert_not_called()

    def test_invalid_descriptor_and_secret_fail_closed(self):
        for descriptor in (-1, 0, 2):
            with self.subTest(descriptor=descriptor):
                with self.assertRaises(ValueError):
                    runner.read_key_fd(descriptor)
        descriptor = key_pipe(b"bad\nkey")
        try:
            with self.assertRaises(ValueError):
                runner.read_key_fd(descriptor)
        finally:
            os.close(descriptor)

    def test_cli_requires_explicit_execute_gate(self):
        descriptor = key_pipe()
        try:
            with self.assertRaises(SystemExit):
                runner.main([
                    "--fixture", str(FIXTURE),
                    "--profile", str(PROFILE),
                    "--output-directory", "/tmp/not-created",
                    "--key-fd", str(descriptor),
                ])
        finally:
            os.close(descriptor)


if __name__ == "__main__":
    unittest.main()
