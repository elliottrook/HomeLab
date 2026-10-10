"""Synthetic local bridge behavior; fake agent only, no Codex or credentials."""
from pathlib import Path
import tempfile
import unittest

from local_turn import run_local_turn
from store import DispatchStore
from test_contract import answer, end


JOB = 'request-12345678-1234-1234-1234-123456789abc'


class FakeAgent:
    def __init__(self, events=(), *, lose_start=False):
        self.events=list(events)
        self.lose_start=lose_start
        self.session=None
        self.starts=[]
        self.interrupts=[]
        self.replies=[]
        self.threads=0

    def create(self, model):
        self.threads+=1
        return 't'

    def start(self, request):
        self.starts.append(request)
        if self.lose_start:
            raise ConnectionError('synthetic lost acknowledgement')
        return 'u'

    def read(self, deadline):
        if not self.events: raise TimeoutError()
        return self.events.pop(0)

    def interrupt(self, request): self.interrupts.append(request)
    def reply(self, response): self.replies.append(response)


class LocalTurnTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'jobs.sqlite'
        self.store=DispatchStore(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def run_turn(self, agent, job_id=JOB, text='synthetic reviewed text'):
        return run_local_turn(agent,self.store,job_id,'owner',text,'fixed-model')

    def test_one_final_answer_and_no_prompt_in_dispatch_store(self):
        agent=FakeAgent([answer(),end()])
        result=self.run_turn(agent)
        self.assertEqual(result['state'],'completed')
        self.assertEqual(result['answer'],'Verified result')
        self.assertEqual(agent.starts[0]['params']['input'][0]['text'],
                         'synthetic reviewed text')
        self.assertEqual(len(agent.starts),1)
        self.assertEqual(self.store.inspect(JOB),('completed','t','u'))
        self.assertNotIn(b'synthetic reviewed text',self.path.read_bytes())
        self.assertNotIn(b'Verified result',self.path.read_bytes())

    def test_lost_turn_start_acknowledgement_never_replays(self):
        first=FakeAgent(lose_start=True)
        result=self.run_turn(first)
        self.assertEqual(result['state'],'unknown')
        self.assertEqual(len(first.starts),1)
        second=FakeAgent([answer(),end()])
        with self.assertRaises(ValueError):self.run_turn(second)
        self.assertEqual(second.threads,0)
        self.assertEqual(second.starts,[])
        self.assertEqual(self.store.inspect(JOB)[0],'unknown')

    def test_uncertain_turn_survives_store_reopen_without_resubmission(self):
        first=FakeAgent(lose_start=True)
        self.assertEqual(self.run_turn(first)['state'],'unknown')
        self.store.close()
        self.store=DispatchStore(self.path)
        second=FakeAgent([answer(),end()])
        with self.assertRaises(ValueError):
            self.run_turn(second)
        self.assertEqual(second.threads,0)
        self.assertEqual(second.starts,[])
        self.assertEqual(self.store.inspect(JOB)[0],'unknown')

    def test_competing_claim_is_uncertain_without_second_turn(self):
        store=self.store
        class CompetingAgent(FakeAgent):
            def create(self, model):
                store.claim(JOB,'other-thread','owner')
                return super().create(model)
        agent=CompetingAgent()
        result=self.run_turn(agent)
        self.assertEqual(result['state'],'unknown')
        self.assertEqual(agent.starts,[])
        self.assertEqual(self.store.inspect(JOB)[1],'other-thread')

    def test_server_tool_request_cannot_produce_an_answer(self):
        agent=FakeAgent([{'id':7,'method':'tool/request'},answer(),end()])
        result=self.run_turn(agent)
        self.assertEqual(result['state'],'blocked_server_request')
        self.assertEqual(result['answer'],'')
        self.assertEqual(self.store.inspect(JOB)[0],'unknown')
        self.assertEqual(agent.replies[0]['error']['code'],-32601)
        self.assertEqual(len(agent.interrupts),1)

    def test_timeout_requests_stop_but_remains_uncertain(self):
        agent=FakeAgent()
        result=self.run_turn(agent)
        self.assertEqual(result['state'],'unknown')
        self.assertEqual(len(agent.interrupts),1)
        self.assertEqual(self.store.inspect(JOB)[0],'unknown')
        self.assertFalse(result['automatic_retry'])

    def test_invalid_request_does_not_start_agent(self):
        agent=FakeAgent()
        for text in ('', ' ', 'bad\x00text', 'x'*16001):
            with self.assertRaises(ValueError):self.run_turn(agent,text=text)
        self.assertEqual(agent.threads,0)
        self.assertEqual(agent.starts,[])
