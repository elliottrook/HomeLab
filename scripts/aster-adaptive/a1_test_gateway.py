"""ASGI guard for a separately configured, no-tool A1 test instance.

This is not a production route, app launcher, credential issuer, or model
client. Deploy only around a test-scoped Aster app with no privileged tools,
no production credential mounts, and a separately reviewed endpoint/egress.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Callable

MAX_BODY = 32_768
PATH = "/v1/chat/completions"
REQUEST_FIELDS = {"model", "messages", "temperature", "max_tokens", "stream",
                  "progress", "persona", "enabled_tools"}
USER_FIELDS = {"request", "clock", "private_context_locality_constraint", "context"}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def valid_body(raw: bytes) -> bool:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BODY:
        return False
    try:
        body = json.loads(raw, object_pairs_hook=_unique_pairs)
        if not isinstance(body, dict) or set(body) != REQUEST_FIELDS:
            return False
        if (body["model"] != "aster-qwen3.5-9b"
                or body["temperature"] != 0 or type(body["temperature"]) is bool
                or type(body["max_tokens"]) is not int or body["max_tokens"] != 256
                or body["stream"] is not False or body["progress"] is not False
                or body["persona"] != "sysadmin" or body["enabled_tools"] != []):
            return False
        messages = body["messages"]
        if (not isinstance(messages, list) or len(messages) != 1
                or not isinstance(messages[0], dict)
                or set(messages[0]) != {"role", "content"}
                or messages[0]["role"] != "user"
                or not isinstance(messages[0]["content"], str)):
            return False
        user = json.loads(messages[0]["content"], object_pairs_hook=_unique_pairs)
        return (isinstance(user, dict) and set(user) == USER_FIELDS
                and isinstance(user["request"], str)
                and bool(user["request"].strip())
                and isinstance(user["clock"], str)
                and isinstance(user["private_context_locality_constraint"], str)
                and isinstance(user["context"], list))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        return False


async def _reject(send: Callable, status: int) -> None:
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"),
                            (b"cache-control", b"no-store")]})
    await send({"type": "http.response.body", "body": b"{}", "more_body": False})


class A1TestGateway:
    def __init__(self, app: Callable, *, token_sha256: str,
                 request_sha256s: frozenset[str]):
        if (not callable(app) or not isinstance(token_sha256, str)
                or len(token_sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in token_sha256)
                or not isinstance(request_sha256s, frozenset)
                or len(request_sha256s) != 20
                or any(not isinstance(digest, str) or len(digest) != 64
                       or any(ch not in "0123456789abcdef" for ch in digest)
                       for digest in request_sha256s)):
            raise ValueError("invalid isolated test gateway configuration")
        self.app = app
        self.token_sha256 = token_sha256
        self.request_sha256s = request_sha256s

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope.get("type") == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope.get("type") != "http" or scope.get("path") != PATH or scope.get("method") != "POST":
            await _reject(send, 404)
            return
        headers = scope.get("headers", [])
        auth = [v for k, v in headers if k.lower() == b"authorization"]
        content_types = [v.lower() for k, v in headers if k.lower() == b"content-type"]
        if content_types != [b"application/json"]:
            await _reject(send, 415)
            return
        if len(auth) != 1 or not auth[0].startswith(b"Bearer "):
            await _reject(send, 401)
            return
        token = auth[0][7:]
        if (not token or len(token) > 512
                or not hmac.compare_digest(hashlib.sha256(token).hexdigest(), self.token_sha256)):
            await _reject(send, 401)
            return
        chunks = []
        total = 0
        for _ in range(16):
            message = await receive()
            if message.get("type") != "http.request":
                await _reject(send, 400)
                return
            chunk = message.get("body", b"")
            if (not isinstance(chunk, bytes)
                    or type(message.get("more_body", False)) is not bool):
                await _reject(send, 400)
                return
            total += len(chunk)
            if total > MAX_BODY:
                await _reject(send, 413)
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        else:
            await _reject(send, 413)
            return
        raw = b"".join(chunks)
        if not valid_body(raw):
            await _reject(send, 400)
            return
        if hashlib.sha256(raw).hexdigest() not in self.request_sha256s:
            await _reject(send, 403)
            return
        delivered = False

        async def replay():
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {"type": "http.request", "body": raw, "more_body": False}

        await self.app(scope, replay, send)
