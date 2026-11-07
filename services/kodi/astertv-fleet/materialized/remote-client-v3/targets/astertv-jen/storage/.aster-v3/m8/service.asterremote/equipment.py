#!/usr/bin/env python3
"""Send one allowlisted physical equipment intent through the room bridge."""

from __future__ import annotations

import json
from pathlib import Path
import secrets
import sys
import urllib.error
import urllib.request


BASE = "http://192.168.70.10:9120/v1/remote/client/equipment"
CONFIG = Path("/storage/.aster-private/asterremote-client.json")
KEY = Path("/storage/.aster-private/asterremote-client.key")
ALLOWED = frozenset({
    "volume_up", "volume_down", "mute_toggle", "power_toggle",
    "power_on", "power_off",
})


def identity() -> tuple[str, str]:
    if not CONFIG.is_file() or CONFIG.stat().st_mode & 0o077:
        raise RuntimeError("identity-permissions")
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    client_id, room_id = value.get("client_id"), value.get("room_id")
    if not all(isinstance(item, str) and 1 <= len(item) <= 64
               for item in (client_id, room_id)):
        raise RuntimeError("identity-invalid")
    return client_id, room_id


def private_key() -> str:
    details = KEY.stat()
    if not KEY.is_file() or details.st_mode & 0o077:
        raise RuntimeError("credential-permissions")
    value = KEY.read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise RuntimeError("credential-invalid")
    return value


def send(control: str) -> None:
    if control not in ALLOWED:
        raise RuntimeError("control-denied")
    client_id, room_id = identity()
    payload = {
        "client_id": client_id,
        "room_id": room_id,
        "request_id": "physical-" + secrets.token_hex(12),
        "control": control,
    }
    request = urllib.request.Request(
        BASE, json.dumps(payload).encode("utf-8"),
        {"Content-Type": "application/json",
         "Authorization": "Bearer " + private_key(),
         "X-AsterTV-Client": client_id},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError("gateway-response")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError("gateway-unavailable") from error


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(2)
    send(sys.argv[1])
