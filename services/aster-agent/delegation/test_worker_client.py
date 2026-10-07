import hashlib
import tempfile
import unittest
from pathlib import Path
try:
    import httpx
    from fastapi import FastAPI
except ImportError:
    httpx = None


@unittest.skipIf(httpx is None, 'Run with pinned gateway dependencies')
class WorkerClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_identity_to_owner_result_and_revocation(self):
        from handoff import Gateway
        from worker_auth import WorkerIdentity, ISSUER, CLIENT_ID
        from worker_client import WorkerClient, WorkerConnectionError
        from worker_router import worker_router, owner_result_router
        active = True
        def issuer(request):
            return httpx.Response(200, json=dict(active=active, sub='fixture', iss=ISSUER,
                client_id=CLIENT_ID, aud=CLIENT_ID, scope='aster.worker', iat=1000, exp=1300))
        identity = WorkerIdentity('fixture', lambda: 'fixture-secret', lambda: True,
            enabled=True, clock=lambda: 1100, transport=httpx.MockTransport(issuer))
        with tempfile.TemporaryDirectory() as directory:
            gateway = Gateway(Path(directory)/'gateway.sqlite', 'gateway', clock=lambda: 1000)
            try:
                gateway.create('job-1', 'owner', 'aster-codex-worker-mac', 'a'*64, 'b'*64, 'model', 1100)
                app = FastAPI(); app.include_router(worker_router(gateway, identity, enabled=True))
                async def owner(): return 'owner'
                app.include_router(owner_result_router(gateway, owner, enabled=True))
                transport = httpx.ASGITransport(app=app)
                worker = WorkerClient(lambda: 'fixture-token', enabled=True, transport=transport)
                envelope = await worker.offer('job-1')
                receipt = dict(delivery_id=envelope['delivery_id'], event='completed',
                               result_sha256=hashlib.sha256(b'Exact fixture answer').hexdigest())
                await worker.receipt('job-1', receipt)
                await worker.answer('job-1', envelope['delivery_id'], 'Exact fixture answer')
                async with httpx.AsyncClient(transport=transport, base_url='https://aster.elliottrook.com') as client:
                    value = (await client.get('/v1/companion/delegation/jobs/job-1')).json()
                    self.assertEqual(value['reply'], 'Exact fixture answer')
                active = False
                with self.assertRaises(WorkerConnectionError): await worker.offer('job-1')
            finally: gateway.close()

    async def test_disabled_invalid_id_and_token_have_no_network_effect(self):
        from worker_client import WorkerClient, WorkerConnectionError
        calls = []
        def handler(request): calls.append(request); return httpx.Response(500)
        worker = WorkerClient(lambda: 'token', transport=httpx.MockTransport(handler))
        with self.assertRaises(WorkerConnectionError): await worker.offer('j')
        worker.enabled = True
        for job in ('../other', 'j?token=x', 'j/offer', ''):
            with self.assertRaises(WorkerConnectionError): await worker.offer(job)
        worker.token = lambda: 'bad\ntoken'
        with self.assertRaises(WorkerConnectionError): await worker.offer('j')
        self.assertEqual(calls, [])

    async def test_failures_do_not_redirect_retry_or_leak_body(self):
        from worker_client import WorkerClient, WorkerConnectionError
        for status in (302, 401, 409, 500):
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(status, text='sensitive upstream text',
                                      headers={'Location': 'https://untrusted.invalid/'})
            worker = WorkerClient(lambda: 'fixture-token', enabled=True, transport=httpx.MockTransport(handler))
            with self.assertRaises(WorkerConnectionError) as caught: await worker.offer('j')
            self.assertNotIn('sensitive', str(caught.exception))
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].url.host, 'aster.elliottrook.com')

    async def test_malformed_and_oversize_responses_are_rejected(self):
        from worker_client import WorkerClient, WorkerConnectionError
        for value in ([], {'offer': {}, 'unexpected': True}, {'offer': {}}, {'padding': 'x'*66000}):
            worker = WorkerClient(lambda: 'fixture-token', enabled=True,
                transport=httpx.MockTransport(lambda request: httpx.Response(200, json=value)))
            with self.assertRaises(WorkerConnectionError): await worker.offer('j')
