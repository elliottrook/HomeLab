import base64
import hashlib
import unittest
import httpx
from fastapi import FastAPI
from pilot_view import SCRIPT,pilot_view_router


class PilotViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_shell_has_no_answer_admission_or_external_dependency(self):
        app=FastAPI();app.include_router(pilot_view_router())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as client:
            response=await client.get('/companion/codex-pilot')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['cache-control'],'no-store')
            digest=base64.b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode()
            self.assertIn("script-src 'sha256-"+digest+"'",response.headers['content-security-policy'])
            self.assertIn('<pre id="result"></pre>',response.text)
            self.assertNotIn('innerHTML',SCRIPT)
            self.assertNotIn('setInterval',SCRIPT)
            self.assertNotIn('http',SCRIPT)
            self.assertEqual((await client.post('/companion/codex-pilot')).status_code,405)
            self.assertEqual((await client.post('/v1/delegation/jobs')).status_code,404)
