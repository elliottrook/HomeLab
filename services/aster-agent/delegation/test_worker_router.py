import tempfile
import unittest
from pathlib import Path
try:
    import httpx
    from fastapi import FastAPI, Header, HTTPException
except ImportError:
    httpx = None
from handoff import Gateway


@unittest.skipIf(httpx is None,'Run with pinned gateway dependencies')
class WorkerRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from worker_router import worker_router
        self.tmp=tempfile.TemporaryDirectory()
        self.gateway=Gateway(Path(self.tmp.name)/'jobs.sqlite','gateway',clock=lambda:1000)
        self.gateway.create('j','owner','mac','a'*64,'b'*64,'fixture-model',1100)
        async def identity(authorization: str=Header(default='')):
            identities={'worker-fixture':'mac','other-worker-fixture':'other'}
            if authorization not in identities: raise HTTPException(401,'Worker identity required')
            return identities[authorization]
        app=FastAPI();app.include_router(worker_router(self.gateway,identity,enabled=True))
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture')
        self.headers={'Authorization':'worker-fixture'}
        self.base='/v1/delegation/worker/jobs/j'

    async def asyncTearDown(self):
        await self.client.aclose();self.gateway.close();self.tmp.cleanup()

    async def test_user_identity_cannot_poll_and_other_worker_cannot_claim(self):
        r=await self.client.post(self.base+'/offer',headers={'Authorization':'owner'})
        self.assertEqual(r.status_code,401)
        r=await self.client.post(self.base+'/offer',headers={'Authorization':'other-worker-fixture'})
        self.assertEqual(r.status_code,404)

    async def test_repeated_offer_has_same_delivery_and_no_store(self):
        first=await self.client.post(self.base+'/offer',headers=self.headers)
        second=await self.client.post(self.base+'/offer',headers=self.headers)
        self.assertEqual(first.json(),second.json())
        self.assertEqual(first.headers['cache-control'],'no-store')

    async def test_spoofed_identity_or_privileges_in_receipt_rejected(self):
        e=(await self.client.post(self.base+'/offer',headers=self.headers)).json()['offer']
        r=await self.client.post(self.base+'/receipt',headers=self.headers,
            json={'delivery_id':e['delivery_id'],'event':'running','worker':'mac','permissions':['root']})
        self.assertEqual(r.status_code,422)
        self.assertEqual(self.gateway.status('owner','j')['state'],'offered')

    async def test_receipt_is_bound_and_completion_cannot_be_rewritten(self):
        e=(await self.client.post(self.base+'/offer',headers=self.headers)).json()['offer']
        body={'delivery_id':e['delivery_id'],'event':'completed','result_sha256':'c'*64}
        self.assertEqual((await self.client.post(self.base+'/receipt',headers=self.headers,json=body)).status_code,200)
        body['result_sha256']='d'*64
        self.assertEqual((await self.client.post(self.base+'/receipt',headers=self.headers,json=body)).status_code,409)

    async def test_default_disabled_routes_do_not_offer_work(self):
        from worker_router import worker_router
        async def identity(): return 'mac'
        app=FastAPI();app.include_router(worker_router(self.gateway,identity))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://fixture') as c:
            self.assertEqual((await c.post(self.base+'/offer')).status_code,503)
        self.assertEqual(self.gateway.status('owner','j')['state'],'queued')
