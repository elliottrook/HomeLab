import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from delegation.deployment import attach


class DeploymentTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_preserves_routes_lifecycle_and_never_loads_custody(self):
        from contextlib import asynccontextmanager
        events=[]
        @asynccontextmanager
        async def lifespan(app):
            events.append('start');yield;events.append('stop')
        app=FastAPI(lifespan=lifespan)
        @app.get('/household')
        def household(): return {'available':True}
        before=list(app.routes)
        with patch.dict(sys.modules,{'delegation.credentials':None,'delegation.gateway_assembly':None}):
            self.assertIsNone(attach(app,lambda:'owner',{}))
        self.assertEqual(app.routes,before)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as client:
                self.assertEqual((await client.get('/household')).json(),{'available':True})
                self.assertEqual((await client.post('/v1/delegation/worker/jobs/j/offer')).status_code,404)
        self.assertEqual(events,['start','stop'])

    async def test_enabled_refuses_unpinned_configuration_before_mount(self):
        for env in ({'ASTER_DELEGATION_ENABLED':'true'},
                    {'ASTER_DELEGATION_ENABLED':'1'},
                    {'ASTER_DELEGATION_ENABLED':'1','ASTER_WORKER_SUBJECT':'subject',
                     'CREDENTIALS_DIRECTORY':'/run/credentials/aster-agent.service',
                     'ASTER_WORKER_APPROLE_FILE':'/tmp/arbitrary','ASTER_WORKER_BAO_CA':'/ca'}):
            app=FastAPI();before=list(app.routes)
            with self.assertRaises(ValueError): attach(app,lambda:'owner',env)
            self.assertEqual(app.routes,before)

    async def test_duplicate_attachment_rejected(self):
        app=FastAPI();attach(app,lambda:'owner',{})
        with self.assertRaises(ValueError): attach(app,lambda:'owner',{})

    async def test_wrapper_reuses_installed_app_without_copy(self):
        existing=types.ModuleType('aster_agent');existing.app=FastAPI()
        existing.companion_owner=lambda:'owner'
        path=Path(__file__).resolve().parent.parent/'aster_with_delegation.py'
        spec=importlib.util.spec_from_file_location('fixture_wrapper',path)
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'aster_agent':existing}),patch.dict('os.environ',{'ASTER_DELEGATION_ENABLED':'0'}):
            spec.loader.exec_module(module)
        self.assertIs(module.app,existing.app)
        self.assertIsNone(module.app.state.aster_delegation)
