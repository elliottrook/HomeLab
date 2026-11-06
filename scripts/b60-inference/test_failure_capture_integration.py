"""Exercise the exact next live transport and host retention with fake IO."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import signal
import sys
import unittest
from unittest.mock import patch
import urllib.error

P = Path(__file__).parent / 'model-trial-20261106-r3'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, P / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Response:
    status = 200
    def __init__(self, value):
        self.raw = json.dumps(value).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, maximum): return self.raw[:maximum]


def answer(finish='stop', content='42'):
    return {'choices': [{'finish_reason': finish,
            'message': {'content': content, 'reasoning_content': 'synthetic hidden'}}],
            'usage': {'completion_tokens': 1024}}


class Integration(unittest.TestCase):
    def setUp(self):
        self.g = load('next_guest', 'guest_requests.py')
        self.m = load('next_model', 'model_trial.py')
        self.modules = patch.dict(sys.modules, {'guest_requests': self.g})
        self.modules.start()
    def tearDown(self): self.modules.stop()
    def packet(self, results):
        calls = []
        class Opener:
            def open(self, req, timeout):
                calls.append((req, timeout))
                value = results[len(calls)-1]
                if isinstance(value, BaseException): raise value
                return Response(value)
        times = iter([0, 1, 2, 3])
        with patch.object(self.g, 'capture', side_effect=lambda transport, clock:
                __import__('request_failure_capture').capture(transport, clock, source_path=P/'legacy_requests.py')):
            value = self.g.run(read_key=lambda: 'synthetic-key', opener=Opener(), clock=lambda: next(times))
        return value, calls
    def test_failed_second_result_retained_before_failure(self):
        packet, calls = self.packet([answer(), answer('length', '')])
        writes = []
        class Store:
            def write(self, name, data, **kw): writes.append((name, data, kw))
        result = self.m.retain_request_packet(json.dumps(packet), Store())
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(writes[0][0], 'model-result.json')
        self.assertTrue(writes[0][2]['immutable'])
        self.assertEqual(result['records'][1]['outcome'], 'token_limit')
        self.assertTrue(result['records'][0]['arithmetic_exact'])
        self.assertEqual(len(calls), 2)
        self.assertNotIn('synthetic-key', json.dumps(result))
        self.assertNotIn('synthetic hidden', json.dumps(result))
    def test_fixed_payload_endpoint_and_timeout(self):
        _, calls = self.packet([answer(), answer()])
        for req, timeout in calls:
            self.assertEqual(req.full_url, self.g.ENDPOINT)
            self.assertEqual(timeout, 60)
            self.assertEqual(json.loads(req.data)['max_tokens'], 1024)
    def test_http_error_captured_without_body_or_retry(self):
        error = urllib.error.HTTPError(self.g.ENDPOINT, 302, 'secret', {}, None)
        packet, calls = self.packet([error])
        self.assertEqual(packet['records'][0]['http_status'], 302)
        self.assertEqual(packet['records'][0]['outcome'], 'http_error')
        self.assertEqual(len(calls), 1)
        self.assertIsNone(self.g.NoRedirect().redirect_request(None, None, None, None, None, None))
    def test_alarm_is_restored_on_failure(self):
        before = signal.getsignal(signal.SIGALRM)
        self.packet([TimeoutError()])
        self.assertEqual(signal.getsignal(signal.SIGALRM), before)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0], 0)
    def test_url_timeout_is_bounded_timeout_metadata(self):
        packet, calls = self.packet([urllib.error.URLError(TimeoutError('synthetic private error'))])
        self.assertEqual(packet['records'][0]['outcome'], 'timeout')
        self.assertEqual(len(calls), 1)
        self.assertNotIn('synthetic private', json.dumps(packet))
    def test_actual_cli_preserves_failed_packet_with_zero_exit(self):
        packet, _ = self.packet([answer(), answer('length', '')])
        output = io.StringIO()
        with patch.object(sys, 'argv', ['capture', '--run-authorized']), \
             patch.object(self.g, 'run', return_value=packet), contextlib.redirect_stdout(output):
            self.assertEqual(self.g.main(), 0)
        self.assertEqual(json.loads(output.getvalue()), packet)
    def test_cli_without_switch_does_not_read_key_or_call(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['capture']), \
             patch.object(self.g, 'run', side_effect=AssertionError('must remain inert')), \
             contextlib.redirect_stdout(output):
            self.assertEqual(self.g.main(), 0)
        self.assertEqual(json.loads(output.getvalue()), {'state': 'disabled', 'requests': 0})
    def test_arbitrary_fields_rejected_before_store(self):
        packet, _ = self.packet([answer(), answer()])
        packet['secret'] = 'must not persist'
        class Store:
            def write(self, *args, **kw): raise RuntimeError('write reached')
        with self.assertRaises(AssertionError):
            self.m.retain_request_packet(json.dumps(packet), Store())
    def test_store_failure_cannot_be_success(self):
        packet, _ = self.packet([answer(), answer()])
        class Store:
            def write(self, *args, **kw): raise OSError('fake storage failure')
        with self.assertRaises(OSError):
            self.m.retain_request_packet(json.dumps(packet), Store())
    def test_news_requires_exact_peer_terminal_and_recovery_margin(self):
        n = load('next_news', 'news_xpu_boundary.py')
        row = {'booking_id': n.NEWS, 'owner': 'aster-news-video',
               'workload': 'aster-news-video-musetalk-xpu-smoke-v1',
               'state': 'complete', 'finished_epoch': 1000}
        self.assertTrue(n.peer_released(row, 1900))
        self.assertFalse(n.peer_released(row, 1899))
        for key, value in [('state', 'claimed'), ('owner', 'other-owner'),
                           ('booking_id', 'other-booking'), ('finished_epoch', None)]:
            self.assertFalse(n.peer_released(dict(row, **{key: value}), 1900))


if __name__ == '__main__': unittest.main()
