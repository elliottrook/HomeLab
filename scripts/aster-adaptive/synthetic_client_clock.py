"""In-process, fictional-only join of the B60 client and Aster ASGI clocks.

The supplied app must be an ASGIResponseClock around an explicitly marked
fixture. This module has no HTTP transport, credentials, model or tool client.
It returns timing/status records only, never response text or exception detail.
It is not a native Companion display measurement or live Aster-path result.
"""
from __future__ import annotations

import inspect
from typing import Callable

from aster_asgi_clock import ASGIResponseClock
from client_display_clock import ClientDisplayClock
from join_aster_clock import join

MAX_FIXTURE_BODY = 65_536


async def run_fixture(
    wrapped: ASGIResponseClock,
    display: Callable[[bytes], None],
    *,
    clock: Callable[[], int],
) -> dict:
    if (not isinstance(wrapped, ASGIResponseClock)
            or getattr(wrapped.app, "synthetic_clock_fixture", False) is not True
            or not callable(display)):
        raise ValueError("only a marked in-process clock fixture is allowed")

    client = ClientDisplayClock(clock)
    pieces: list[bytes] = []
    size = 0
    response_started = False
    terminal_body = False
    prior_gateway_rows = len(wrapped.sink)
    failed = False

    request_delivered = False

    async def receive():
        nonlocal request_delivered
        if request_delivered:
            return {"type": "http.disconnect"}
        request_delivered = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal response_started, terminal_body, size
        if message["type"] == "http.response.start":
            if response_started:
                raise ValueError("duplicate response start")
            response_started = True
            identifiers = [value.decode("ascii") for name, value in message.get("headers", [])
                           if name.lower() == b"x-aster-observation-id"]
            if len(identifiers) != 1:
                raise ValueError("missing or duplicate observation ID")
            client.response_identity(identifiers[0], message["status"])
        elif message["type"] == "http.response.body":
            if (not response_started or terminal_body
                    or not isinstance(message.get("body", b""), bytes)
                    or type(message.get("more_body", False)) is not bool):
                raise ValueError("invalid response body sequence")
            part = message.get("body", b"")
            size += len(part)
            if size > MAX_FIXTURE_BODY:
                raise ValueError("oversized fictional response")
            pieces.append(part)
            terminal_body = message.get("more_body", False) is False
        else:
            raise ValueError("unexpected ASGI response event")

    try:
        await wrapped({"type": "http", "path": "/v1/chat/completions",
                       "method": "POST", "headers": []}, receive, send)
        if terminal_body:
            # A caller-supplied fixture renderer is the only point that may
            # mark display. Merely receiving the final body is insufficient.
            result = display(b"".join(pieces))
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()
                raise ValueError("fixture display callback must complete synchronously")
        else:
            failed = True
    except Exception:
        failed = True
    client_row = client.finish(terminal_displayed=terminal_body and not failed)
    if len(wrapped.sink) != prior_gateway_rows + 1:
        raise ValueError("missing gateway clock record")
    gateway_row = wrapped.sink[-1]
    joined = None
    if client_row["observation_id"] is not None:
        joined = join(client_row, gateway_row)
    return {"schema_version": "aster-synthetic-clock-pair.v0",
            "client": client_row, "gateway": gateway_row, "joined": joined,
            "fixture_state": "failed" if failed else "displayed"}
