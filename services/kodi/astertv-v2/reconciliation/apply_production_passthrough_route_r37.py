#!/usr/bin/env python3
"""Restore normal HDMI 0 and correct the inactive passthrough route."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-passthrough-route-r37-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
GUISETTINGS = Path("/storage/.kodi/userdata/guisettings.xml")
NORMAL = "audiooutput.audiodevice"
PASSTHROUGH_DEVICE = "audiooutput.passthroughdevice"
PASSTHROUGH = "audiooutput.passthrough"
CURRENT = {
    NORMAL: "ALSA:@|Default (HDA Intel PCH SN6140 Analog)",
    PASSTHROUGH_DEVICE: "ALSA:hdmi:CARD=PCH,DEV=1|HDA Intel PCH",
    PASSTHROUGH: False,
}
TARGET_DEVICE = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"


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


def value(setting: str):
    return rpc("Settings.GetSettingValue", {"setting": setting})["value"]


def values() -> dict:
    return {key: value(key) for key in CURRENT}


def set_value(setting: str, value) -> None:
    if rpc("Settings.SetSettingValue", {"setting": setting, "value": value}) is not True:
        raise RuntimeError("setting update failed: " + setting)


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    before = values()
    if before != CURRENT:
        raise RuntimeError("unexpected audio predecessor: " + repr(before))
    if not GUISETTINGS.is_file() or GUISETTINGS.is_symlink():
        raise RuntimeError("invalid guisettings boundary")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(GUISETTINGS, CHECKPOINT / "guisettings.xml.before")
    (CHECKPOINT / "runtime-before.json").write_text(
        json.dumps(before, indent=2, sort_keys=True) + "\n")
    try:
        set_value(NORMAL, TARGET_DEVICE)
        set_value(PASSTHROUGH_DEVICE, TARGET_DEVICE)
        expected = dict(CURRENT, **{
            NORMAL: TARGET_DEVICE,
            PASSTHROUGH_DEVICE: TARGET_DEVICE,
        })
        if values() != expected or rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("HDMI route verification failed")
    except Exception:
        if rpc("Player.GetActivePlayers") == []:
            for key, old in before.items():
                try:
                    set_value(key, old)
                except Exception:
                    pass
        RECOVERY.write_text("r37 passthrough-route rollback required\n")
        raise

    result = {"installed": True, "checkpoint": str(CHECKPOINT),
              "settings": values(), "active_players": rpc("Player.GetActivePlayers")}
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
