#!/usr/bin/env python3
"""Restore the known-good HDMI 0 route after the r34 saver diagnostic crash."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-r34-test-audio-recovery-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
SETTING = "audiooutput.audiodevice"
PREDECESSOR = "ALSA:@:CARD=PCH,DEV=0|HDA Intel PCH"
TARGET = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"


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


def value() -> str:
    return rpc("Settings.GetSettingValue", {"setting": SETTING})["value"]


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    before = value()
    if before != PREDECESSOR:
        raise RuntimeError("unexpected audio predecessor: " + repr(before))
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / "before.json").write_text(json.dumps({
        "setting": SETTING, "value": before,
        "cause": "Kodi auto-restart after r34 screensaver diagnostic crash",
    }, indent=2, sort_keys=True) + "\n")
    try:
        result = rpc("Settings.SetSettingValue", {"setting": SETTING, "value": TARGET})
        if result is not True or value() != TARGET:
            raise RuntimeError("explicit HDMI 0 route did not persist")
    except Exception:
        try:
            rpc("Settings.SetSettingValue", {"setting": SETTING, "value": before})
        finally:
            RECOVERY.write_text("r34 diagnostic audio recovery required\n")
        raise
    final = {"restored": True, "setting": SETTING, "before": before,
             "after": value(), "active_players": rpc("Player.GetActivePlayers")}
    (CHECKPOINT / "result.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
