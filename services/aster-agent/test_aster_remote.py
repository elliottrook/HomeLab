import asyncio
import ipaddress
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from aster_remote import (AsterRemoteGateway, BrowserCommand, ClientAck,
                          ClientIdentity, ClientPoll, REMOTE_HEADERS)


class Clock:
    def __init__(self): self.value = 1_800_000_000.0
    def __call__(self): return self.value


class Request:
    def __init__(self, forwarded="192.168.1.20", proxy="127.0.0.1", *, headers=None, body=b""):
        self.client = SimpleNamespace(host=proxy)
        self.headers = {"X-Forwarded-For": forwarded, **(headers or {})}
        self._body = body
    async def body(self): return self._body


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock(); self.root = tempfile.TemporaryDirectory(); root = Path(self.root.name)
        for name in ("index.html", "app.js", "styles.css", "sw.js", "aster-compass.png", "manifest.webmanifest"):
            (root / name).write_text(name)
        self.gateway = AsterRemoteGateway(
            None, root,
            clients={"AsterTV-Jen": ClientIdentity("jen-lab", "AsterTV Jen", "k" * 40)},
            subject_rooms={},
            network_rooms={ipaddress.ip_network("192.168.1.0/24"): {"jen-lab"},
                           ipaddress.ip_network("192.168.40.0/24"): {"guest"}},
            trusted_proxies={ipaddress.ip_address("127.0.0.1")},
            voice_key="v" * 40, clock=self.clock,
        )

    def tearDown(self): self.root.cleanup()
    def call(self, coroutine): return asyncio.run(coroutine)
    def command(self, payload, request=None, origin="https://aster.elliottrook.com"):
        return self.gateway.command(payload, request or Request(), origin)

    def test_session_is_network_and_room_scoped_and_content_free(self):
        result = self.call(self.gateway.session(Request()))
        self.assertEqual(result["rooms"][0]["room_id"], "jen-lab")
        self.assertFalse(result["rooms"][0]["connected"])
        self.assertFalse(result["equipment_controls"])
        self.assertEqual(result["rooms"][0]["input"], {"active": False, "sensitive": False, "title": "", "value": ""})

    def test_browser_requires_trusted_proxy_single_forwarded_ip_and_mapped_room(self):
        for request in (Request(proxy="192.168.1.20"),
                        Request(forwarded="192.168.1.20, 192.168.50.23"),
                        Request(forwarded="10.9.8.7"),
                        Request(forwarded="192.168.40.20")):
            with self.assertRaises(HTTPException) as caught: self.call(self.gateway.session(request))
            self.assertEqual(caught.exception.status_code, 403)

    def test_command_requires_exact_origin_network_room_and_shape(self):
        payload = BrowserCommand(request_id="remote-12345678", room_id="jen-lab", action="nav.up")
        self.assertEqual(self.call(self.command(payload))["status"], "accepted")
        with self.assertRaises(HTTPException) as caught: self.call(self.command(payload, origin="https://evil.example"))
        self.assertEqual(caught.exception.status_code, 403)
        with self.assertRaises(ValueError): BrowserCommand(request_id="remote-abcdefgh", room_id="jen-lab", action="nav.up", text="secret")
        with self.assertRaises(ValueError): BrowserCommand(request_id="remote-abcdefgh", room_id="jen-lab", action="search.open")

    def test_client_identity_and_at_most_once_delivery(self):
        command = BrowserCommand(request_id="remote-abcdefgh", room_id="jen-lab", action="search.open", text="space")
        self.call(self.command(command))
        poll = ClientPoll(client_id="AsterTV-Jen", room_id="jen-lab", current_page="media", playback="idle")
        delivered = self.call(self.gateway.client_poll(poll, "Bearer " + "k" * 40, "AsterTV-Jen"))
        self.assertEqual((delivered["action"], delivered["text"]), ("search.open", "space"))
        with self.assertRaises(HTTPException) as caught: self.call(self.gateway.client_poll(poll, "Bearer wrong", "AsterTV-Jen"))
        self.assertEqual(caught.exception.status_code, 401)

    def test_idempotency_and_ack(self):
        payload = BrowserCommand(request_id="remote-12345678", room_id="jen-lab", action="nav.select")
        self.call(self.command(payload)); self.call(self.command(payload))
        self.assertEqual(len(self.gateway.rooms["jen-lab"].queue), 1)
        ack = ClientAck(client_id="AsterTV-Jen", room_id="jen-lab", request_id="remote-12345678", outcome="completed")
        self.call(self.gateway.client_ack(ack, "Bearer " + "k" * 40, "AsterTV-Jen"))
        self.assertEqual(self.gateway.rooms["jen-lab"].last_outcome, "completed")

    def test_voice_uses_server_credential_and_bounded_body(self):
        response = SimpleNamespace(content=b'{"text":"dark"}', status_code=200)
        client = AsyncMock(); client.__aenter__.return_value.post.return_value = response
        with patch("aster_remote.httpx.AsyncClient", return_value=client):
            result = self.call(self.gateway.voice(Request(headers={"Content-Type":"multipart/form-data; boundary=x", "Content-Length":"4"}, body=b"test"), self.gateway.origin))
        self.assertEqual(result.status_code, 200)
        headers = client.__aenter__.return_value.post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer " + "v" * 40)
        with self.assertRaises(HTTPException) as caught:
            self.call(self.gateway.voice(Request(headers={"Content-Type":"text/plain"}, body=b"x"), self.gateway.origin))
        self.assertEqual(caught.exception.status_code, 415)

    def test_keyboard_state_and_password_content(self):
        poll = ClientPoll(client_id="AsterTV-Jen", room_id="jen-lab", current_page="keyboard", playback="idle", input_active=True, input_title="Search", input_value="Dark")
        self.gateway.rooms["jen-lab"].last_seen = self.clock.value
        async def publish():
            task = asyncio.create_task(self.gateway.client_poll(poll, "Bearer " + "k" * 40, "AsterTV-Jen"))
            await asyncio.sleep(0); task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        self.call(publish())
        self.assertEqual(self.call(self.gateway.session(Request()))["rooms"][0]["input"]["value"], "Dark")
        with self.assertRaises(ValueError):
            ClientPoll(client_id="AsterTV-Jen", room_id="jen-lab", current_page="keyboard", playback="idle", input_active=True, input_sensitive=True, input_title="Password", input_value="secret")

    def test_actions_and_csp_remain_narrow(self):
        actions = set(BrowserCommand.model_json_schema()["properties"]["action"]["enum"])
        self.assertFalse(actions & {"volume.up", "power", "shell", "jsonrpc", "home.call_service"})
        policy = REMOTE_HEADERS["Content-Security-Policy"]
        self.assertIn("connect-src 'self'", policy); self.assertNotIn("auth.elliottrook.com", policy)
        self.assertEqual(REMOTE_HEADERS["X-Frame-Options"], "DENY")


if __name__ == "__main__": unittest.main()
