import json
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest import mock
from sa3_fresh_execute import (
    MAX_HTTP_BYTES,
    MAX_INPUT_BYTES,
    NoRedirect,
    build_local_opener,
    decode_unique_json,
    load_bounded_json,
    parse_processing_metric,
    read_bounded,
)
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

    def test_local_service_transport_ignores_environment_proxies(self):
        with mock.patch.dict('os.environ', {'HTTP_PROXY': 'http://proxy.invalid:3128'}):
            opener = build_local_opener()
        self.assertFalse(any(isinstance(handler, urllib.request.ProxyHandler)
                             for handler in opener.handlers))

    def test_local_service_response_is_bounded_before_json_parsing(self):
        self.assertEqual('{"ok":true}', read_bounded(io.BytesIO(b'{"ok":true}')))
        with self.assertRaisesRegex(ValueError, 'bounded envelope'):
            read_bounded(io.BytesIO(b'x' * (MAX_HTTP_BYTES + 1)))
        self.assertEqual({'ok': True}, decode_unique_json('{"ok":true}'))
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            decode_unique_json('{"ok":true,"ok":false}')
        for value in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value), self.assertRaisesRegex(
                    ValueError, 'non-JSON numeric constant'):
                decode_unique_json('{"value":' + value + '}')

    def test_evaluation_inputs_are_bounded_and_reject_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text('{"ok":true}')
            self.assertEqual({'ok': True}, load_bounded_json(path))
            path.write_text('{"ok":true,"ok":false}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                load_bounded_json(path)
            with path.open('wb') as stream:
                stream.truncate(MAX_INPUT_BYTES + 1)
            with self.assertRaisesRegex(ValueError, 'bounded envelope'):
                load_bounded_json(path)

    def test_readiness_metric_is_single_finite_and_nonnegative(self):
        self.assertEqual(
            0.0,
            parse_processing_metric(
                '# HELP fixture\nllamacpp:requests_processing{model="fixture"} 0\n'
            ),
        )
        for raw in (
            '',
            'llamacpp:requests_processing 0\nllamacpp:requests_processing 0\n',
            'llamacpp:requests_processing NaN\n',
            'llamacpp:requests_processing +Inf\n',
            'llamacpp:requests_processing -1\n',
            'llamacpp:requests_processing not-a-number\n',
        ):
            with self.subTest(raw=raw), self.assertRaisesRegex(
                    ValueError, 'requests-processing metric'):
                parse_processing_metric(raw)


if __name__ == '__main__': unittest.main()
