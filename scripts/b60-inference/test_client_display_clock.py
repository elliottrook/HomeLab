import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from client_display_clock import ClientDisplayClock

ROOT = Path(__file__).resolve().parents[1] / 'aster-adaptive'


def owned(name, pin):
    path = ROOT / (name + '.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
        raise ValueError('owner clock source drift')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


gateway = owned('aster_asgi_clock', 'e7f8240fc38a62772ac2d7e4e9461ee8f3be21580885d9dfc0cab40fe1919305')
joiner = owned('join_aster_clock', '38318b894be89525be166a19ab1bd933966dfddf12ca060386ff0a2768fc694b')
ID = 'a' * 32


class ClockTests(unittest.TestCase):
    def clock(self):
        return ClientDisplayClock(clock=iter([1000000, 46000000]).__next__)

    def test_acceptance_to_display_not_response_arrival(self):
        clock = self.clock(); clock.response_identity(ID, 200)
        row = clock.finish(terminal_displayed=True)
        self.assertEqual(row['accepted_to_displayed_ms'], 45)
        self.assertEqual(set(row), joiner.CLIENT_FIELDS)
        self.assertNotIn('useful_answer_ms', row)

    def test_no_identity_cannot_be_joined_or_invented(self):
        row = self.clock().finish(terminal_displayed=False)
        self.assertIsNone(row['observation_id'])
        self.assertIsNone(row['accepted_to_displayed_ms'])

    def test_no_double_finish_or_changed_identity(self):
        clock = self.clock(); clock.response_identity(ID, 200)
        with self.assertRaises(ValueError): clock.response_identity('b' * 32, 200)
        clock.finish(terminal_displayed=True)
        with self.assertRaises(ValueError): clock.finish(terminal_displayed=True)

    def test_invalid_ids_and_boolean_status_rejected(self):
        for identity, status in [('request/private/text', 200), (ID, True), (ID, 999)]:
            with self.assertRaises(ValueError): self.clock().response_identity(identity, status)

    def test_backward_clock_rejected(self):
        clock = ClientDisplayClock(clock=iter([100, 0]).__next__)
        with self.assertRaises(ValueError): clock.finish(terminal_displayed=True)

    def run_gateway(self, *, status=200, display=True, interrupted=False):
        sink = []; client = self.clock()

        async def app(scope, receive, send):
            await send({'type': 'http.response.start', 'status': status, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'FAKE synthetic text', 'more_body': True})
            if not interrupted:
                await send({'type': 'http.response.body', 'body': b'', 'more_body': False})

        async def send(message):
            if message['type'] == 'http.response.start':
                headers = dict(message['headers'])
                client.response_identity(headers[b'x-aster-observation-id'].decode(), message['status'])

        async def receive(): return {'type': 'http.request', 'body': b''}
        asyncio.run(gateway.ASGIResponseClock(app, sink, id_factory=lambda: ID)(
            {'type': 'http', 'path': '/v1/chat/completions'}, receive, send))
        return joiner.join(client.finish(terminal_displayed=display), sink[0])

    def test_fake_full_path_joins_without_usefulness_claim(self):
        result = self.run_gateway()
        self.assertTrue(result['terminal_joined'])
        self.assertEqual(result['client_terminal_display_ms'], 45)
        self.assertIsNone(result['useful_answer_ms'])
        self.assertNotIn('FAKE synthetic text', json.dumps(result))

    def test_displayed_error_keeps_error_status_not_quality_pass(self):
        result = self.run_gateway(status=502)
        self.assertEqual(result['http_status'], 502)
        self.assertIsNone(result['useful_answer_ms'])

    def test_partial_stream_is_censored(self):
        result = self.run_gateway(display=False, interrupted=True)
        self.assertTrue(result['censored'])
        self.assertIsNone(result['gateway_terminal_ms'])

    def test_gateway_complete_but_client_not_displayed_is_censored(self):
        result = self.run_gateway(display=False)
        self.assertTrue(result['censored'])
        self.assertIsNone(result['client_terminal_display_ms'])
        self.assertIsNotNone(result['gateway_terminal_ms'])


if __name__ == '__main__': unittest.main()
