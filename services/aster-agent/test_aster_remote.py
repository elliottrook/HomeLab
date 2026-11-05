import asyncio
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from aster_remote import (
    AsterRemoteGateway, BrowserCommand, ClientAck, ClientIdentity, ClientPoll,
)


class Clock:
    def __init__(self):
        self.value = 1_800_000_000.0

    def __call__(self):
        return self.value


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.root = tempfile.TemporaryDirectory()
        root = Path(self.root.name)
        for name in ("index.html", "app.js", "styles.css", "sw.js", "manifest.webmanifest"):
            (root / name).write_text(name)

        def claims(value):
            if value != "Bearer owner":
                raise HTTPException(401, "bad")
            return {"owner_hash": "owner-hash"}

        self.gateway = AsterRemoteGateway(
            claims, root,
            clients={
                "AsterTV-Jen": ClientIdentity("jen-lab", "AsterTV Jen", "k" * 40),
            },
            subject_rooms={"owner-hash": {"jen-lab"}},
            clock=self.clock,
        )

    def tearDown(self):
        self.root.cleanup()

    def call(self, coroutine):
        return asyncio.run(coroutine)

    def test_session_is_room_scoped_and_content_free(self):
        result = self.call(self.gateway.session("Bearer owner"))
        self.assertEqual(result["rooms"][0]["room_id"], "jen-lab")
        self.assertFalse(result["rooms"][0]["connected"])
        self.assertFalse(result["equipment_controls"])
        self.assertNotIn("title", str(result).casefold())

    def test_command_requires_exact_origin_owner_room_and_shape(self):
        payload = BrowserCommand(
            request_id="remote-12345678", room_id="jen-lab", action="nav.up"
        )
        result = self.call(self.gateway.command(
            payload, "https://aster.elliottrook.com", "Bearer owner"
        ))
        self.assertEqual(result["status"], "accepted")
        with self.assertRaises(HTTPException) as caught:
            self.call(self.gateway.command(payload, "https://evil.example", "Bearer owner"))
        self.assertEqual(caught.exception.status_code, 403)
        with self.assertRaises(ValueError):
            BrowserCommand(
                request_id="remote-abcdefgh", room_id="jen-lab",
                action="nav.up", text="secret",
            )
        with self.assertRaises(ValueError):
            BrowserCommand(
                request_id="remote-abcdefgh", room_id="jen-lab",
                action="search.open",
            )

    def test_client_identity_and_at_most_once_delivery(self):
        command = BrowserCommand(
            request_id="remote-abcdefgh", room_id="jen-lab",
            action="search.open", text="space",
        )
        self.call(self.gateway.command(
            command, "https://aster.elliottrook.com", "Bearer owner"
        ))
        poll = ClientPoll(
            client_id="AsterTV-Jen", room_id="jen-lab",
            current_page="media", playback="idle",
        )
        delivered = self.call(self.gateway.client_poll(
            poll, "Bearer " + "k" * 40, "AsterTV-Jen"
        ))
        self.assertEqual(delivered["action"], "search.open")
        self.assertEqual(delivered["text"], "space")
        self.assertEqual(len(self.gateway.rooms["jen-lab"].queue), 0)
        with self.assertRaises(HTTPException) as caught:
            self.call(self.gateway.client_poll(poll, "Bearer wrong", "AsterTV-Jen"))
        self.assertEqual(caught.exception.status_code, 401)

    def test_idempotency_rate_limit_expiry_and_ack(self):
        payload = BrowserCommand(
            request_id="remote-12345678", room_id="jen-lab", action="nav.select"
        )
        self.call(self.gateway.command(
            payload, "https://aster.elliottrook.com", "Bearer owner"
        ))
        self.call(self.gateway.command(
            payload, "https://aster.elliottrook.com", "Bearer owner"
        ))
        self.assertEqual(len(self.gateway.rooms["jen-lab"].queue), 1)
        ack = ClientAck(
            client_id="AsterTV-Jen", room_id="jen-lab",
            request_id="remote-12345678", outcome="completed",
        )
        self.call(self.gateway.client_ack(
            ack, "Bearer " + "k" * 40, "AsterTV-Jen"
        ))
        self.assertEqual(self.gateway.rooms["jen-lab"].last_outcome, "completed")

    def test_actions_exclude_equipment_shell_and_general_rpc(self):
        schema = BrowserCommand.model_json_schema()
        actions = set(schema["properties"]["action"]["enum"])
        self.assertFalse(actions & {
            "volume.up", "volume.down", "mute", "power", "shell",
            "jsonrpc", "home.call_service",
        })


if __name__ == "__main__":
    unittest.main()
