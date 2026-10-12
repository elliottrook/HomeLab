"""Content-free ASGI request clock candidate for Aster offline tests.

Measures app-entry to final response body. This excludes client/network time
and does not decide whether a response was useful or policy-compliant.
"""
from __future__ import annotations

import time
from typing import Any, Callable


class ASGIResponseClock:
    def __init__(self, app: Callable, sink: list[dict[str, Any]],
                 allowed_path: str = "/v1/chat/completions"):
        self.app = app
        self.sink = sink
        self.allowed_path = allowed_path

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != self.allowed_path:
            await self.app(scope, receive, send)
            return
        started = time.monotonic_ns()
        first_body = None
        status = None
        terminal = None

        async def measured_send(message):
            nonlocal first_body, status, terminal
            if message["type"] == "http.response.start":
                status = message["status"]
            elif message["type"] == "http.response.body":
                now = time.monotonic_ns()
                if first_body is None:
                    first_body = now
                if not message.get("more_body", False):
                    terminal = now
            await send(message)

        try:
            await self.app(scope, receive, measured_send)
        finally:
            self.sink.append({
                "schema_version": "aster-asgi-clock.v0",
                "path": self.allowed_path,
                "http_status": status,
                "first_body_ms": round((first_body - started) / 1_000_000, 3)
                if first_body is not None else None,
                "terminal_ms": round((terminal - started) / 1_000_000, 3)
                if terminal is not None else None,
                "terminal_observed": terminal is not None,
            })
