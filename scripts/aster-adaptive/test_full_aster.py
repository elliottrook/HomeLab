"""Actual Aster HTTP chat path with synthetic auth and fixture-only dependencies.

ASGITransport does not start application background workers. No live OIDC,
model, source reader, broker, notification worker or filesystem state is used.
"""
import asyncio
import importlib
import json
import os
import socket
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException

from fixtures import CASES, make_run
from offline_baseline import SOURCE, digest
from contracts import HarnessRun


class FullAsterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.dict(os.environ, {
            'ASTER_API_KEY': 'synthetic-offline-fixture',
            'ASTER_LAB_STATE': str(root/'jobs.db'),
            'ASTER_NOTIFICATION_STATE': str(root/'notifications'),
            'ASTER_NOTIFICATION_KEY': str(root/'nonexistent-fixture-key'),
        }, clear=True))
        self.stack.enter_context(patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')))
        self.stack.enter_context(patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')))
        sys.path.insert(0, str(SOURCE.parent))
        self.addCleanup(lambda: sys.path.remove(str(SOURCE.parent)))
        self.aster = importlib.import_module('aster_agent')
        # Import caching must not select a previous test module's key/configuration.
        self.stack.enter_context(patch.object(self.aster, 'ASTER_API_KEY', 'synthetic-offline-fixture'))
        self.stack.enter_context(patch.object(self.aster.lab_operations, 'enabled', set()))
        self.stack.enter_context(patch.object(self.aster.lab_operations, 'owner', ''))
        self.stack.enter_context(patch.object(self.aster.lab_operations, 'worker_key', ''))
        self.executor = self.stack.enter_context(patch.object(self.aster, 'execute_tool', new_callable=AsyncMock))
        self.executor.return_value = {'fixture': True, 'status': 'available'}
        self.model = self.stack.enter_context(patch.object(self.aster, 'upstream_completion', new_callable=AsyncMock))
        self.model.return_value = self.reply()
        # Never contact JWKS: this suite tests the real synthetic-key path only.
        self.stack.enter_context(patch.object(self.aster._authentik_jwks_client,
                                             'get_signing_key_from_jwt', side_effect=ValueError('fixture invalid JWT')))
        self.http = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.aster.app), base_url='http://fixture.invalid')
        self.addAsyncCleanup(self.http.aclose)
        self.headers = {'Authorization': 'Bearer synthetic-offline-fixture'}

    @staticmethod
    def reply(calls=None):
        message = {'role': 'assistant', 'content': 'Synthetic answer'}
        if calls:
            message['tool_calls'] = calls
        return {'choices': [{'message': message, 'finish_reason': 'stop'}],
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}}

    def body(self, prompt, ids=()):
        contract = make_run(digest(SOURCE.read_bytes()), ids)
        contract = HarnessRun.model_validate_json(contract.model_dump_json())
        return {'messages': [{'role': 'user', 'content': prompt}],
                'enabled_tools': [c.implementation for c in contract.projection.capabilities]}

    async def test_full_http_fixed_corpus_stays_within_projection(self):
        for name, prompt, ids in CASES:
            with self.subTest(name=name):
                self.executor.reset_mock()
                self.model.reset_mock()
                response = await self.http.post('/v1/chat/completions', headers=self.headers, json=self.body(prompt, ids))
                self.assertEqual(200, response.status_code, response.text)
                self.assertEqual(len(ids), self.executor.await_count)
                self.assertEqual(1, self.model.await_count)
                payload = self.model.call_args.args[0]
                self.assertNotIn('tools', payload)
                self.assertNotIn('enabled_tools', payload)
                self.assertNotIn('synthetic-offline-fixture', json.dumps(payload))

    async def test_missing_and_invalid_identity_never_reach_executor(self):
        for headers in ({}, {'Authorization': 'Bearer invalid-fixture'}):
            response = await self.http.post('/v1/chat/completions', headers=headers,
                                            json=self.body('What time is it?', ('fixture.time',)))
            self.assertEqual(401, response.status_code)
        self.executor.assert_not_awaited()
        self.model.assert_not_awaited()

    async def test_persona_scope_cannot_be_expanded_by_conversation_tools(self):
        body = self.body('What is the current Home Assistant version?', ('fixture.ha',))
        body['persona'] = 'media'
        response = await self.http.post('/v1/chat/completions', headers=self.headers, json=body)
        self.assertEqual(200, response.status_code)
        self.executor.assert_not_awaited()

    async def test_unrequested_model_tool_call_is_denied(self):
        malicious = [{'id': 'fixture-call', 'type': 'function',
                      'function': {'name': 'get_netbox_report', 'arguments': '{}'}}]
        self.model.side_effect = [self.reply(malicious), self.reply()]
        response = await self.http.post('/v1/chat/completions', headers=self.headers,
                                        json=self.body('Tell me a short joke'))
        self.assertEqual(200, response.status_code)
        self.executor.assert_not_awaited()
        self.assertIn('unavailable', self.model.call_args.args[0]['messages'][-1]['content'])

    async def test_model_failure_is_not_success(self):
        self.model.side_effect = HTTPException(502, 'Synthetic model outage')
        response = await self.http.post('/v1/chat/completions', headers=self.headers,
                                        json=self.body('Tell me a short joke'))
        self.assertEqual(502, response.status_code)
        self.executor.assert_not_awaited()

    async def test_endless_model_tool_calls_stop_at_existing_round_limit(self):
        calls = [{'id': 'fixture-call', 'type': 'function',
                  'function': {'name': 'not_allowed', 'arguments': '{}'}}]
        self.model.return_value = self.reply(calls)
        response = await self.http.post('/v1/chat/completions', headers=self.headers,
                                        json=self.body('Tell me a short joke'))
        self.assertEqual(502, response.status_code)
        self.assertEqual(self.aster.MAX_TOOL_ROUNDS + 1, self.model.await_count)
        self.executor.assert_not_awaited()

    async def test_progress_model_failure_is_explicit_sse_error(self):
        async def fail_stream(payload, progress):
            raise HTTPException(502, 'Synthetic stream outage')
        self.stack.enter_context(patch.object(self.aster, 'relay_progress_stream', side_effect=fail_stream))
        body = self.body('Tell me a short joke') | {'stream': True, 'progress': True}
        response = await self.http.post('/v1/chat/completions', headers=self.headers, json=body)
        self.assertEqual(200, response.status_code)
        frames = [json.loads(line[6:]) for line in response.text.splitlines()
                  if line.startswith('data: ') and line != 'data: [DONE]']
        self.assertTrue(any(x.get('type') == 'error' for x in frames))
        self.assertIn('data: [DONE]', response.text)
        self.executor.assert_not_awaited()
