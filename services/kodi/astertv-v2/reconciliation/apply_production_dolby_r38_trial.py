#!/usr/bin/env python3
"""Enable a bounded AC-3/E-AC-3 passthrough trial on production HDMI 0."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import xml.etree.ElementTree as ET


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-dolby-r38-trial-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
GUISETTINGS = Path("/storage/.kodi/userdata/guisettings.xml")
DEVICE = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"
BASELINE = {
    "audiooutput.audiodevice": DEVICE,
    "audiooutput.passthroughdevice": DEVICE,
    "audiooutput.passthrough": False,
    "audiooutput.channels": 1,
    "audiooutput.config": 2,
    "videoplayer.usedisplayasclock": False,
}
CODECS_BEFORE = {
    "audiooutput.ac3passthrough": True,
    "audiooutput.ac3transcode": False,
    "audiooutput.eac3passthrough": True,
    "audiooutput.truehdpassthrough": True,
    "audiooutput.dtspassthrough": False,
    "audiooutput.dtshdpassthrough": False,
}
CODECS_TRIAL = dict(CODECS_BEFORE, **{
    "audiooutput.truehdpassthrough": False,
})


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


def values(keys) -> dict:
    return {key: value(key) for key in keys}


def set_value(setting: str, value) -> None:
    result = rpc("Settings.SetSettingValue", {"setting": setting, "value": value})
    if result is not True:
        raise RuntimeError("setting update failed: " + setting)


def xml_values() -> dict:
    root = ET.fromstring(GUISETTINGS.read_bytes())
    wanted = set(BASELINE) | set(CODECS_BEFORE)
    wanted.remove("videoplayer.usedisplayasclock")
    rows = {node.get("id"): node.text for node in root.iter("setting")
            if node.get("id") in wanted}
    if set(rows) != wanted:
        raise RuntimeError("missing guisettings audio values")
    return rows


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if values(BASELINE) != BASELINE:
        raise RuntimeError("unexpected live audio baseline")
    expected_xml = {
        "audiooutput.audiodevice": DEVICE,
        "audiooutput.passthroughdevice": DEVICE,
        "audiooutput.passthrough": "false",
        "audiooutput.channels": "1",
        "audiooutput.config": "2",
        "audiooutput.ac3passthrough": "true",
        "audiooutput.ac3transcode": "false",
        "audiooutput.eac3passthrough": "true",
        "audiooutput.truehdpassthrough": "true",
        "audiooutput.dtspassthrough": "false",
        "audiooutput.dtshdpassthrough": "false",
    }
    if xml_values() != expected_xml:
        raise RuntimeError("unexpected persisted audio baseline")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(GUISETTINGS, CHECKPOINT / "guisettings.xml.before")
    (CHECKPOINT / "runtime-before.json").write_text(
        json.dumps(BASELINE, indent=2, sort_keys=True) + "\n")
    try:
        set_value("audiooutput.passthrough", True)
        if values(CODECS_BEFORE) != CODECS_BEFORE:
            raise RuntimeError("codec predecessor changed after passthrough enable")
        for key, target in CODECS_TRIAL.items():
            set_value(key, target)
        expected = dict(BASELINE, **{"audiooutput.passthrough": True})
        if values(expected) != expected or values(CODECS_TRIAL) != CODECS_TRIAL:
            raise RuntimeError("Dolby trial settings did not persist")
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        if rpc("Player.GetActivePlayers") == []:
            for key, old in CODECS_BEFORE.items():
                try:
                    set_value(key, old)
                except Exception:
                    pass
            try:
                set_value("audiooutput.passthrough", False)
            except Exception:
                pass
        RECOVERY.write_text("r38 Dolby trial rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "profile": "HDMI 0 AC-3/E-AC-3 only",
        "baseline": values(BASELINE),
        "codecs": values(CODECS_TRIAL),
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
