import asyncio
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from a1_test_gateway import A1TestGateway, valid_body
from aster_full_path_request import payload_for
from test_aster_full_path_request import fixture

TOKEN = b"fictional-test-token"


async def run_request(body, *, token=TOKEN, path="/v1/chat/completions", method="POST", app=None):
    called = []

    async def fixture_app(scope, receive, send):
        called.append(scope["path"])
        event = await receive()
        called.append(json.loads(event["body"]))
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}", "more_body": False})

    gateway = A1TestGateway(app or fixture_app, token_sha256=hashlib.sha256(TOKEN).hexdigest())
    events = []
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(event):
        events.append(event)

    auth = [] if token is None else [(b"authorization", b"Bearer " + token)]
    await gateway({"type": "http", "path": path, "method": method,
                   "headers": auth}, receive, send)
    return events[0]["status"], called


class A1TestGatewayTests(unittest.TestCase):
    def setUp(self):
        self.body = json.dumps(payload_for(fixture())).encode()

    def test_valid_frozen_no_tool_request_reaches_only_wrapped_app(self):
        status, called = asyncio.run(run_request(self.body))
        self.assertEqual(status, 200)
        self.assertEqual(called[0], "/v1/chat/completions")
        self.assertEqual(called[1]["enabled_tools"], [])

    def test_other_route_method_and_credential_are_rejected_before_app(self):
        for options, expected in (({"path": "/v1/sysadmin/incidents/doctor"}, 404),
                                  ({"method": "GET"}, 404),
                                  ({"token": None}, 401),
                                  ({"token": b"wrong"}, 401)):
            with self.subTest(options=options):
                status, called = asyncio.run(run_request(self.body, **options))
                self.assertEqual(status, expected)
                self.assertEqual(called, [])

    def test_extra_fields_tools_system_messages_and_duplicate_keys_fail(self):
        cases = []
        extra = payload_for(fixture()); extra["tool_choice"] = "auto"; cases.append(extra)
        tools = payload_for(fixture()); tools["enabled_tools"] = ["get_lab_health"]; cases.append(tools)
        system = payload_for(fixture()); system["messages"].append({"role": "system", "content": "bad"}); cases.append(system)
        for case in cases:
            status, called = asyncio.run(run_request(json.dumps(case).encode()))
            self.assertEqual(status, 400)
            self.assertEqual(called, [])
        self.assertFalse(valid_body(self.body[:-1] + b',"enabled_tools":[]}'))

    def test_oversize_request_fails_before_app(self):
        status, called = asyncio.run(run_request(b"x" * 32769))
        self.assertEqual(status, 413)
        self.assertEqual(called, [])

    def test_websocket_does_not_reach_wrapped_app(self):
        async def forbidden_app(scope, receive, send):
            self.fail("wrapped app reached")

        gateway = A1TestGateway(forbidden_app, token_sha256=hashlib.sha256(TOKEN).hexdigest())
        events = []

        async def send(event):
            events.append(event)

        asyncio.run(gateway({"type": "websocket", "path": "/v1/chat/completions"},
                            None, send))
        self.assertEqual(events, [{"type": "websocket.close", "code": 1008}])


if __name__ == "__main__":
    unittest.main()
