import tempfile
import unittest
from pathlib import Path
from handoff import Gateway
from session import Session
from store import DispatchStore
from integration import poll_remote_stop
from test_contract import end


class RemoteControlsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.now = 1000
        self.gateway = Gateway(self.root/'gateway.sqlite', 'gateway', clock=lambda: self.now)
        self.gateway.create('j','owner','mac','a'*64,'b'*64,'model',1100)
        self.envelope = self.gateway.offer('mac','j')
        self.store = DispatchStore(self.root/'dispatch.sqlite')
        self.session = Session(self.store,'j','t',owner='owner')
        self.session.prepare('fixture'); self.session.acknowledge('u')
        self.gateway.receipt('mac','j',self.envelope['delivery_id'],'running')

    def tearDown(self):
        self.store.close(); self.gateway.close(); self.tmp.cleanup()

    async def test_stop_survives_restart_and_only_terminal_confirms(self):
        self.gateway.request_stop('owner','j')
        self.gateway.close()
        self.gateway = Gateway(self.root/'gateway.sqlite','gateway',clock=lambda:self.now)
        gateway = self.gateway
        class Client:
            async def controls(self, job, delivery): return gateway.controls('mac',job,delivery)
        sent = []
        async def interrupt(request): sent.append(request)
        await poll_remote_stop(Client(),self.envelope,self.session,interrupt)
        await poll_remote_stop(Client(),self.envelope,self.session,interrupt)
        self.assertEqual(len(sent),1)
        self.assertEqual(sent[0]['method'],'turn/interrupt')
        self.assertEqual(self.session.state,'cancel_requested')
        self.assertEqual(gateway.status('owner','j')['state'],'running')
        self.session.receive(end('interrupted'))
        gateway.receipt('mac','j',self.envelope['delivery_id'],'interrupted')
        self.assertEqual(gateway.owner_result('owner','j')['state'],'interrupted')

    async def test_control_outage_marks_unknown_without_retry(self):
        class Client:
            async def controls(self, *args): raise ConnectionError('fixture')
        async def interrupt(request): self.fail('Must not send')
        with self.assertRaises(ConnectionError):
            await poll_remote_stop(Client(),self.envelope,self.session,interrupt)
        self.assertEqual(self.session.state,'unknown')

    async def test_other_owner_or_worker_cannot_control(self):
        with self.assertRaises(KeyError): self.gateway.request_stop('other','j')
        with self.assertRaises(KeyError): self.gateway.controls('other','j',self.envelope['delivery_id'])
        self.assertFalse(self.gateway.owner_result('owner','j')['cancel_requested'])

    async def test_usage_is_sanitized_replace_not_sum_and_expires(self):
        counts = dict(inputTokens=4,cachedInputTokens=0,outputTokens=2,reasoningOutputTokens=0,totalTokens=6)
        usage = {'last':counts,'total':counts,'prompt':'must not persist'}
        for _ in range(2): self.gateway.report_usage('mac','j',self.envelope['delivery_id'],usage)
        value = self.gateway.owner_result('owner','j')['usage']
        self.assertEqual(value['total']['totalTokens'],6)
        self.assertNotIn('prompt',value)
        self.now += 86400
        self.assertIsNone(self.gateway.owner_result('owner','j')['usage'])
        self.assertEqual(self.gateway.status('owner','j')['state'],'running')

    async def test_usage_wrong_identity_or_malformed_rejected(self):
        with self.assertRaises(ValueError): self.gateway.report_usage('mac','j',self.envelope['delivery_id'],{})
        counts = dict(inputTokens=4,cachedInputTokens=0,outputTokens=2,reasoningOutputTokens=0,totalTokens=6)
        with self.assertRaises(KeyError):
            self.gateway.report_usage('other','j',self.envelope['delivery_id'],{'last':counts,'total':counts})
