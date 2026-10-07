import hashlib
import tempfile
import unittest
from pathlib import Path
from handoff import Gateway, WorkerInbox
from runtime import open_runtime
from worker import run_one
from test_contract import answer, end


class Agent:
    def __init__(self):
        self.session = None; self.starts = 0; self.stops = 0
        self.events = [answer(),end()]
    def create(self, model): return 't'
    def start(self, request): self.starts += 1; return 'u'
    def read(self, deadline): return self.events.pop(0)
    def interrupt(self, request): self.stops += 1
    def reply(self, message): pass


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.payload = b'fictional fixture'
        self.gateway = Gateway(self.root/'gateway.sqlite','gateway',clock=lambda:1000)
        self.gateway.create('j','owner','mac',hashlib.sha256(self.payload).hexdigest(),'a'*64,'model',1100)
        self.inbox = WorkerInbox(self.root/'inbox.sqlite','mac','gateway',[('a'*64,'model')],clock=lambda:1000)
        self.runtime = open_runtime(self.root/'worker',enabled=True)
        self.agent = Agent()
        gateway = self.gateway
        class Client:
            async def offer(self, job): return gateway.offer('mac',job)
            async def receipt(self, job, value): return gateway.receipt('mac',job,**value)
            async def controls(self, job, delivery): return gateway.controls('mac',job,delivery)
            async def answer(self, job, delivery, answer): gateway.deliver_answer('mac',job,delivery,answer)
            async def usage(self, job, delivery, usage): gateway.report_usage('mac',job,delivery,usage)
        self.client = Client()

    def tearDown(self):
        self.runtime.close(); self.inbox.close(); self.gateway.close(); self.tmp.cleanup()

    async def run_worker(self, **kwargs):
        return await run_one(self.client,self.inbox,self.runtime.store,self.agent,'j',self.payload,enabled=True,**kwargs)

    async def test_complete_once_and_deliver_exact_owner_answer(self):
        self.assertEqual((await self.run_worker())['state'],'completed')
        self.assertEqual(self.gateway.owner_result('owner','j')['answer'],'Verified result')
        self.assertEqual((await self.run_worker())['state'],'not_offered')
        self.assertEqual(self.agent.starts,1)

    async def test_stop_before_dispatch_never_starts_model(self):
        self.gateway.request_stop('owner','j')
        self.assertEqual((await self.run_worker())['state'],'not_dispatched_review_required')
        self.assertEqual(self.agent.starts,0)
        self.assertIsNone(self.runtime.store.inspect('j'))

    async def test_lost_start_ack_stays_unknown_and_never_repeats(self):
        def lost(request): self.agent.starts += 1; raise ConnectionError('lost')
        self.agent.start = lost
        result = await self.run_worker()
        self.assertEqual(result['state'],'unknown')
        self.assertEqual(result['diagnostic'],{'stage':'turn_start','error_type':'ConnectionError','stop_rpc_acknowledged':False})
        await self.run_worker()
        self.assertEqual(self.agent.starts,1)
        self.assertEqual(self.runtime.store.inspect('j')[0],'unknown')

    async def test_stop_while_running_waits_for_provider_terminal(self):
        original = self.agent.start
        def start(request):
            self.gateway.request_stop('owner','j')
            return original(request)
        self.agent.start = start; self.agent.events = [end('interrupted')]
        self.assertEqual((await self.run_worker())['state'],'interrupted')
        self.assertEqual(self.agent.stops,1)

    async def test_failure_diagnostic_never_retains_raw_exception(self):
        def failed(request): raise RuntimeError('secret material must not be stored')
        self.agent.start = failed
        result = await self.run_worker()
        self.assertNotIn('secret material',str(result))
        self.assertEqual(result['diagnostic']['error_type'],'RuntimeError')
        self.assertIsNone(self.gateway.owner_result('owner','j')['answer'])

    async def test_control_outage_attempts_stop_and_preserves_unknown(self):
        original = self.client.controls; calls = 0
        async def controls(*args):
            nonlocal calls
            calls += 1
            if calls >= 3: raise ConnectionError('lost')
            return await original(*args)
        self.client.controls = controls
        self.assertEqual((await self.run_worker())['state'],'unknown')
        self.assertEqual(self.agent.stops,1)
        self.assertEqual(self.runtime.store.inspect('j')[0],'unknown')

    async def test_lost_final_delivery_retains_completed_record_for_recovery(self):
        async def lost(*args): raise ConnectionError('lost')
        self.client.answer = lost
        self.assertEqual((await self.run_worker())['state'],'unknown')
        self.assertEqual(self.runtime.store.inspect('j')[0],'completed')
        self.assertTrue(self.gateway.owner_result('owner','j')['recovery_required'])
        await self.run_worker()
        self.assertEqual(self.agent.starts,1)

    async def test_disabled_has_no_effect(self):
        value = await run_one(self.client,self.inbox,self.runtime.store,self.agent,'j',self.payload)
        self.assertEqual(value['state'],'disabled')
        self.assertEqual(self.gateway.status('owner','j')['state'],'queued')

    async def test_deadline_interrupts_and_unconfirmed_stop_remains_unknown(self):
        now = 0
        def clock():
            nonlocal now
            now += .1
            return now
        def read(deadline): raise TimeoutError('fixture')
        self.agent.read = read
        self.assertEqual((await self.run_worker(deadline_seconds=1,clock=clock))['state'],'unknown')
        self.assertEqual(self.agent.starts,1)
        self.assertEqual(self.agent.stops,1)
