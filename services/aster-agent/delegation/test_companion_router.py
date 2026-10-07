"""HTTP fixture tests; requires the gateway's pinned FastAPI/httpx dependencies."""
import tempfile
import unittest
from pathlib import Path

try:
    import httpx
    from fastapi import FastAPI, Header, HTTPException
except ImportError:
    httpx = None

from companion import CompanionJobs
from session import Session
from store import DispatchStore
from test_contract import answer, end


@unittest.skipIf(httpx is None, 'Run with the pinned gateway dependencies')
class RouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from companion_router import delegation_router
        self.tmp = tempfile.TemporaryDirectory()
        self.store = DispatchStore(Path(self.tmp.name)/'jobs.sqlite')
        self.session = Session(self.store, 'j', 't', owner='alice')
        self.session.prepare('fixture'); self.session.acknowledge('u')
        self.service = CompanionJobs(self.store, enabled=True)
        self.sessions = {'j': self.session}
        self.sent = []
        self.fail_send = False
        async def owner(authorization: str = Header(default='')):
            if authorization not in ('alice', 'bob'):
                raise HTTPException(401, 'Sign in')
            return authorization
        async def send(request):
            self.sent.append(request)
            if self.fail_send:
                raise RuntimeError('sensitive transport detail')
        app = FastAPI()
        app.include_router(delegation_router(self.service, owner, self.sessions, send))
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture')
        self.path = '/v1/companion/delegation/jobs/j'

    async def asyncTearDown(self):
        await self.client.aclose(); self.store.close(); self.tmp.cleanup()

    async def test_authentication_and_owner_are_required(self):
        self.assertEqual((await self.client.get(self.path)).status_code, 401)
        self.assertEqual((await self.client.get(self.path+'?owner=alice', headers={'Authorization':'bob'})).status_code, 404)
        self.assertEqual((await self.client.post(self.path+'/cancel', headers={'Authorization':'bob'}, json={'owner':'alice'})).status_code,404)
        self.assertEqual(self.sent, [])

    async def test_disabled_returns_unavailable(self):
        self.service.enabled = False
        self.assertEqual((await self.client.get(self.path, headers={'Authorization':'alice'})).status_code,503)

    async def test_final_answer_and_no_store(self):
        self.session.receive(answer('Faithful final answer')); self.session.receive(end())
        response = await self.client.get(self.path, headers={'Authorization':'alice'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertEqual(response.json()['reply'],'Faithful final answer')

    async def test_cancellation_waits_for_ack_and_is_not_resent(self):
        for _ in range(2):
            response = await self.client.post(self.path+'/cancel', headers={'Authorization':'alice'})
            self.assertEqual(response.status_code,202)
            self.assertEqual(response.json()['state'],'cancel_requested')
        self.assertEqual(len(self.sent),1)
        self.assertEqual(self.sent[0], {'method':'turn/interrupt','params':{'threadId':'t','turnId':'u'}})
        self.session.receive(end('interrupted'))
        response = await self.client.get(self.path, headers={'Authorization':'alice'})
        self.assertEqual(response.json()['state'],'interrupted')

    async def test_transport_failure_does_not_claim_stopped(self):
        self.fail_send = True
        response = await self.client.post(self.path+'/cancel', headers={'Authorization':'alice'})
        self.assertEqual(response.status_code,503)
        self.assertNotIn('sensitive',response.text)
        response = await self.client.get(self.path, headers={'Authorization':'alice'})
        self.assertEqual(response.json()['state'],'unknown')

    async def test_no_live_session_blocks_cancel_without_resubmit(self):
        self.sessions.clear()
        response = await self.client.post(self.path+'/cancel', headers={'Authorization':'alice'})
        self.assertEqual(response.status_code,409)
        self.assertEqual(self.sent,[])

    async def test_no_dispatch_endpoint(self):
        response = await self.client.post('/v1/companion/delegation/jobs', headers={'Authorization':'alice'},json={'prompt':'do work'})
        self.assertEqual(response.status_code,404)
