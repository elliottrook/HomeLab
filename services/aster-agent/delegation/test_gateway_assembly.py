import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import httpx
from fastapi import FastAPI
from gateway_assembly import GatewayAssembly
from worker_auth import CLIENT_ID, ISSUER


class GatewayAssemblyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name).resolve()/'state'
        self.socket = str(Path(self.tmp.name)/'broker.sock')
        self.enabled = True
        self.issuer_calls = 0
        self.secret = Mock(return_value='fixture-only')
        self.server = await asyncio.start_unix_server(self.broker, path=self.socket)

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        self.tmp.cleanup()

    async def broker(self, reader, writer):
        try:
            self.assertEqual(await reader.readline(), b'{"method":"automation.status"}\n')
            writer.write(json.dumps({'ok': True, 'result': {'global_enabled': self.enabled}}).encode()+b'\n')
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    def assembly(self, enabled=True,request_model=None):
        import time
        def issuer(request):
            self.issuer_calls += 1
            now = int(time.time())
            return httpx.Response(200, json=dict(active=True, sub='fixture-sub',
                iss=ISSUER, client_id=CLIENT_ID, aud=CLIENT_ID, scope='aster.worker',
                iat=now, exp=now+300))
        async def owner(): return 'owner'
        return GatewayAssembly(self.path, owner, subject='fixture-sub', secret=self.secret,
            enabled=enabled, broker_socket=self.socket, transport=httpx.MockTransport(issuer),request_model=request_model)

    async def test_optional_intake_lifecycle_retains_metadata_not_text_on_restart(self):
        import uuid
        assembly=self.assembly(request_model='fixture')
        app=FastAPI();app.include_router(assembly.router)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as c:
                r=await c.post('/v1/companion/delegation/requests',json={
                    'request_id':str(uuid.uuid4()),'text':'reviewed fixture','cloud_consent':True,'local_only':False})
                self.assertEqual(r.status_code,202)
                jid=r.json()['id'];self.assertIn(jid,assembly.intake.content)
        self.assertEqual(assembly.intake.content,{})
        async with app.router.lifespan_context(app):
            self.assertEqual(assembly.gateway._row(jid)[1],'queued')
            self.assertEqual(assembly.intake.content,{})

    async def test_closed_intake_reports_status_without_custody_or_submission(self):
        assembly=self.assembly()
        app=FastAPI();app.include_router(assembly.router)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as c:
                r=await c.get('/v1/companion/delegation/capabilities')
                self.assertEqual(r.status_code,200)
                self.assertFalse(r.json()['submission_enabled'])
                self.assertEqual(r.json()['worker_status'],'unknown')
                self.assertEqual(r.headers['cache-control'],'no-store')
                self.assertEqual((await c.post('/v1/companion/delegation/requests',json={})).status_code,404)
                self.secret.assert_not_called()
                self.assertEqual(self.issuer_calls,0)

    async def test_closed_status_still_requires_owner_authentication(self):
        from fastapi import HTTPException
        from request_intake import closed_intake_router
        async def deny():raise HTTPException(401,'Not authenticated')
        app=FastAPI();app.include_router(closed_intake_router(deny))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as c:
            self.assertEqual((await c.get('/v1/companion/delegation/capabilities')).status_code,401)

    async def test_disabled_has_no_routes_state_or_credentials(self):
        assembly = self.assembly(False)
        app = FastAPI(); app.include_router(assembly.router)
        async with app.router.lifespan_context(app):
            self.assertFalse(self.path.exists())
            self.assertFalse(assembly.router.routes)
            self.secret.assert_not_called()

    async def test_private_single_owner_and_durable_no_requeue(self):
        assembly = self.assembly()
        async with assembly.lifespan(None):
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o700)
            self.assertEqual((self.path/'gateway.sqlite').stat().st_mode & 0o777, 0o600)
            with self.assertRaises(BlockingIOError):
                async with self.assembly().lifespan(None): pass
            import time
            assembly.gateway.create('j', 'owner', 'aster-codex-worker-mac',
                'a'*64, 'b'*64, 'fixture', int(time.time())+100)
            offer = assembly.gateway.offer('aster-codex-worker-mac', 'j')
            assembly.gateway.receipt('aster-codex-worker-mac', 'j', offer['delivery_id'], 'accepted')
        async with assembly.lifespan(None):
            self.assertEqual(assembly.gateway.owner_result('owner', 'j')['state'], 'accepted')
            self.assertIsNone(assembly.gateway.offer('aster-codex-worker-mac', 'j'))
        self.assertIsNone(assembly.gateway)

    async def test_permissive_state_and_symlinks_refused(self):
        self.path.mkdir(mode=0o755); os.chmod(self.path, 0o755)
        with self.assertRaises(ValueError):
            async with self.assembly().lifespan(None): pass
        self.path.rmdir(); self.path.symlink_to(Path(self.tmp.name).resolve())
        with self.assertRaises(ValueError):
            async with self.assembly().lifespan(None): pass

    async def test_composed_http_checks_live_gate_on_each_request(self):
        assembly = self.assembly()
        app = FastAPI(); app.include_router(assembly.router)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://fixture') as client:
                headers = {'Authorization': 'Bearer fixture'}
                url = '/v1/delegation/worker/jobs/missing/offer'
                self.assertEqual((await client.post(url, headers=headers)).status_code, 404)
                self.enabled = False
                self.assertEqual((await client.post(url, headers=headers)).status_code, 503)
                self.assertEqual(self.issuer_calls, 1)
                self.server.close(); await self.server.wait_closed()
                self.assertEqual((await client.post(url, headers=headers)).status_code, 503)
                # Human status remains readable when worker access is disabled.
                self.assertEqual((await client.get('/v1/companion/delegation/jobs')).status_code, 200)
                self.assertEqual(self.issuer_calls, 1)
