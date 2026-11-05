"""Private, capability-scoped Aster Remote gateway.

Browser sessions are authorized by their source network at the trusted proxy.
Each television polls outbound with its own key.  The gateway transports only
the enumerated semantic actions below; it is deliberately not a JSON-RPC,
Home Assistant, equipment or shell proxy.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hmac
import ipaddress
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator


REMOTE_ORIGIN = "https://aster.elliottrook.com"
COMMAND_LIFETIME_SECONDS = 15
CONNECTED_SECONDS = 35
MAX_QUEUE = 32
REMOTE_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; base-uri 'none'; object-src 'none'; "
        "frame-ancestors 'none'; form-action 'none'; img-src 'self'; "
        "script-src 'self'; style-src 'self'; worker-src 'self'; "
        "manifest-src 'self'; media-src 'self' blob:; "
        "connect-src 'self'"
    ),
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(self)",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}

Action = Literal[
    "nav.up", "nav.down", "nav.left", "nav.right", "nav.select",
    "nav.back", "nav.home", "nav.context", "playback.toggle",
    "search.open", "text.send", "text.replace", "text.backspace", "text.clear",
    "text.cancel", "text.enter", "voice.search",
]
TEXT_ACTIONS = frozenset({"search.open", "text.send", "text.replace", "voice.search"})
NO_TEXT_ACTIONS = frozenset({
    "nav.up", "nav.down", "nav.left", "nav.right", "nav.select",
    "nav.back", "nav.home", "nav.context", "playback.toggle",
    "text.backspace", "text.clear", "text.cancel", "text.enter",
})


class BrowserCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{7,63}$")
    room_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")
    action: Action
    text: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def exact_shape(self):
        if self.action in TEXT_ACTIONS and not self.text:
            raise ValueError("text-required")
        if self.action in NO_TEXT_ACTIONS and self.text is not None:
            raise ValueError("text-not-allowed")
        return self


class ClientPoll(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,31}$")
    room_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")
    current_page: Literal[
        "home", "media", "movies", "tv", "music", "books", "news",
        "youtube", "requests", "cameras", "search", "keyboard", "other",
    ]
    playback: Literal["idle", "playing", "paused"]
    input_active: bool = False
    input_sensitive: bool = False
    input_title: str = Field(default="", max_length=128)
    input_value: str = Field(default="", max_length=512)

    @model_validator(mode="after")
    def protect_sensitive_input(self):
        if self.input_sensitive and (self.input_title or self.input_value):
            raise ValueError("sensitive-input-content-forbidden")
        if not self.input_active and (self.input_sensitive or self.input_title or self.input_value):
            raise ValueError("inactive-input-content-forbidden")
        return self


class ClientAck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{0,31}$")
    room_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")
    request_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{7,63}$")
    outcome: Literal[
        "completed", "denied", "expired", "unavailable", "invalid-state",
    ]


@dataclass(frozen=True)
class ClientIdentity:
    room_id: str
    label: str
    key: str


@dataclass
class QueuedCommand:
    request_id: str
    action: str
    text: str | None
    expires_at: float


@dataclass
class RoomRuntime:
    queue: deque[QueuedCommand] = field(default_factory=deque)
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)
    last_seen: float = 0.0
    current_page: str = "other"
    playback: str = "idle"
    last_outcome: str | None = None
    last_request_id: str | None = None
    input_active: bool = False
    input_sensitive: bool = False
    input_title: str = ""
    input_value: str = ""


class AsterRemoteGateway:
    def __init__(
        self,
        claims: Callable[[str | None], dict[str, Any]] | None,
        static_root: Path,
        *,
        clients: dict[str, ClientIdentity],
        subject_rooms: dict[str, set[str]],
        network_rooms: dict[ipaddress.IPv4Network, set[str]] | None = None,
        trusted_proxies: set[ipaddress.IPv4Address] | None = None,
        voice_url: str = "http://192.168.70.14:9130/v1/stt",
        voice_key: str = "",
        origin: str = REMOTE_ORIGIN,
        clock: Callable[[], float] = time.time,
    ):
        self.claims = claims
        self.static_root = Path(static_root)
        self.clients = dict(clients)
        self.subject_rooms = {key: frozenset(value) for key, value in subject_rooms.items()}
        self.network_rooms = {
            network: frozenset(rooms) for network, rooms in (network_rooms or {}).items()
        }
        self.trusted_proxies = frozenset(trusted_proxies or set())
        self.voice_url = voice_url
        self.voice_key = voice_key
        self.origin = origin.rstrip("/")
        self.clock = clock
        self.rooms = {identity.room_id: RoomRuntime() for identity in clients.values()}
        self.seen: dict[str, float] = {}
        self.rates: dict[str, deque[float]] = defaultdict(deque)
        self.router = APIRouter()
        self._routes()

    def _routes(self):
        self.router.add_api_route("/remote", self.index, methods=["GET"])
        self.router.add_api_route("/remote/", self.index, methods=["GET"])
        self.router.add_api_route("/remote/app.js", self.asset, methods=["GET"])
        self.router.add_api_route("/remote/styles.css", self.asset, methods=["GET"])
        self.router.add_api_route("/remote/sw.js", self.asset, methods=["GET"])
        self.router.add_api_route("/remote/aster-compass.png", self.asset, methods=["GET"])
        self.router.add_api_route(
            "/remote/manifest.webmanifest", self.asset, methods=["GET"]
        )
        self.router.add_api_route("/v1/remote/session", self.session, methods=["GET"])
        self.router.add_api_route("/v1/remote/command", self.command, methods=["POST"])
        self.router.add_api_route("/v1/remote/voice", self.voice, methods=["POST"])
        self.router.add_api_route(
            "/v1/remote/client/poll", self.client_poll, methods=["POST"]
        )
        self.router.add_api_route(
            "/v1/remote/client/ack", self.client_ack, methods=["POST"]
        )

    async def index(self) -> FileResponse:
        return FileResponse(
            self.static_root / "index.html",
            headers={"Cache-Control": "no-cache", **REMOTE_HEADERS},
        )

    async def asset(self, request: Request) -> FileResponse:
        name = request.url.path.rsplit("/", 1)[-1]
        allowed = {
            "app.js": "application/javascript",
            "styles.css": "text/css",
            "sw.js": "application/javascript",
            "aster-compass.png": "image/png",
            "manifest.webmanifest": "application/manifest+json",
        }
        if name not in allowed:
            raise HTTPException(404, "Remote asset not found")
        headers = {"Cache-Control": "no-cache", **REMOTE_HEADERS}
        if name == "sw.js":
            headers["Service-Worker-Allowed"] = "/remote/"
        return FileResponse(self.static_root / name, media_type=allowed[name], headers=headers)

    def _browser(self, request: Request) -> tuple[str, frozenset[str]]:
        try:
            proxy = ipaddress.ip_address(request.client.host if request.client else "")
        except ValueError as error:
            raise HTTPException(403, "Remote proxy denied") from error
        if proxy not in self.trusted_proxies:
            raise HTTPException(403, "Remote proxy denied")
        forwarded = request.headers.get("X-Forwarded-For", "")
        if not forwarded or "," in forwarded:
            raise HTTPException(403, "Remote client address denied")
        try:
            client = ipaddress.ip_address(forwarded.strip())
        except ValueError as error:
            raise HTTPException(403, "Remote client address denied") from error
        for network, rooms in self.network_rooms.items():
            if client in network:
                allowed = frozenset(room for room in rooms if room in self.rooms)
                if not allowed:
                    raise HTTPException(403, "No AsterTV rooms are assigned")
                return "network:" + network.with_prefixlen, allowed
        raise HTTPException(403, "Remote network denied")

    def _same_origin(self, origin: str | None):
        if origin != self.origin:
            raise HTTPException(403, "Remote origin denied")

    def _rate(self, owner: str):
        now = self.clock()
        rows = self.rates[owner]
        while rows and rows[0] <= now - 10:
            rows.popleft()
        if len(rows) >= 40 or sum(value > now - 1 for value in rows) >= 10:
            raise HTTPException(429, "Remote command rate exceeded")
        rows.append(now)

    def _client(
        self, client_id: str, room_id: str, authorization: str | None,
        header_client: str | None,
    ) -> ClientIdentity:
        identity = self.clients.get(client_id)
        supplied = authorization.removeprefix("Bearer ") if authorization else ""
        if (
            identity is None
            or header_client != client_id
            or identity.room_id != room_id
            or not hmac.compare_digest(identity.key, supplied)
        ):
            raise HTTPException(401, "Invalid AsterTV remote client")
        return identity

    def _room_state(self, room_id: str, identity: ClientIdentity | None = None):
        room = self.rooms[room_id]
        return {
            "room_id": room_id,
            "label": identity.label if identity else room_id,
            "connected": room.last_seen > self.clock() - CONNECTED_SECONDS,
            "current_page": room.current_page,
            "playback": room.playback,
            "last_outcome": room.last_outcome,
            "input": {
                "active": room.input_active,
                "sensitive": room.input_sensitive,
                "title": room.input_title,
                "value": room.input_value,
            },
        }

    async def session(self, request: Request):
        _owner, allowed = self._browser(request)
        identities = {row.room_id: row for row in self.clients.values()}
        return {
            "status": "ready",
            "rooms": [
                self._room_state(room_id, identities.get(room_id))
                for room_id in sorted(allowed)
                if room_id in self.rooms
            ],
            "equipment_controls": False,
        }

    async def command(
        self,
        payload: BrowserCommand,
        request: Request,
        origin: str | None = Header(default=None),
    ):
        self._same_origin(origin)
        owner, allowed = self._browser(request)
        if payload.room_id not in allowed or payload.room_id not in self.rooms:
            raise HTTPException(403, "AsterTV room denied")
        self._rate(owner)
        now = self.clock()
        self.seen = {key: expiry for key, expiry in self.seen.items() if expiry > now}
        if payload.request_id in self.seen:
            return {"status": "accepted", "request_id": payload.request_id}
        room = self.rooms[payload.room_id]
        if len(room.queue) >= MAX_QUEUE:
            raise HTTPException(503, "AsterTV remote queue is busy")
        self.seen[payload.request_id] = now + COMMAND_LIFETIME_SECONDS
        room.queue.append(QueuedCommand(
            payload.request_id, payload.action, payload.text,
            now + COMMAND_LIFETIME_SECONDS,
        ))
        async with room.condition:
            room.condition.notify_all()
        return {"status": "accepted", "request_id": payload.request_id}

    async def voice(self, request: Request, origin: str | None = Header(default=None)):
        self._same_origin(origin)
        self._browser(request)
        content_type = request.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data;"):
            raise HTTPException(415, "Remote voice content type denied")
        length = request.headers.get("Content-Length")
        if length and (not length.isdecimal() or int(length) > 15 * 1024 * 1024):
            raise HTTPException(413, "Remote voice exceeds the maximum permitted size")
        body = await request.body()
        if not body or len(body) > 15 * 1024 * 1024:
            raise HTTPException(413 if body else 400, "Remote voice body invalid")
        if len(self.voice_key) < 32:
            raise HTTPException(503, "Remote voice is not configured")
        try:
            async with httpx.AsyncClient(timeout=40) as client:
                response = await client.post(
                    self.voice_url, content=body,
                    headers={"Content-Type": content_type,
                             "Authorization": "Bearer " + self.voice_key},
                )
        except httpx.HTTPError as error:
            raise HTTPException(502, "Remote voice is unavailable") from error
        if len(response.content) > 65536:
            raise HTTPException(502, "Remote voice response invalid")
        return Response(content=response.content, status_code=response.status_code,
                        media_type="application/json")

    async def client_poll(
        self,
        payload: ClientPoll,
        authorization: str | None = Header(default=None),
        x_astertv_client: str | None = Header(default=None),
    ):
        self._client(payload.client_id, payload.room_id, authorization, x_astertv_client)
        room = self.rooms[payload.room_id]
        room.last_seen = self.clock()
        room.current_page = payload.current_page
        room.playback = payload.playback
        room.input_active = payload.input_active
        room.input_sensitive = payload.input_sensitive
        room.input_title = payload.input_title
        room.input_value = payload.input_value
        deadline = time.monotonic() + 20
        while True:
            now = self.clock()
            while room.queue and room.queue[0].expires_at <= now:
                room.queue.popleft()
            if room.queue:
                command = room.queue.popleft()
                return {
                    "request_id": command.request_id,
                    "action": command.action,
                    "text": command.text,
                    "expires_at": datetime.fromtimestamp(
                        command.expires_at, timezone.utc
                    ).isoformat(),
                }
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return Response(status_code=204)
            async with room.condition:
                try:
                    await asyncio.wait_for(room.condition.wait(), min(remaining, 1.0))
                except TimeoutError:
                    pass
            room.last_seen = self.clock()

    async def client_ack(
        self,
        payload: ClientAck,
        authorization: str | None = Header(default=None),
        x_astertv_client: str | None = Header(default=None),
    ):
        self._client(payload.client_id, payload.room_id, authorization, x_astertv_client)
        room = self.rooms[payload.room_id]
        room.last_seen = self.clock()
        room.last_outcome = payload.outcome
        room.last_request_id = payload.request_id
        return {"status": "recorded"}


def _environment_clients() -> dict[str, ClientIdentity]:
    raw = json.loads(os.environ.get("ASTER_REMOTE_CLIENTS", "{}"))
    if not isinstance(raw, dict):
        raise ValueError("invalid-remote-clients")
    result = {}
    for client_id, row in raw.items():
        if (
            not isinstance(row, dict)
            or set(row) != {"room_id", "label", "key"}
            or not all(isinstance(row[key], str) and row[key] for key in row)
            or len(row["key"]) < 32
        ):
            raise ValueError("invalid-remote-client")
        result[client_id] = ClientIdentity(**row)
    return result


def _environment_rooms() -> dict[str, set[str]]:
    raw = json.loads(os.environ.get("ASTER_REMOTE_SUBJECT_ROOMS", "{}"))
    if not isinstance(raw, dict):
        raise ValueError("invalid-remote-subject-rooms")
    result = {}
    for subject, rooms in raw.items():
        if not isinstance(subject, str) or not isinstance(rooms, list):
            raise ValueError("invalid-remote-subject-room")
        result[subject] = {room for room in rooms if isinstance(room, str)}
    return result


def _environment_network_rooms() -> dict[ipaddress.IPv4Network, set[str]]:
    raw = json.loads(os.environ.get("ASTER_REMOTE_NETWORK_ROOMS", "{}"))
    if not isinstance(raw, dict):
        raise ValueError("invalid-remote-network-rooms")
    result = {}
    for value, rooms in raw.items():
        try:
            network = ipaddress.ip_network(value, strict=True)
        except ValueError as error:
            raise ValueError("invalid-remote-network") from error
        if network.version != 4 or not isinstance(rooms, list) or not all(
            isinstance(room, str) and room for room in rooms
        ):
            raise ValueError("invalid-remote-network-room")
        result[network] = set(rooms)
    return result


def _environment_trusted_proxies() -> set[ipaddress.IPv4Address]:
    result = set()
    for value in os.environ.get("ASTER_REMOTE_TRUSTED_PROXIES", "").split(","):
        if not value.strip(): continue
        address = ipaddress.ip_address(value.strip())
        if address.version != 4: raise ValueError("invalid-remote-trusted-proxy")
        result.add(address)
    return result


def from_environment(claims, static_root: Path) -> AsterRemoteGateway:
    return AsterRemoteGateway(
        claims,
        static_root,
        clients=_environment_clients(),
        subject_rooms=_environment_rooms(),
        network_rooms=_environment_network_rooms(),
        trusted_proxies=_environment_trusted_proxies(),
        voice_url=os.environ.get(
            "ASTER_REMOTE_VOICE_URL", "http://192.168.70.14:9130/v1/stt"
        ),
        voice_key=os.environ.get("ASTER_REMOTE_SPEECH_API_KEY", ""),
        origin=os.environ.get("ASTER_REMOTE_ORIGIN", REMOTE_ORIGIN),
    )
