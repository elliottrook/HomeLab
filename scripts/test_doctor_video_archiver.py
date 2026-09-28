"""Exercise the actual Doctor function with synthetic remote output on macOS Bash."""
import os
from pathlib import Path
import subprocess
import time
import unittest

SOURCE = Path(__file__).with_name('doctor.sh').read_text()
FUNCTION = SOURCE[SOURCE.index('check_video_archiver() {'):SOURCE.index('check_jellyfin_integrity() {')]


class VideoArchiverDoctorTests(unittest.TestCase):
    def run_check(self, output):
        script = '''set -u
ssh() { cat >/dev/null; printf '%s\\n' "$FIXTURE"; }
pass() { printf 'PASS %s\\n' "$1"; }
warn() { printf 'WARN %s\\n' "$1"; }
fail() { printf 'FAIL %s\\n' "$1"; }
''' + FUNCTION + '\ncheck_video_archiver\necho CHECK_COMPLETED\n'
        result = subprocess.run(['/bin/bash', '-c', script], text=True, capture_output=True,
                                env=dict(os.environ, FIXTURE=output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CHECK_COMPLETED', result.stdout)
        return result.stdout

    def fixture(self, failed=1):
        return f'log_path=/fixture/run.jsonl\nmtime={int(time.time())}\ndry_run=0\nfound=112\nsucceeded=110\nfailed={failed}\n'

    def test_failure_without_details_does_not_abort_doctor(self):
        output = self.run_check(self.fixture())
        self.assertIn('FAIL video-archiver: 1 failure(s)', output)
        self.assertIn('see log: /fixture/run.jsonl', output)

    def test_failure_with_spaces_preserves_detail(self):
        output = self.run_check(self.fixture() + 'error_entry=Test movie.mkv|||output exceeds cap\n')
        self.assertIn('Test movie.mkv: output exceeds cap', output)

    def test_success(self):
        self.assertIn('PASS video-archiver clean run', self.run_check(self.fixture(0)))

    def test_missing_summary(self):
        self.assertIn('WARN video-archiver has no run log yet', self.run_check('no_summary=1'))

    def test_scan_failure_is_reported_even_with_successful_files(self):
        import json
        import tempfile
        start = FUNCTION.index('python3 -c "') + len('python3 -c "')
        end = FUNCTION.index('\n"\nREMOTE', start)
        code = FUNCTION[start:end].replace('\\"', '"')
        for summary_count in (0, 1):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl') as f:
                f.write(json.dumps({'event': 'jellyfin_scan_failed', 'error': 'HTTP 401'}) + '\n')
                f.write(json.dumps({'event': 'summary', 'mode': 'EXECUTE', 'failed': 0,
                                   'scan_failed': summary_count}) + '\n')
                f.flush()
                result = subprocess.run(['python3', '-c', code.replace('$latest', f.name)],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('failed=1', result.stdout)
                self.assertIn('error_entry=Jellyfin scan|||HTTP 401', result.stdout)
                output = self.run_check(self.fixture(0) + result.stdout)
                self.assertIn('FAIL video-archiver: 1 failure(s)', output)
                self.assertNotIn('PASS', output)

    def test_live_and_legacy_log_schemas(self):
        # Execute the embedded Python producer itself with a temporary JSONL.
        import json
        import tempfile
        start = FUNCTION.index('python3 -c "') + len('python3 -c "')
        end = FUNCTION.index('\n"\nREMOTE', start)
        code = FUNCTION[start:end].replace('\\"', '"')
        for summary, failure in [
            ({'mode': 'EXECUTE', 'considered': 112, 'replaced': 110, 'failed': 1},
             {'event': 'file', 'status': 'failed', 'path': '/fixture/Test movie.mkv', 'reason': 'output exceeds cap'}),
            ({'dry_run': False, 'total_candidates_found': 112, 'succeeded': 110, 'failed': 1},
             {'event': 'error', 'title': 'Test movie.mkv', 'error': 'output exceeds cap'}),
        ]:
            with self.subTest(summary=summary), tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl') as f:
                f.write(json.dumps(failure) + '\n' + json.dumps(dict(summary, event='summary')) + '\n')
                f.flush()
                result = subprocess.run(['python3', '-c', code.replace('$latest', f.name)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                for line in ('dry_run=0', 'found=112', 'succeeded=110', 'failed=1', 'error_entry=Test movie.mkv|||output exceeds cap'):
                    self.assertIn(line, result.stdout)


if __name__ == '__main__':
    unittest.main()
