import json
import os
import tempfile
import unittest
from pathlib import Path

from recovery import reconcile
from session import Session
from store import DispatchStore
from transport import Transport
from test_contract import answer, end


class TransportTests(unittest.TestCase):
    def setUp(self):
        a, b = os.pipe(); c, d = os.pipe()
        self.reader, self.server_writer = os.fdopen(a, 'rb', buffering=0), os.fdopen(b, 'wb', buffering=0)
        self.server_reader, self.writer = os.fdopen(c, 'rb', buffering=0), os.fdopen(d, 'wb', buffering=0)
        self.events = []
        self.transport = Transport(self.reader, self.writer, {'turn/start'}, self.events.append)

    def tearDown(self):
        self.transport.close()
        for f in (self.reader, self.writer, self.server_reader, self.server_writer):
            f.close()

    def feed(self, *messages):
        for m in messages:
            self.server_writer.write(json.dumps(m).encode()+b'\n')

    def test_notifications_are_not_lost_before_rpc_response(self):
        self.feed(answer(), end(), {'id': 1, 'result': {'turn': {'id': 'u'}}})
        result = self.transport.call('turn/start', {})
        self.assertEqual(result['turn']['id'], 'u')
        self.assertEqual(len(self.events), 2)

    def test_server_request_is_rejected_not_silently_approved(self):
        self.feed({'id': 19, 'method': 'approval'}, {'id': 1, 'result': {}})
        self.transport.call('turn/start', {})
        sent = os.read(self.server_reader.fileno(), 4096).decode().splitlines()
        self.assertEqual(json.loads(sent[1])['error']['code'], -32601)

    def test_timeout_disables_transport_without_retry(self):
        with self.assertRaises(TimeoutError):
            self.transport.call('turn/start', {}, timeout=.01)
        with self.assertRaises(ValueError):
            self.transport.call('turn/start', {})

    def test_blocked_writer_has_deadline(self):
        try:
            while True:
                os.write(self.writer.fileno(), b'x'*4096)
        except BlockingIOError:
            pass
        with self.assertRaises(TimeoutError):
            self.transport.call('turn/start', {}, timeout=.01)

    def test_eof_marks_uncertain(self):
        self.server_writer.close()
        with self.assertRaises(EOFError):
            self.transport.call('turn/start', {})
        self.assertTrue(self.transport.broken)

    def test_wrong_response_id_stops(self):
        self.feed({'id': 999, 'result': {}})
        with self.assertRaises(ValueError):
            self.transport.call('turn/start', {})

    def test_unlisted_method_never_written(self):
        with self.assertRaises(ValueError):
            self.transport.call('config/value/write', {})
        self.assertEqual(self.transport.serial, 0)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'jobs.sqlite'
        self.store = DispatchStore(self.path)
        self.session = Session(self.store, 'j', 't')
        self.session.prepare('fixture')

    def tearDown(self):
        self.store.close(); self.tmp.cleanup()

    def snapshot(self, status='completed'):
        return {'thread': {'id': 't', 'turns': [{'id': 'u', 'status': status,
            'itemsView': 'full', 'items': [answer()['params']['item']]}]}}

    def test_lost_ack_retains_thread_but_does_not_guess_turn(self):
        self.assertEqual(self.store.inspect('j'), ('dispatch_unknown', 't', None))
        self.assertEqual(reconcile(self.store, 'j', self.snapshot())['state'], 'unacknowledged_dispatch')

    def test_known_turn_recovers_after_restart_without_resubmit(self):
        self.session.acknowledge('u')
        self.store.close(); self.store = DispatchStore(self.path)
        result = reconcile(self.store, 'j', self.snapshot())
        self.assertEqual(result, {'state': 'completed', 'answer': 'Verified result'})
        self.assertFalse(self.store.claim('j'))
        self.assertEqual(reconcile(self.store, 'j', self.snapshot()), result)

    def test_wrong_thread_rejected(self):
        self.session.acknowledge('u')
        s = self.snapshot(); s['thread']['id'] = 'other'
        with self.assertRaises(ValueError):
            reconcile(self.store, 'j', s)

    def test_partial_snapshot_cannot_publish(self):
        self.session.acknowledge('u')
        s = self.snapshot(); s['thread']['turns'][0]['itemsView'] = 'partial'
        self.assertEqual(reconcile(self.store, 'j', s)['state'], 'incomplete_snapshot')

    def test_conflicting_terminal_status_rejected(self):
        self.session.acknowledge('u')
        self.store.finish('j', 't', 'u', 'failed')
        with self.assertRaises(ValueError):
            reconcile(self.store, 'j', self.snapshot())

    def test_failed_and_active_turns_do_not_publish_answer(self):
        self.session.acknowledge('u')
        self.assertEqual(reconcile(self.store, 'j', self.snapshot('inProgress'))['answer'], '')
        self.assertEqual(reconcile(self.store, 'j', self.snapshot('failed'))['answer'], '')
