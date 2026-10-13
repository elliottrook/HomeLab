import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aster_asgi_clock import ASGIResponseClock


class ObservationIdTests(unittest.TestCase):
    def test_opaque_id_joins_response_to_content_free_clock_record(self):
        records = []
        messages = []

        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200,
                        "headers": [(b"X-Aster-Observation-Id", b"untrusted")]})
            await send({"type": "http.response.body", "body": b"fictional answer",
                        "more_body": False})

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        wrapped = ASGIResponseClock(app, records, id_factory=lambda: "a" * 32)
        asyncio.run(wrapped({"type": "http", "path": "/v1/chat/completions"}, receive, send))
        self.assertEqual(dict(messages[0]["headers"])[b"x-aster-observation-id"], b"a" * 32)
        self.assertEqual(len(messages[0]["headers"]), 1)
        self.assertEqual(records[0]["observation_id"], "a" * 32)
        self.assertTrue(records[0]["terminal_observed"])
        self.assertNotIn("fictional answer", str(records))

    def test_interrupted_stream_keeps_id_but_not_a_fake_completion(self):
        records = []
        messages = []

        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"partial", "more_body": True})
            raise RuntimeError("synthetic interruption")

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        wrapped = ASGIResponseClock(app, records, id_factory=lambda: "b" * 32)
        with self.assertRaises(RuntimeError):
            asyncio.run(wrapped({"type": "http", "path": "/v1/chat/completions"}, receive, send))
        self.assertEqual(dict(messages[0]["headers"])[b"x-aster-observation-id"], b"b" * 32)
        self.assertEqual(records[0]["observation_id"], "b" * 32)
        self.assertFalse(records[0]["terminal_observed"])
        self.assertIsNone(records[0]["terminal_ms"])

    def test_invalid_factory_output_never_calls_app(self):
        calls = []

        async def app(scope, receive, send):
            calls.append(True)

        wrapped = ASGIResponseClock(app, [], id_factory=lambda: "untrusted\r\nheader")
        with self.assertRaisesRegex(ValueError, "observation id"):
            asyncio.run(wrapped({"type": "http", "path": "/v1/chat/completions"}, None, None))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
