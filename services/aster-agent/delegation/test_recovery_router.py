"""Offline ASGI authentication and answer-gating fixture."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import httpx
from fastapi import FastAPI,Header,HTTPException
from handoff import Gateway
from recovery_router import recovery_router


class RecoveryRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.gateway=Gateway(Path(self.tmp.name)/'gateway.sqlite','gateway',clock=lambda:1000)
        self.answer='Synthetic completed answer.'
        digest=hashlib.sha256(self.answer.encode()).hexdigest()
        self.gateway.create('job','owner','worker','a'*64,'b'*64,'model',1100)
        e=self.gateway.offer('worker','job')
        self.gateway.receipt('worker','job',e['delivery_id'],'completed',digest)
        async def owner(authorization:str=Header(default='')):
            if authorization not in {'owner-token','other-owner-token'}:
                raise HTTPException(401,'Owner required')
            return 'owner' if authorization=='owner-token' else 'other-owner'
        async def worker(authorization:str=Header(default='')):
            if authorization not in {'worker-token','other-worker-token'}:
                raise HTTPException(401,'Worker required')
            return 'worker' if authorization=='worker-token' else 'other-worker'
        self.owner,self.worker=owner,worker
        app=FastAPI();app.include_router(recovery_router(self.gateway,owner,worker,enabled=True))
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture')

    async def asyncTearDown(self):
        await self.client.aclose();self.gateway.close();self.tmp.cleanup()

    async def ticket(self):
        r=await self.client.post('/v1/companion/delegation/recovery/job',headers={'Authorization':'owner-token'})
        self.assertEqual(r.status_code,202)
        return r.json()['ticket_id']

    async def test_owner_cannot_be_spoofed_and_worker_cannot_claim_as_owner(self):
        for header in ({},{'Authorization':'worker-token'},{'Authorization':'other-owner-token'}):
            r=await self.client.post('/v1/companion/delegation/recovery/job',headers=header)
            self.assertIn(r.status_code,(401,404))
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_recovery').fetchone()[0],0)

    async def test_exact_ticket_claim_and_digest_bound_answer(self):
        ticket=await self.ticket()
        base='/v1/delegation/worker/recovery/'+ticket
        self.assertEqual((await self.client.post(base+'/claim',headers={'Authorization':'other-worker-token'})).status_code,404)
        claim=await self.client.post(base+'/claim',headers={'Authorization':'worker-token'})
        self.assertEqual(claim.status_code,200)
        self.assertEqual(claim.json()['job_id'],'job')
        self.assertEqual((await self.client.post(base+'/answer',headers={'Authorization':'worker-token'},json={'answer':'Changed'})).status_code,409)
        self.assertIsNone(self.gateway.owner_result('owner','job')['answer'])
        sent=await self.client.post(base+'/answer',headers={'Authorization':'worker-token'},json={'answer':self.answer})
        self.assertEqual(sent.json(),{'accepted':True,'job_id':'job'})
        self.assertEqual(self.gateway.owner_result('owner','job')['answer'],self.answer)
        status=await self.client.get('/v1/companion/delegation/recovery/tickets/'+ticket,headers={'Authorization':'owner-token'})
        self.assertEqual(status.json()['state'],'completed')
        self.assertEqual(status.headers['cache-control'],'no-store')
        other=await self.client.get('/v1/companion/delegation/recovery/tickets/'+ticket,headers={'Authorization':'other-owner-token'})
        self.assertEqual(other.status_code,404)
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_jobs').fetchone()[0],1)

    async def test_disabled_router_does_not_issue_ticket(self):
        app=FastAPI();app.include_router(recovery_router(self.gateway,self.owner,self.worker))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as c:
            r=await c.post('/v1/companion/delegation/recovery/job',headers={'Authorization':'owner-token'})
            self.assertEqual(r.status_code,404)
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_recovery').fetchone()[0],0)
