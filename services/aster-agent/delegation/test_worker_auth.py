import unittest
try:
    import httpx
    from fastapi import FastAPI, HTTPException
except ImportError:
    httpx = None


@unittest.skipIf(httpx is None, 'Run with pinned gateway dependencies')
class WorkerAuthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from worker_auth import WorkerIdentity, CLIENT_ID, ISSUER
        self.claims = dict(active=True, sub='fixture-sub', iss=ISSUER,
                           aud=CLIENT_ID, client_id=CLIENT_ID, scope='aster.worker',
                           iat=1000, exp=1300)
        self.allowed = True
        self.requests = 0
        self.response_status = 200
        def upstream(request):
            self.requests += 1
            self.assertEqual(request.url.host, 'auth.elliottrook.com')
            return httpx.Response(self.response_status, json=self.claims)
        self.identity = WorkerIdentity('fixture-sub', lambda: 'fixture-secret',
            lambda: self.allowed, enabled=True, clock=lambda: 1100,
            transport=httpx.MockTransport(upstream))

    async def test_active_identity_and_revocation_checked_each_request(self):
        self.assertEqual(await self.identity('Bearer fixture'), 'aster-codex-worker-mac')
        self.claims['active'] = False
        with self.assertRaises(HTTPException): await self.identity('Bearer fixture')
        self.assertEqual(self.requests, 2)

    async def test_boundary_and_lifetime_mismatches_fail_closed(self):
        for key, value in [('sub', 'human'), ('iss', 'other'), ('aud', 'aster-companion'),
                           ('client_id', 'aster-companion'), ('scope', 'openid'),
                           ('exp', 1600), ('iat', 1200), ('active', 'true'),
                           ('act', {'sub': 'human'})]:
            with self.subTest(key=key):
                previous = dict(self.claims)
                self.claims[key] = value
                with self.assertRaises(HTTPException): await self.identity('Bearer fixture')
                self.claims = previous

    async def test_disabled_or_killed_does_not_contact_issuer(self):
        self.identity.enabled = False
        with self.assertRaises(HTTPException): await self.identity('Bearer fixture')
        self.identity.enabled = True; self.allowed = False
        with self.assertRaises(HTTPException): await self.identity('Bearer fixture')
        self.assertEqual(self.requests, 0)

    async def test_gate_exception_or_truthy_nonboolean_denies_without_issuer(self):
        def broken(): raise RuntimeError('private status diagnostic')
        for callback in (broken, lambda: 1, lambda: 'true'):
            self.identity.permitted = callback
            with self.assertRaises(HTTPException) as caught:
                await self.identity('Bearer fixture')
            self.assertEqual(caught.exception.status_code, 503)
            self.assertNotIn('private', caught.exception.detail)
        self.assertEqual(self.requests, 0)

    async def test_outage_redirect_and_oversize_fail_closed(self):
        for status in (302, 401, 500):
            self.response_status = status
            with self.assertRaises(HTTPException): await self.identity('Bearer fixture')
        self.response_status = 200
        self.claims['padding'] = 'x'*33000
        with self.assertRaises(HTTPException): await self.identity('Bearer fixture')

    async def test_invalid_authorization_never_contacts_issuer(self):
        for header in ('', 'Basic fixture', 'Bearer ', 'Bearer two words', 'Bearer '+'x'*17000):
            with self.assertRaises(HTTPException): await self.identity(header)
        self.assertEqual(self.requests, 0)

    async def test_secret_failure_does_not_expose_exception(self):
        def unavailable(): raise RuntimeError('sensitive diagnostic')
        self.identity.secret = unavailable
        with self.assertRaises(HTTPException) as caught: await self.identity('Bearer fixture')
        self.assertNotIn('sensitive', caught.exception.detail)

    async def test_real_dependency_signature_and_owner_projection(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from handoff import Gateway
        from worker_router import worker_router, owner_result_router
        with tempfile.TemporaryDirectory() as directory:
            gateway = Gateway(Path(directory)/'jobs.sqlite', 'gateway', clock=lambda: 1000)
            try:
                gateway.create('j', 'owner', 'aster-codex-worker-mac', 'a'*64, 'b'*64, 'fixture', 1100)
                app = FastAPI()
                app.include_router(worker_router(gateway, self.identity, enabled=True))
                async def owner(): return 'owner'
                app.include_router(owner_result_router(gateway, owner, enabled=True))
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
                    headers = {'Authorization': 'Bearer fixture'}
                    base = '/v1/delegation/worker/jobs/j'
                    envelope = (await client.post(base+'/offer', headers=headers)).json()['offer']
                    receipt = dict(delivery_id=envelope['delivery_id'], event='completed',
                                   result_sha256=hashlib.sha256(b'Exact answer').hexdigest())
                    self.assertEqual((await client.post(base+'/receipt', headers=headers, json=receipt)).status_code, 200)
                    missing = (await client.get('/v1/companion/delegation/jobs/j')).json()
                    self.assertTrue(missing['recovery_required'])
                    self.assertEqual((await client.post(base+'/answer', headers=headers,
                        json=dict(delivery_id=envelope['delivery_id'], answer='Exact answer'))).status_code, 200)
                    result = await client.get('/v1/companion/delegation/jobs/j')
                    self.assertEqual(result.json()['reply'], 'Exact answer')
                    self.assertEqual(result.headers['cache-control'], 'no-store')
                    self.claims['active'] = False
                    self.assertEqual((await client.post(base+'/offer', headers=headers)).status_code, 401)
            finally:
                gateway.close()
