"""Doctor reports fresh capacity audits and actionable pressure cleanly."""

import os
import subprocess
import time
import unittest
from pathlib import Path


source = Path(__file__).with_name('doctor.sh').read_text()
function = source[source.index('check_media_retention_audit() {'):source.index('check_video_archiver() {')]


class MediaRetentionDoctorTests(unittest.TestCase):
    def run_check(self, fixture):
        script = '''set -u
ssh() { cat >/dev/null; printf '%s\\n' "$FIXTURE"; }
pass() { printf 'PASS %s\\n' "$1"; }
warn() { printf 'WARN %s\\n' "$1"; }
fail() { printf 'FAIL %s\\n' "$1"; }
''' + function + '\ncheck_media_retention_audit\n'
        result = subprocess.run(['/bin/bash', '-c', script], text=True,
                                capture_output=True, env=dict(os.environ, FIXTURE=fixture))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def fixture(self, cap=41, reclaimable=0, age_hours=1):
        stamp = int(time.time()) - age_hours * 3600
        return f'mtime={stamp}\ncap={cap}\nreclaimable={reclaimable}\nsnapshot_covered=7397\n'

    def test_healthy_audit(self):
        self.assertIn('PASS media retention audit fresh', self.run_check(self.fixture()))

    def test_missing_and_stale_audit(self):
        self.assertIn('WARN media retention audit has no status yet', self.run_check('missing=1'))
        self.assertIn('WARN media retention audit is stale', self.run_check(self.fixture(age_hours=40)))

    def test_trigger_with_no_reclaimable_files_fails(self):
        self.assertIn('FAIL Media pool 60% full', self.run_check(self.fixture(cap=60)))

    def test_urgent_threshold_fails_even_with_candidates(self):
        self.assertIn('FAIL Media pool 62% full',
                      self.run_check(self.fixture(cap=62, reclaimable=50)))

    def test_trigger_with_candidates_warns_until_controller_enabled(self):
        self.assertIn('WARN Media pool 60% full',
                      self.run_check(self.fixture(cap=60, reclaimable=50)))


if __name__ == '__main__':
    unittest.main()
