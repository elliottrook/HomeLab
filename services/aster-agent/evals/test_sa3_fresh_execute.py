import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from sa3_fresh_execute import NoRedirect
from test_sa3_fresh_package import fixture


class ExecuteTests(unittest.TestCase):
    def test_label_free_dry_run_without_credentials(self):
        bundle, manifest = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'cases.json').write_text(json.dumps(bundle))
            (root/'manifest.json').write_text(json.dumps(manifest))
            cmd = [sys.executable, str(Path(__file__).with_name('sa3_fresh_execute.py')),
                   '--cases', str(root/'cases.json'), '--manifest', str(root/'manifest.json'),
                   '--expected-release-digest', manifest['release_digest']]
            result = subprocess.run(cmd, env={}, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['sessions'], 40)
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['cases.json', 'manifest.json'])
            cmd[-1] = '0'*64
            self.assertNotEqual(subprocess.run(cmd, env={}, capture_output=True).returncode, 0)

    def test_authenticated_redirect_is_never_followed(self):
        req = urllib.request.Request('http://example.invalid', headers={'Authorization': 'Bearer fixture'})
        with self.assertRaises(urllib.error.HTTPError):
            NoRedirect().redirect_request(req, None, 302, 'moved', {}, 'https://other.invalid')


if __name__ == '__main__': unittest.main()
