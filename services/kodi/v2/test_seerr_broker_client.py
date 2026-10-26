import json
import tempfile
import unittest
from pathlib import Path

from seerr_broker_client import BrokerUnavailable, RequestWriter, candidate_page
from seerr_request_model import candidate, propose


def raw(kind='movie', media_id=123):
    return {'schema': 2, 'identity': f'seerr:{kind}:{media_id}',
            'media_type': kind, 'media_id': media_id, 'title': 'Example',
            'year': '2026', 'overview': 'Synthetic.', 'poster': '/p.jpg',
            'backdrop': '/b.jpg',
            'owned': False, 'availability': 'unknown', 'request_id': None,
            'request_state': 'none',
            'seasons': [1, 2] if kind == 'tv' else []}


def reply(identity='seerr:movie:123'):
    return {'schema': 1, 'candidate_id': identity, 'request_id': 77,
            'state': 'pending', 'duplicate': False}


class BrokerClientTests(unittest.TestCase):
    def test_candidate_page_is_bounded_exact_and_unique(self):
        page = {'schema': 1, 'query': 'Example', 'candidates': [raw()]}
        self.assertEqual(candidate_page(page, 'Example')[0].identity,
                         'seerr:movie:123')
        page['candidates'] = [raw(), raw()]
        with self.assertRaisesRegex(BrokerUnavailable, 'duplicate'):
            candidate_page(page, 'Example')
        page['candidates'] = [raw(media_id=index+1) for index in range(25)]
        with self.assertRaisesRegex(BrokerUnavailable, 'schema'):
            candidate_page(page, 'Example')
        for query in (' Example', '', 'x'*101):
            with self.subTest(query=query), self.assertRaisesRegex(
                    BrokerUnavailable, 'query-invalid'):
                candidate_page({'schema': 1, 'query': query, 'candidates': []}, query)

    def test_success_is_journalled_and_never_sent_twice(self):
        calls = []
        with tempfile.TemporaryDirectory() as folder:
            writer = RequestWriter(folder, lambda payload: calls.append(payload) or reply())
            ready = propose(candidate(raw()), confirmed=True)
            self.assertEqual(writer.submit(ready)['request_id'], 77)
            self.assertEqual(writer.submit(ready)['request_id'], 77)
            self.assertEqual(len(calls), 1)
            record = json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertEqual(record['status'], 'committed')
            self.assertNotIn('title', record)
            self.assertEqual(next(Path(folder).glob('*.json')).stat().st_mode & 0o777,
                             0o600)

    def test_transport_or_invalid_response_is_sticky_uncertainty(self):
        for send in (lambda _payload: (_ for _ in ()).throw(TimeoutError('secret')),
                     lambda _payload: reply('seerr:movie:999')):
            with self.subTest(send=send), tempfile.TemporaryDirectory() as folder:
                ready = propose(candidate(raw()), confirmed=True)
                writer = RequestWriter(folder, send)
                with self.assertRaisesRegex(BrokerUnavailable, 'outcome-uncertain'):
                    writer.submit(ready)
                writer.send = lambda _payload: reply()
                with self.assertRaisesRegex(BrokerUnavailable, 'recovery-required'):
                    writer.submit(ready)
                self.assertEqual(json.loads(next(Path(folder).glob('*.json')).read_text())['status'],
                                 'uncertain')

    def test_unconfirmed_and_identity_reuse_are_refused_before_send(self):
        calls = []
        with tempfile.TemporaryDirectory() as folder:
            writer = RequestWriter(folder, lambda payload: calls.append(payload) or reply())
            with self.assertRaisesRegex(BrokerUnavailable, 'not-ready'):
                writer.submit(propose(candidate(raw())))
            ready = propose(candidate(raw()), confirmed=True)
            writer.submit(ready)
            changed = propose(candidate(raw()), confirmed=True)
            changed.payload['seasons'] = [1]
            with self.assertRaisesRegex(BrokerUnavailable, 'identity-reused'):
                writer.submit(changed)
            self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
