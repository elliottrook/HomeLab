"""ASGI guard for a separately configured, no-tool A1 test instance.

This is not a production route, app launcher, credential issuer, or model
client. Deploy only around a test-scoped Aster app with no privileged tools,
no production credential mounts, and a separately reviewed endpoint/egress.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import stat
import threading
from pathlib import Path
from typing import Callable

MAX_BODY = 32_768
PATH = "/v1/chat/completions"
REQUEST_FIELDS = {"model", "messages", "temperature", "max_tokens", "stream",
                  "progress", "persona", "enabled_tools"}
USER_FIELDS = {"request", "clock", "private_context_locality_constraint", "context"}
REPO = Path(__file__).resolve().parents[2]


class DurableAttemptJournal:
    """Owner-only, create-once digest claims across worker restarts."""

    def __init__(self, directory: Path):
        if not isinstance(directory, Path) or not directory.is_absolute() or directory.is_symlink():
            raise ValueError("invalid attempt journal directory")
        resolved = directory.resolve()
        if resolved == REPO or REPO in resolved.parents:
            raise ValueError("attempt journal must stay outside Git")
        metadata = directory.stat()
        if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid()
                or metadata.st_mode & 0o077):
            raise ValueError("attempt journal must be an owner-only directory")
        self.directory = directory

    def claim(self, digest: str) -> bool:
        if (not isinstance(digest, str) or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)):
            raise ValueError("invalid request digest")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.directory / digest, flags, 0o600)
        except FileExistsError:
            return False
        with os.fdopen(fd, "wb") as stream:
            stream.write((digest + "\n").encode("ascii"))
            stream.flush()
            os.fsync(stream.fileno())
        dirfd = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
        return True


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
                 request_sha256s: frozenset[str],
                 attempt_journal: DurableAttemptJournal | None = None,
                 downstream_bearer: bytes | None = None):
        if (not callable(app) or not isinstance(token_sha256, str)
                or len(token_sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in token_sha256)
                or not isinstance(request_sha256s, frozenset)
                or len(request_sha256s) != 20
                or any(not isinstance(digest, str) or len(digest) != 64
                       or any(ch not in "0123456789abcdef" for ch in digest)
                       for digest in request_sha256s)
                or (attempt_journal is not None
                    and not isinstance(attempt_journal, DurableAttemptJournal))
                or (downstream_bearer is not None
                    and (not isinstance(downstream_bearer, bytes)
                         or not 16 <= len(downstream_bearer) <= 256
                         or any(not 33 <= ch <= 126 for ch in downstream_bearer)
                         or hashlib.sha256(downstream_bearer).hexdigest() == token_sha256))):
            raise ValueError("invalid isolated test gateway configuration")
        self.app = app
        self.token_sha256 = token_sha256
        self.request_sha256s = request_sha256s
        self.attempt_journal = attempt_journal
        self.downstream_bearer = downstream_bearer
        self._attempted: set[str] = set()
        self._attempt_lock = threading.Lock()

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope.get("type") == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if (scope.get("type") != "http" or scope.get("path") != PATH
                or scope.get("method") != "POST" or scope.get("query_string", b"") != b""):
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
        request_digest = hashlib.sha256(raw).hexdigest()
        if request_digest not in self.request_sha256s:
            await _reject(send, 403)
            return
        # Claim before forwarding. An uncertain downstream result cannot be
        # retried in this process and silently counted as a second attempt.
        with self._attempt_lock:
            repeated = request_digest in self._attempted
            if not repeated:
                self._attempted.add(request_digest)
        if repeated:
            await _reject(send, 409)
            return
        if self.attempt_journal is not None:
            try:
                claimed = self.attempt_journal.claim(request_digest)
            except OSError:
                await _reject(send, 503)
                return
            if not claimed:
                await _reject(send, 409)
                return
        delivered = False

        async def replay():
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {"type": "http.request", "body": raw, "more_body": False}

        # The ingress test credential belongs to this guard, not to Aster or
        # any downstream model/tool adapter.
        inner_scope = dict(scope)
        # Forward only the content type established above. Caller-controlled
        # cookies, identity/proxy headers and other extensions must not become
        # authority or routing hints inside the isolated Aster instance.
        inner_scope["headers"] = [(b"content-type", b"application/json")]
        if self.downstream_bearer is not None:
            inner_scope["headers"].append((b"authorization", b"Bearer " + self.downstream_bearer))
        await self.app(inner_scope, replay, send)
