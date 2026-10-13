"""Content-free join of a future client clock and the offline ASGI clock.

This only joins same-request observations. It never subtracts monotonic times
from different processes or declares a terminal response useful.
"""
from __future__ import annotations

import math
import re

ID = re.compile(r"[0-9a-f]{32}\Z")
CLIENT_FIELDS = {"schema_version", "observation_id", "http_status",
                 "accepted_to_displayed_ms", "terminal_displayed"}
ASGI_FIELDS = {"schema_version", "observation_id", "path", "http_status",
               "first_body_ms", "terminal_ms", "terminal_observed"}


def _milliseconds(value, *, nullable: bool) -> float | None:
    if value is None and nullable:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        raise ValueError("invalid duration")
    return float(value)


def _status(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 100 <= value <= 599:
        raise ValueError("invalid HTTP status")
    return value


def join(client: dict, gateway: dict) -> dict:
    if (not isinstance(client, dict) or set(client) != CLIENT_FIELDS
            or not isinstance(gateway, dict) or set(gateway) != ASGI_FIELDS):
        raise ValueError("unexpected clock fields; raw content is forbidden")
    if (client["schema_version"] != "aster-client-clock.v0"
            or gateway["schema_version"] != "aster-asgi-clock.v0"
            or gateway["path"] != "/v1/chat/completions"
            or not isinstance(client["observation_id"], str)
            or not ID.fullmatch(client["observation_id"])
            or client["observation_id"] != gateway["observation_id"]):
        raise ValueError("clock identity mismatch")
    client_status = _status(client["http_status"])
    gateway_status = _status(gateway["http_status"])
    if client_status is not None and gateway_status is not None and client_status != gateway_status:
        raise ValueError("clock status mismatch")
    if not isinstance(client["terminal_displayed"], bool) or not isinstance(gateway["terminal_observed"], bool):
        raise ValueError("invalid terminal marker")
    client_ms = _milliseconds(client["accepted_to_displayed_ms"], nullable=True)
    first_ms = _milliseconds(gateway["first_body_ms"], nullable=True)
    gateway_ms = _milliseconds(gateway["terminal_ms"], nullable=True)
    if ((client_ms is None) == client["terminal_displayed"]
            or (gateway_ms is None) == gateway["terminal_observed"]
            or (gateway_ms is not None and (first_ms is None or first_ms > gateway_ms))):
        raise ValueError("terminal timing and marker disagree")
    joined = client["terminal_displayed"] and gateway["terminal_observed"]
    return {"schema_version": "aster-clock-join.v0",
            "observation_id": client["observation_id"],
            "http_status": client_status if client_status is not None else gateway_status,
            "client_terminal_display_ms": client_ms,
            "gateway_first_body_ms": first_ms,
            "gateway_terminal_ms": gateway_ms,
            "terminal_joined": joined,
            "censored": not joined,
            "useful_answer_ms": None}
