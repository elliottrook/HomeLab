"""Capability-scoped AsterTV intent gateway.

The gateway classifies a deliberately small television command language.  It
does not expose Aster chat, model tools, Jellyfin credentials, Home Assistant
service calls or Kodi JSON-RPC.  A client must execute the returned semantic
intent through its own separately authorized adapters.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


LOGGER = logging.getLogger("aster.astertv")
CLIENT_ID = "AsterTV-Jen"
ROOM_ID = "jen-lab"
ALLOWED_PROFILES = frozenset({"jason"})
MAX_LIFETIME_SECONDS = 15
MAX_CLOCK_SKEW_SECONDS = 5

PAGE_TARGETS = {
    "camera": "cameras", "cameras": "cameras",
    "media": "media", "movies": "movies", "movie": "movies",
    "television": "tv", "tv": "tv", "music": "music",
    "books": "books", "youtube": "youtube", "requests": "requests",
    "home": "home", "news": "news",
}

INJECTION = re.compile(
    r"\b(?:ignore (?:all |the )?(?:previous|prior)|system prompt|developer "
    r"message|reveal (?:the )?(?:token|key|credential)|api[_ -]?key|password|"
    r"sudo|shell|terminal|command line|curl|wget|json[- ]?rpc|home assistant "
    r"service|execute arbitrary|bypass|jailbreak)\b",
    re.I,
)
TITLE = re.compile(r"^[\w][\w .,'’&:!+\-]{0,159}$", re.UNICODE)


class IntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{7,63}$")
    client_id: str = Field(max_length=32)
    room_id: str = Field(max_length=32)
    profile_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,47}$")
    origin_page: str = Field(pattern=r"^[a-z][a-z0-9-]{0,47}$")
    utterance: str = Field(min_length=1, max_length=512)
    issued_at: datetime
    expires_at: datetime

    @field_validator("issued_at", "expires_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone-required")
        return value.astimezone(timezone.utc)


class IntentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: Literal["ready", "denied", "ambiguous"]
    intent: Literal[
        "media.search", "page.open", "playback.play_named",
        "playback.resume_named", "news.play", "news.open",
        "home.alias_execute", "none",
    ]
    surface: Literal["direct", "search"]
    response: str = Field(max_length=160)
    arguments: dict[str, str]
    confirmation: Literal["none", "visible", "required"]


class IntentEngine:
    """Deterministic authority layer; model output is never trusted here."""

    def __init__(self, home_aliases: dict[str, dict[str, str]] | None = None):
        self.home_aliases = {}
        for alias, policy in (home_aliases or {}).items():
            normalized = self._phrase(alias)
            if (not re.fullmatch(r"[a-z][a-z0-9 ]{0,63}", normalized)
                    or set(policy) != {"action", "confirmation"}
                    or policy["action"] not in {"on", "off"}
                    or policy["confirmation"] not in {"visible", "required"}):
                raise ValueError("invalid-home-alias-policy")
            self.home_aliases[normalized] = dict(policy)

    @staticmethod
    def _phrase(value: str) -> str:
        return " ".join(value.casefold().strip().split())

    @staticmethod
    def _title(value: str) -> str | None:
        value = " ".join(value.strip(" .?!").split())
        return value if TITLE.fullmatch(value) else None

    @staticmethod
    def _result(request_id: str, *, status: str, intent: str = "none",
                surface: str = "direct", response: str,
                arguments: dict[str, str] | None = None,
                confirmation: str = "none") -> IntentResponse:
        return IntentResponse(
            request_id=request_id, status=status, intent=intent,
            surface=surface, response=response,
            arguments=arguments or {}, confirmation=confirmation,
        )

    def classify(self, request: IntentRequest) -> IntentResponse:
        text = self._phrase(request.utterance)
        if INJECTION.search(text):
            return self._result(
                request.request_id, status="denied",
                response="That command is not available on AsterTV.",
            )

        if re.fullmatch(r"(?:play|start)(?: the)? news(?: digest)?", text):
            return self._result(
                request.request_id, status="ready", intent="news.play",
                response="Playing the news digest.", confirmation="visible",
            )
        if re.fullmatch(r"(?:open|show)(?: the)? news(?: digest)?", text):
            return self._result(
                request.request_id, status="ready", intent="news.open",
                response="Opening the news digest.",
            )

        page = re.fullmatch(
            r"(?:show me|open|show|go to)(?: the)? ([a-z ]+?)(?: page)?", text
        )
        if page:
            target = PAGE_TARGETS.get(page.group(1).strip())
            if target:
                return self._result(
                    request.request_id, status="ready", intent="page.open",
                    response="Opening " + target.title() + ".",
                    arguments={"target": target},
                )

        resume = re.fullmatch(
            r"(?:play|resume)(?: the)? next episode of (.+)", text
        )
        if resume:
            title = self._title(resume.group(1))
            if title:
                return self._result(
                    request.request_id, status="ready",
                    intent="playback.resume_named",
                    response="Resuming the next episode of " + title + ".",
                    arguments={"title": title, "media_type": "tv"},
                    confirmation="visible",
                )

        search = re.fullmatch(
            r"(?:search for|find|show me)(?: (?:a |some ))?(.+)", text
        )
        if search:
            query = self._title(search.group(1))
            if query:
                return self._result(
                    request.request_id, status="ready", intent="media.search",
                    surface="search", response="Searching for " + query + ".",
                    arguments={"query": query},
                )

        play = re.fullmatch(r"(?:play|watch) (.+)", text)
        if play:
            title = self._title(play.group(1))
            if title:
                return self._result(
                    request.request_id, status="ready",
                    intent="playback.play_named",
                    response="Playing " + title + ".",
                    arguments={"title": title}, confirmation="visible",
                )

        home = re.fullmatch(r"(?:turn|switch) (on|off) (?:the )?(.+)", text)
        if home:
            action, alias = home.group(1), self._phrase(home.group(2))
            policy = self.home_aliases.get(alias)
            if policy and policy.get("action") == action:
                confirmation = policy.get("confirmation", "required")
                if confirmation not in {"visible", "required"}:
                    confirmation = "required"
                return self._result(
                    request.request_id, status="ready",
                    intent="home.alias_execute",
                    response=("Ready to turn " + action + " " + alias + "."),
                    arguments={"alias": alias, "action": action},
                    confirmation=confirmation,
                )
            return self._result(
                request.request_id, status="denied",
                response="That Home command is not approved on AsterTV.",
            )

        return self._result(
            request.request_id, status="ambiguous",
            response="I could not match that to an AsterTV command.",
        )


class AsterTVGateway:
    def __init__(self, api_key: str, *, profiles: set[str] | None = None,
                 home_aliases: dict[str, dict[str, str]] | None = None,
                 clock=time.time):
        self.api_key = api_key
        self.profiles = frozenset(profiles or ALLOWED_PROFILES)
        self.engine = IntentEngine(home_aliases)
        self.clock = clock
        self.router = APIRouter()
        self._cache: dict[str, tuple[float, IntentResponse]] = {}
        self.router.add_api_route(
            "/v1/astertv/intent", self.intent, methods=["POST"],
            response_model=IntentResponse,
        )

    def _authenticate(self, authorization: str | None, client: str | None):
        if not self.api_key:
            raise HTTPException(status_code=503, detail="AsterTV broker unavailable")
        expected = "Bearer " + self.api_key
        if (not authorization or not hmac.compare_digest(authorization, expected)
                or client != CLIENT_ID):
            raise HTTPException(status_code=401, detail="Invalid AsterTV identity")

    def _context(self, request: IntentRequest):
        now = datetime.fromtimestamp(self.clock(), timezone.utc)
        lifetime = (request.expires_at - request.issued_at).total_seconds()
        if request.client_id != CLIENT_ID or request.room_id != ROOM_ID:
            raise HTTPException(status_code=403, detail="AsterTV context denied")
        if request.profile_id not in self.profiles:
            raise HTTPException(status_code=403, detail="AsterTV profile denied")
        if not 0 < lifetime <= MAX_LIFETIME_SECONDS:
            raise HTTPException(status_code=400, detail="Invalid AsterTV lifetime")
        if request.issued_at.timestamp() > self.clock() + MAX_CLOCK_SKEW_SECONDS:
            raise HTTPException(status_code=400, detail="AsterTV context not active")
        if request.expires_at <= now:
            raise HTTPException(status_code=409, detail="AsterTV context expired")

    async def intent(
        self, request: IntentRequest,
        authorization: str | None = Header(default=None),
        x_astertv_client: str | None = Header(default=None),
    ) -> IntentResponse:
        self._authenticate(authorization, x_astertv_client)
        self._context(request)
        cached = self._cache.get(request.request_id)
        if cached and cached[0] >= self.clock():
            return cached[1]
        response = self.engine.classify(request)
        self._cache[request.request_id] = (request.expires_at.timestamp(), response)
        profile_hash = hashlib.sha256(request.profile_id.encode()).hexdigest()[:16]
        LOGGER.info(
            "astertv request_id=%s client=%s profile_hash=%s intent=%s decision=%s",
            request.request_id, request.client_id, profile_hash,
            response.intent, response.status,
        )
        return response


def from_environment() -> AsterTVGateway:
    """Build the route from secret-bearing process state without printing it."""
    profiles = {
        value.strip() for value in os.environ.get("ASTER_TV_PROFILES", "jason").split(",")
        if value.strip()
    }
    raw_aliases = os.environ.get("ASTER_TV_HOME_ALIASES", "{}")
    try:
        aliases = json.loads(raw_aliases)
    except json.JSONDecodeError as exc:
        raise RuntimeError("invalid-astertv-alias-config") from exc
    if not isinstance(aliases, dict):
        raise RuntimeError("invalid-astertv-alias-config")
    return AsterTVGateway(
        os.environ.get("ASTER_TV_API_KEY", ""), profiles=profiles,
        home_aliases=aliases,
    )

