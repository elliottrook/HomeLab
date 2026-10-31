#!/usr/bin/env python3
"""Disable unsupported TrueHD passthrough on the Bedroom DisplayPort chain."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-bedroom-truehd-compatibility-20261031"
)
RECOVERY = Path("/storage/.aster-recovery-required")
SETTING = "audiooutput.truehdpassthrough"


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        raw = b""
        while True:
            raw += client.recv(65536)
            try:
                reply = json.loads(raw)
                break
            except json.JSONDecodeError:
                continue
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def value() -> bool:
    result = rpc("Settings.GetSettingValue", {"setting": SETTING})["value"]
    if type(result) is not bool:
        raise RuntimeError("unexpected TrueHD setting type")
    return result


def main() -> None:
    if os.uname().nodename != "AsterTV-Bedroom":
        raise RuntimeError("Bedroom host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    before = value()
    if before is not True:
        raise RuntimeError("unexpected TrueHD predecessor")
    players = rpc("Player.GetActivePlayers")
    if any(row.get("type") != "video" for row in players):
        raise RuntimeError("unexpected active player")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / "before.json").write_text(json.dumps({
        "setting": SETTING,
        "value": before,
        "active_players": players,
        "reason": "Bedroom DisplayPort chain rejects the 8-channel TrueHD carrier",
    }, indent=2, sort_keys=True) + "\n")
    try:
        if rpc("Settings.SetSettingValue", {"setting": SETTING, "value": False}) is not True:
            raise RuntimeError("TrueHD setting rejected")
        if value() is not False:
            raise RuntimeError("TrueHD setting did not persist")
    except Exception:
        try:
            rpc("Settings.SetSettingValue", {"setting": SETTING, "value": before})
        finally:
            RECOVERY.write_text("Bedroom TrueHD compatibility rollback required\n")
        raise

    result = {
        "installed": True,
        "setting": SETTING,
        "before": before,
        "after": value(),
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
