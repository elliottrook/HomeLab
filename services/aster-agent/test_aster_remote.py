import asyncio
import ipaddress
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from aster_remote import (AsterRemoteGateway, BrowserCommand, ClientAck,
                          ClientIdentity, ClientPoll, ContentRead,
                          EquipmentIdentity,
                          EquipmentPoll, PhysicalEquipmentCommand,
                          REMOTE_HEADERS)


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
        for name in ("index.html", "app.js", "styles.css", "sw.js", "aster-compass.png", "astertv-remote-180.png", "astertv-remote-512.png", "manifest.webmanifest"):
            (root / name).write_text(name)
        self.gateway = AsterRemoteGateway(
            None, root,
            clients={"AsterTV-Jen": ClientIdentity("jen-lab", "AsterTV Jen", "k" * 40)},
            subject_rooms={},
            network_rooms={ipaddress.ip_network("192.168.1.0/24"): {"jen-lab"},
                           ipaddress.ip_network("192.168.20.20/32"): {"jen-lab"},
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

    def test_administrator_tailscale_router_is_explicitly_mapped(self):
        result = self.call(self.gateway.session(Request(forwarded="192.168.20.20")))
        self.assertEqual([row["room_id"] for row in result["rooms"]], ["jen-lab"])

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

    def test_content_state_is_current_content_free_and_equipment_scoped(self):
        gateway = AsterRemoteGateway(
            None, self.gateway.static_root,
            clients={"AsterTV-Jen": ClientIdentity(
                "jen-lab", "AsterTV Jen", "k" * 40)},
            equipment_clients={"HA-Family": EquipmentIdentity(
                "jen-lab", "Family equipment", "e" * 40,
                frozenset({"equipment.power_on"}))},
            subject_rooms={}, network_rooms={}, trusted_proxies=set(),
            clock=self.clock,
        )
        content = {
            "schema": "astertv-room-playback.v1",
            "session_id": "boot-12345678", "sequence": 1,
            "observed_epoch": int(self.clock.value),
            "expires_epoch": int(self.clock.value) + 30,
            "available": True, "playback_state": "playing",
            "content_class": "Movie", "page_id": "movie-details",
            "screensaver_active": False,
        }
        poll = ClientPoll(
            client_id="AsterTV-Jen", room_id="jen-lab",
            current_page="movies", playback="playing", content_state=content,
        )

        async def publish():
            task = asyncio.create_task(gateway.client_poll(
                poll, "Bearer " + "k" * 40, "AsterTV-Jen"))
            await asyncio.sleep(0); task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        self.call(publish())
        request = ContentRead(client_id="HA-Family", room_id="jen-lab")
        value = self.call(gateway.equipment_content(
            request, "Bearer " + "e" * 40, "HA-Family"))
        self.assertEqual((value["room_id"], value["content_class"]),
                         ("jen-lab", "Movie"))
        self.assertEqual(set(value), {
            "room_id", "schema", "session_id", "sequence", "observed_epoch",
            "expires_epoch", "available", "playback_state", "content_class",
            "page_id", "screensaver_active",
        })
        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.equipment_content(
                request, "Bearer wrong", "HA-Family"))
        self.assertEqual(caught.exception.status_code, 401)

        replay = ClientPoll(
            client_id="AsterTV-Jen", room_id="jen-lab",
            current_page="movies", playback="playing", content_state=content,
        )
        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.client_poll(
                replay, "Bearer " + "k" * 40, "AsterTV-Jen"))
        self.assertEqual(caught.exception.status_code, 409)

        stale_poll = ClientPoll(
            client_id="AsterTV-Jen", room_id="jen-lab",
            current_page="movies", playback="playing",
            content_state={**content, "session_id": "boot-87654321",
                           "observed_epoch": int(self.clock.value) - 31,
                           "expires_epoch": int(self.clock.value) - 1},
        )
        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.client_poll(
                stale_poll, "Bearer " + "k" * 40, "AsterTV-Jen"))
        self.assertEqual(caught.exception.status_code, 409)

        self.clock.value += 31
        stale = self.call(gateway.equipment_content(
            request, "Bearer " + "e" * 40, "HA-Family"))
        self.assertEqual(stale.status_code, 204)

    def test_actions_and_csp_remain_narrow(self):
        actions = set(BrowserCommand.model_json_schema()["properties"]["action"]["enum"])
        self.assertEqual(actions & {row for row in actions if row.startswith("equipment.")}, {
            "equipment.power_on", "equipment.power_off",
            "equipment.volume_up", "equipment.volume_down",
            "equipment.mute_on", "equipment.mute_off",
        })
        self.assertFalse(actions & {"volume.up", "power", "shell", "jsonrpc", "home.call_service"})
        policy = REMOTE_HEADERS["Content-Security-Policy"]
        self.assertIn("connect-src 'self'", policy); self.assertNotIn("auth.elliottrook.com", policy)
        self.assertEqual(REMOTE_HEADERS["X-Frame-Options"], "DENY")

    def test_equipment_actions_require_separate_live_room_capability(self):
        denied = BrowserCommand(request_id="remote-equipdeny", room_id="jen-lab",
                                action="equipment.power_on")
        with self.assertRaises(HTTPException) as caught:
            self.call(self.command(denied))
        self.assertEqual(caught.exception.status_code, 403)

        gateway = AsterRemoteGateway(
            None, self.gateway.static_root,
            clients={"AsterTV-Jen": ClientIdentity("jen-lab", "AsterTV Jen", "k" * 40)},
            equipment_clients={"HA-Family": EquipmentIdentity(
                "jen-lab", "Family equipment", "e" * 40,
                frozenset({"equipment.power_on", "equipment.power_off"}))},
            subject_rooms={},
            network_rooms={ipaddress.ip_network("192.168.1.0/24"): {"jen-lab"}},
            trusted_proxies={ipaddress.ip_address("127.0.0.1")}, clock=self.clock,
        )
        request = Request()
        self.assertFalse(self.call(gateway.session(request))["rooms"][0]["equipment"]["connected"])
        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.command(denied, request, gateway.origin))
        self.assertEqual(caught.exception.status_code, 503)

        unavailable = EquipmentPoll(client_id="HA-Family", room_id="jen-lab",
                                    power="unavailable", volume_level=None, muted=None)
        async def publish_unavailable():
            task = asyncio.create_task(gateway.equipment_poll(
                unavailable, "Bearer " + "e" * 40, "HA-Family"))
            await asyncio.sleep(0); task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        self.call(publish_unavailable())
        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.command(denied, request, gateway.origin))
        self.assertEqual(caught.exception.status_code, 503)
        gateway.rooms["jen-lab"].equipment_condition = asyncio.Condition()

        poll = EquipmentPoll(client_id="HA-Family", room_id="jen-lab", power="on",
                             volume_level=0.59, muted=False)
        async def publish():
            task = asyncio.create_task(gateway.equipment_poll(
                poll, "Bearer " + "e" * 40, "HA-Family"))
            await asyncio.sleep(0); task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        self.call(publish())
        self.assertTrue(self.call(gateway.session(request))["rooms"][0]["equipment"]["connected"])
        self.assertEqual(self.call(gateway.command(denied, request, gateway.origin))["status"], "accepted")
        self.assertEqual(len(gateway.rooms["jen-lab"].queue), 0)
        self.assertEqual(len(gateway.rooms["jen-lab"].equipment_queue), 1)

        forbidden = BrowserCommand(request_id="remote-equipmute", room_id="jen-lab",
                                   action="equipment.mute_on")
        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.command(forbidden, request, gateway.origin))
        self.assertEqual(caught.exception.status_code, 403)

    def test_physical_equipment_is_same_room_state_aware_and_explicit(self):
        gateway = AsterRemoteGateway(
            None, self.gateway.static_root,
            clients={"AsterTV-Bedroom": ClientIdentity(
                "bedroom", "AsterTV Bedroom", "k" * 40)},
            equipment_clients={"HA-Bedroom": EquipmentIdentity(
                "bedroom", "Bedroom equipment", "e" * 40,
                frozenset({
                    "equipment.power_on", "equipment.power_off",
                    "equipment.volume_up", "equipment.volume_down",
                    "equipment.mute_on", "equipment.mute_off",
                }))},
            subject_rooms={}, network_rooms={}, trusted_proxies=set(),
            clock=self.clock,
        )
        room = gateway.rooms["bedroom"]
        room.equipment_last_seen = self.clock.value
        room.equipment_power = "on"
        room.equipment_volume_level = .25
        room.equipment_muted = False

        async def submit(control, request_id):
            return await gateway.client_equipment(
                PhysicalEquipmentCommand(
                    client_id="AsterTV-Bedroom", room_id="bedroom",
                    request_id=request_id, control=control,
                ),
                "Bearer " + "k" * 40, "AsterTV-Bedroom",
            )

        self.assertEqual(self.call(submit("mute_toggle", "physical-mute0001"))["status"],
                         "accepted")
        self.assertEqual(room.equipment_queue[-1].action, "equipment.mute_on")
        self.assertEqual(self.call(submit("power_toggle", "physical-power001"))["status"],
                         "accepted")
        self.assertEqual(room.equipment_queue[-1].action, "equipment.power_off")
        self.assertEqual(self.call(submit("volume_up", "physical-volume01"))["status"],
                         "accepted")
        self.assertEqual(room.equipment_queue[-1].action, "equipment.volume_up")

        with self.assertRaises(HTTPException) as caught:
            self.call(gateway.client_equipment(
                PhysicalEquipmentCommand(
                    client_id="AsterTV-Bedroom", room_id="bedroom",
                    request_id="physical-wrong001", control="volume_down",
                ), "Bearer wrong", "AsterTV-Bedroom"))
        self.assertEqual(caught.exception.status_code, 401)

        room.equipment_muted = None
        with self.assertRaises(HTTPException) as caught:
            self.call(submit("mute_toggle", "physical-mute0002"))
        self.assertEqual(caught.exception.status_code, 503)


if __name__ == "__main__": unittest.main()
