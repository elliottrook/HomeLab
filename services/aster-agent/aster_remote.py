"""Private, capability-scoped Aster Remote gateway.

Browser sessions are authenticated by the existing Companion OIDC verifier.
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
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Literal

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
        "connect-src 'self' https://auth.elliottrook.com"
    ),
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(self)",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}

Action = Literal[
    "nav.up", "nav.down", "nav.left", "nav.right", "nav.select",
    "nav.back", "nav.home", "nav.context", "playback.toggle",
    "search.open", "text.send", "text.backspace", "text.clear",
    "text.cancel", "text.enter", "voice.search",
]
TEXT_ACTIONS = frozenset({"search.open", "text.send", "voice.search"})
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


class AsterRemoteGateway:
    def __init__(
        self,
        claims: Callable[[str | None], dict[str, Any]],
        static_root: Path,
        *,
        clients: dict[str, ClientIdentity],
        subject_rooms: dict[str, set[str]],
        origin: str = REMOTE_ORIGIN,
        clock: Callable[[], float] = time.time,
    ):
        self.claims = claims
        self.static_root = Path(static_root)
        self.clients = dict(clients)
        self.subject_rooms = {key: frozenset(value) for key, value in subject_rooms.items()}
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
        self.router.add_api_route(
            "/remote/manifest.webmanifest", self.asset, methods=["GET"]
        )
        self.router.add_api_route("/v1/remote/session", self.session, methods=["GET"])
        self.router.add_api_route("/v1/remote/command", self.command, methods=["POST"])
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
            "manifest.webmanifest": "application/manifest+json",
        }
        if name not in allowed:
            raise HTTPException(404, "Remote asset not found")
        headers = {"Cache-Control": "no-cache", **REMOTE_HEADERS}
        if name == "sw.js":
            headers["Service-Worker-Allowed"] = "/remote/"
        return FileResponse(self.static_root / name, media_type=allowed[name], headers=headers)

    def _browser(self, authorization: str | None) -> tuple[str, frozenset[str]]:
        result = self.claims(authorization)
        owner = result.get("owner_hash")
        if not isinstance(owner, str) or not owner:
            raise HTTPException(401, "Sign in to Aster Remote")
        rooms = self.subject_rooms.get(owner, frozenset())
        if not rooms:
            raise HTTPException(403, "No AsterTV rooms are assigned")
        return owner, rooms

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
        }

    async def session(self, authorization: str | None = Header(default=None)):
        _owner, allowed = self._browser(authorization)
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
        origin: str | None = Header(default=None),
        authorization: str | None = Header(default=None),
    ):
        self._same_origin(origin)
        owner, allowed = self._browser(authorization)
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


def from_environment(claims, static_root: Path) -> AsterRemoteGateway:
    return AsterRemoteGateway(
        claims,
        static_root,
        clients=_environment_clients(),
        subject_rooms=_environment_rooms(),
        origin=os.environ.get("ASTER_REMOTE_ORIGIN", REMOTE_ORIGIN),
    )
