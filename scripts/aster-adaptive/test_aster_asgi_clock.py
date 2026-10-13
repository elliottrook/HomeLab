import asyncio
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "services" / "aster-agent"))
from aster_agent import app, require_api_key  # noqa: E402
import aster_agent  # noqa: E402
from aster_asgi_clock import ASGIResponseClock  # noqa: E402


class AsterASGIClockTests(unittest.TestCase):
    def _request(self, fail=False):
        records = []
        wrapped = ASGIResponseClock(app, records)
        app.dependency_overrides[require_api_key] = lambda: None

        async def fake_completion(payload):
            await asyncio.sleep(0.03)
            if fail:
                from fastapi import HTTPException
                raise HTTPException(status_code=502, detail="synthetic unavailable")
            return {"choices": [{"message": {"role": "assistant", "content": "fictional answer"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}

        async def run():
            transport = httpx.ASGITransport(app=wrapped)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                begun = time.monotonic_ns()
                response = await client.post("/v1/chat/completions", json={
                    "messages": [{"role": "user", "content": "Synthetic fact question"}],
                    "enabled_tools": [], "stream": False,
                })
                return response, round((time.monotonic_ns() - begun) / 1_000_000, 3)

        try:
            with patch.object(aster_agent, "upstream_completion", fake_completion), \
                 patch.object(aster_agent.lab_operations, "chat", return_value=None), \
                 patch.object(aster_agent.lab_operations, "plan", return_value=None):
                response, client_ms = asyncio.run(run())
        finally:
            app.dependency_overrides.pop(require_api_key, None)
        return response, records, client_ms

    def test_terminal_clock_includes_synthetic_backend_wait(self):
        response, records, client_ms = self._request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["http_status"], 200)
        self.assertTrue(records[0]["terminal_observed"])
        self.assertGreaterEqual(records[0]["terminal_ms"], 30)
        self.assertEqual(response.headers["x-aster-observation-id"], records[0]["observation_id"])
        self.assertRegex(records[0]["observation_id"], r"^[0-9a-f]{32}$")
        self.assertGreaterEqual(client_ms, records[0]["terminal_ms"])
        self.assertNotIn("fictional answer", str(records))

    def test_failure_keeps_terminal_timing(self):
        response, records, client_ms = self._request(fail=True)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(records[0]["http_status"], 502)
        self.assertTrue(records[0]["terminal_observed"])
        self.assertGreaterEqual(records[0]["terminal_ms"], 30)
        self.assertEqual(response.headers["x-aster-observation-id"], records[0]["observation_id"])
        self.assertGreaterEqual(client_ms, records[0]["terminal_ms"])
        self.assertNotIn("synthetic unavailable", str(records))

    def test_companion_progress_branch_clocks_final_stream_body(self):
        from fastapi.responses import StreamingResponse

        records = []
        wrapped = ASGIResponseClock(app, records)
        app.dependency_overrides[require_api_key] = lambda: None

        def fake_progress(request, persona, allowed_tools):
            async def chunks():
                yield b'data: {"type":"content","text":"fictional"}\n\n'
                await asyncio.sleep(0.03)
                yield b'data: [DONE]\n\n'
            return StreamingResponse(chunks(), media_type="text/event-stream")

        async def run():
            transport = httpx.ASGITransport(app=wrapped)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.post("/v1/chat/completions", json={
                    "messages": [{"role": "user", "content": "Synthetic stream question"}],
                    "enabled_tools": [], "stream": True, "progress": True,
                })

        try:
            with patch.object(aster_agent, "progress_chat", fake_progress):
                response = asyncio.run(run())
        finally:
            app.dependency_overrides.pop(require_api_key, None)
        self.assertEqual(response.status_code, 200)
        self.assertIn("[DONE]", response.text)
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["terminal_observed"])
        self.assertGreaterEqual(records[0]["terminal_ms"], 30)
        self.assertEqual(response.headers["x-aster-observation-id"], records[0]["observation_id"])
        self.assertNotIn("fictional", str(records))

    def test_interrupted_asgi_stream_is_censored(self):
        records = []

        async def broken_app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"synthetic part",
                        "more_body": True})
            raise RuntimeError("synthetic interruption")

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            pass

        with self.assertRaises(RuntimeError):
            asyncio.run(ASGIResponseClock(broken_app, records)(
                {"type": "http", "path": "/v1/chat/completions"}, receive, send))
        self.assertEqual(records[0]["http_status"], 200)
        self.assertIsNotNone(records[0]["first_body_ms"])
        self.assertIsNone(records[0]["terminal_ms"])
        self.assertFalse(records[0]["terminal_observed"])


if __name__ == "__main__":
    unittest.main()
