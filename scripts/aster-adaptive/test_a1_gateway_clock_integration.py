"""One fictional no-tool ASGI path; no FastAPI, endpoint or model is contacted."""
import asyncio
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from a1_test_gateway import A1TestGateway
from aster_asgi_clock import ASGIResponseClock
from aster_full_path_request import payload_for
from client_display_clock import ClientDisplayClock
from join_aster_clock import join
from test_aster_full_path_request import fixture

TOKEN = b"fictional-test-token"
ID = "a" * 32


async def run_case(*, display: bool):
    seen = []
    gateway_rows = []

    async def fake_aster(scope, receive, send):
        event = await receive()
        seen.append(json.loads(event["body"]))
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b'{"fictional":"answer"}',
                    "more_body": False})

    app = A1TestGateway(
        ASGIResponseClock(fake_aster, gateway_rows, id_factory=lambda: ID),
        token_sha256=hashlib.sha256(TOKEN).hexdigest(),
    )
    body = json.dumps(payload_for(fixture())).encode()
    events = []
    delivered = False
    client = ClientDisplayClock()

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(event):
        events.append(event)
        if event["type"] == "http.response.start":
            identifiers = [v.decode("ascii") for k, v in event["headers"]
                           if k == b"x-aster-observation-id"]
            if len(identifiers) != 1:
                raise AssertionError("missing observation identity")
            client.response_identity(identifiers[0], event["status"])

    await app({"type": "http", "path": "/v1/chat/completions", "method": "POST",
               "headers": [(b"authorization", b"Bearer " + TOKEN)]}, receive, send)
    row = client.finish(terminal_displayed=display)
    return seen, events, join(row, gateway_rows[0])


class A1GatewayClockIntegrationTests(unittest.TestCase):
    def test_admitted_request_joins_after_headless_display(self):
        seen, events, joined = asyncio.run(run_case(display=True))
        self.assertEqual(seen[0]["enabled_tools"], [])
        self.assertEqual(events[0]["status"], 200)
        self.assertTrue(joined["terminal_joined"])
        self.assertFalse(joined["censored"])
        self.assertIsNone(joined["useful_answer_ms"])
        self.assertNotIn("fictional", str(joined))

    def test_gateway_completion_without_display_is_censored(self):
        _, _, joined = asyncio.run(run_case(display=False))
        self.assertFalse(joined["terminal_joined"])
        self.assertTrue(joined["censored"])
        self.assertIsNone(joined["client_terminal_display_ms"])


if __name__ == "__main__":
    unittest.main()
