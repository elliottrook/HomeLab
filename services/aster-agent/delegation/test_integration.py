import hashlib
import tempfile
import unittest
from pathlib import Path

from handoff import Gateway, WorkerInbox
from integration import execute_admitted, deliver_recovered
from runtime import open_runtime
from test_contract import answer, end


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = 1000
        self.payload = b"fictional fixture"
        self.gateway = Gateway(self.root/'gateway.sqlite', 'gateway', clock=lambda: self.now)
        self.inbox = WorkerInbox(self.root/'inbox.sqlite', 'mac', 'gateway',
                                 [('a'*64, 'fixture-model')], clock=lambda: self.now)
        self.runtime = open_runtime(self.root/'runtime', enabled=True)
        self.gateway.create('j', 'owner', 'mac', hashlib.sha256(self.payload).hexdigest(),
                            'a'*64, 'fixture-model', 1100)
        self.envelope = self.gateway.offer('mac', 'j')
        self.calls = 0
        self.snapshot = {'thread': {'id': 't', 'turns': [{'id': 'u', 'status': 'completed',
                         'itemsView': 'full', 'items': [answer()['params']['item']]}]}}

    def tearDown(self):
        self.runtime.close()
        self.inbox.close()
        self.gateway.close()
        self.tmp.cleanup()

    def exchange(self, request, session):
        self.calls += 1
        self.assertEqual(request['method'], 'turn/start')
        self.assertEqual(request['params']['input'][0]['text'], self.payload.decode())
        session.acknowledge('u')
        session.receive(answer())
        session.receive(end())

    def run_fixture(self, exchange=None, enabled=True):
        return execute_admitted(self.inbox, self.runtime.store, 'gateway', self.envelope,
                                self.payload, 't', exchange or self.exchange, enabled=enabled)

    def deliver(self):
        return deliver_recovered(self.inbox, self.runtime.store, self.envelope,
                                  self.snapshot, self.gateway, 'mac')

    def test_disabled_does_not_admit_or_dispatch(self):
        self.assertIsNone(self.run_fixture(enabled=False))
        self.assertIsNone(self.runtime.store.inspect('j'))
        self.assertEqual(self.calls, 0)
        self.assertIsNotNone(self.run_fixture())

    def test_owner_receives_exact_answer_and_other_owner_is_denied(self):
        self.run_fixture()
        self.assertEqual(self.deliver(), 'completed')
        result = self.gateway.owner_result('owner', 'j')
        self.assertEqual(result['answer'], 'Verified result')
        self.assertFalse(result['automatic_retry'])
        with self.assertRaises(KeyError): self.gateway.owner_result('other', 'j')

    def test_lost_start_ack_never_reexecutes_or_guesses_turn(self):
        def lost(request, session):
            self.calls += 1
            raise ConnectionError('fixture loss')
        with self.assertRaises(ConnectionError): self.run_fixture(lost)
        self.assertIsNone(self.run_fixture())
        self.assertIsNone(self.deliver())
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.runtime.store.inspect('j')[0], 'unknown')

    def test_lost_terminal_event_recovers_without_second_dispatch(self):
        def lost(request, session):
            self.calls += 1
            session.acknowledge('u')
            raise ConnectionError('fixture loss')
        with self.assertRaises(ConnectionError): self.run_fixture(lost)
        self.runtime.close()
        self.runtime = open_runtime(self.root/'runtime', enabled=True)
        self.assertIsNone(self.run_fixture())
        self.assertEqual(self.deliver(), 'completed')
        self.assertEqual(self.calls, 1)

    def test_gateway_restart_loses_text_but_recovers_without_inference(self):
        self.run_fixture(); self.deliver()
        self.gateway.close()
        self.gateway = Gateway(self.root/'gateway.sqlite', 'gateway', clock=lambda: self.now)
        self.assertTrue(self.gateway.owner_result('owner', 'j')['recovery_required'])
        self.deliver(); self.deliver()
        self.assertEqual(self.gateway.owner_result('owner', 'j')['answer'], 'Verified result')
        self.assertEqual(self.calls, 1)

    def test_wrong_worker_changed_text_and_early_answer_rejected(self):
        args = ('mac', 'j', self.envelope['delivery_id'], 'Verified result')
        with self.assertRaises(ValueError): self.gateway.deliver_answer(*args)
        self.run_fixture(); self.deliver()
        with self.assertRaises(KeyError): self.gateway.deliver_answer('other', *args[1:])
        with self.assertRaises(ValueError): self.gateway.deliver_answer(*args[:3], 'Altered')

    def test_final_text_expires_without_erasing_duplicate_protection(self):
        self.run_fixture(); self.deliver()
        self.now += 900
        result = self.gateway.owner_result('owner', 'j')
        self.assertIsNone(result['answer'])
        self.assertTrue(result['recovery_required'])
        self.assertIsNone(self.run_fixture())
        self.assertEqual(self.calls, 1)

    def test_incomplete_exchange_return_is_unknown(self):
        session = self.run_fixture(lambda request, session: session.acknowledge('u'))
        self.assertEqual(session.state, 'unknown')
        self.assertEqual(session.answer, '')
