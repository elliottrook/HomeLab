"""Regression tests for the content-silent EPUB narration Doctor check."""

import os
from pathlib import Path
import subprocess
import unittest


SOURCE = Path(__file__).with_name("doctor.sh").read_text()
CHECK = SOURCE[
    SOURCE.index("check_epub_narration() {") : SOURCE.index("# Flags a recurrence")
]


class DoctorEpubNarrationTests(unittest.TestCase):
    def run_check(self, fixture):
        script = """set -u
ssh() { cat >/dev/null; printf '%s\n' "$FIXTURE"; }
pass() { printf 'PASS %s\n' "$1"; }
warn() { printf 'WARN %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; }
""" + CHECK + "\ncheck_epub_narration\n"
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            text=True,
            capture_output=True,
            env=dict(os.environ, FIXTURE=fixture),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    @staticmethod
    def fixture(**changes):
        values = {
            "source_mount": "192.168.20.40:/mnt/Media/media/books",
            "source_options": "ro,nosuid,nodev,noexec",
            "output_mount": "192.168.20.40:/mnt/Media/AsterReader",
            "output_options": "rw,nosuid,nodev,noexec",
            "timer": "active",
            "worker": "inactive",
            "limits": "3s,3221225472,15,3,",
            "monitor_state": "healthy",
            "source_count": "167",
            "queued": "167",
            "ready": "0",
            "failed": "0",
            "status_age": "60",
        }
        values.update(changes)
        return "\n".join(f"{key}={value}" for key, value in values.items())

    def test_accepts_healthy_monitor_with_intentionally_inactive_worker(self):
        self.assertIn("PASS EPUB narration monitor healthy", self.run_check(self.fixture()))

    def test_rejects_stale_status(self):
        self.assertIn("FAIL EPUB narration monitor is disabled, stale or invalid", self.run_check(self.fixture(status_age="172801")))

    def test_rejects_source_mount_without_read_only_option(self):
        self.assertIn("FAIL EPUB narration storage mounts", self.run_check(self.fixture(source_options="rw,nosuid,nodev")))

    def test_warns_on_bounded_failures_without_exposing_identifiers(self):
        output = self.run_check(self.fixture(queued="160", failed="7"))
        self.assertIn("WARN EPUB narration monitor healthy; queued=160 ready=0 failed=7", output)
        self.assertNotIn("title", output.lower())


if __name__ == "__main__":
    unittest.main()
