#!/usr/bin/env python3
"""Enable a reversible HDMI 0 passthrough signal trial without codec probing."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import xml.etree.ElementTree as ET


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-dolby-r39-signal-20261031")
FAILED_R38 = Path(
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
    "audiooutput.ac3passthrough": True,
    "videoplayer.usedisplayasclock": False,
}


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
    return {key: value(key) for key in BASELINE}


def xml_codec_values() -> dict:
    wanted = {
        "audiooutput.ac3passthrough", "audiooutput.ac3transcode",
        "audiooutput.eac3passthrough", "audiooutput.truehdpassthrough",
        "audiooutput.dtspassthrough", "audiooutput.dtshdpassthrough",
    }
    root = ET.fromstring(GUISETTINGS.read_bytes())
    rows = {node.get("id"): node.text for node in root.iter("setting")
            if node.get("id") in wanted}
    if set(rows) != wanted:
        raise RuntimeError("missing persisted codec flags")
    return rows


def set_passthrough(enabled: bool) -> None:
    result = rpc("Settings.SetSettingValue", {
        "setting": "audiooutput.passthrough", "value": enabled})
    if result is not True:
        raise RuntimeError("global passthrough update failed")


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if values() != BASELINE:
        raise RuntimeError("unexpected safe audio baseline")
    marker = RECOVERY.read_text() if RECOVERY.exists() else ""
    if marker:
        if marker != "r38 Dolby trial rollback required\n" or not FAILED_R38.is_dir():
            raise RuntimeError("unrelated recovery guard")
        # r38 marked recovery even after successfully restoring every bounded
        # setting. The exact safe baseline above is the recovery proof.
        RECOVERY.unlink()
    codecs = xml_codec_values()
    if codecs != {
        "audiooutput.ac3passthrough": "true",
        "audiooutput.ac3transcode": "false",
        "audiooutput.eac3passthrough": "true",
        "audiooutput.truehdpassthrough": "true",
        "audiooutput.dtspassthrough": "false",
        "audiooutput.dtshdpassthrough": "false",
    }:
        raise RuntimeError("unexpected persisted codec flags")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(GUISETTINGS, CHECKPOINT / "guisettings.xml.before")
    (CHECKPOINT / "runtime-before.json").write_text(
        json.dumps(BASELINE, indent=2, sort_keys=True) + "\n")
    (CHECKPOINT / "codec-flags.json").write_text(
        json.dumps(codecs, indent=2, sort_keys=True) + "\n")
    try:
        set_passthrough(True)
        expected = dict(BASELINE, **{"audiooutput.passthrough": True})
        if values() != expected or rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("signal trial settings did not persist")
    except Exception:
        if rpc("Player.GetActivePlayers") == []:
            try:
                set_passthrough(False)
            except Exception:
                pass
        RECOVERY.write_text("r39 Dolby signal rollback required\n")
        raise

    result = {"installed": True, "checkpoint": str(CHECKPOINT),
              "profile": "HDMI 0 signal-observation trial",
              "settings": values(), "persisted_codecs": codecs,
              "active_players": rpc("Player.GetActivePlayers")}
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
