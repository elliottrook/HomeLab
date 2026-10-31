#!/usr/bin/env python3
"""Replace production's Working label with the static AsterTV splash."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import xml.etree.ElementTree as ET


BUSY = Path("/storage/.kodi/addons/skin.asterhome/1080i/DialogBusy.xml")
SPLASH = Path("/storage/.kodi/media/Splash.png")
SOURCE = Path(__file__).resolve().parent / "payload/skin.asterhome/1080i/DialogBusy.xml"
CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-busy-logo-r36-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED_BUSY = "f285cba0b64b06bf85b0f67252e0dcf52e132402907eabc69b6a152fb98936ff"
EXPECTED_SPLASH = "912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce"
AUDIO_SETTINGS = (
    "audiooutput.audiodevice", "audiooutput.passthroughdevice",
    "audiooutput.passthrough", "audiooutput.channels", "audiooutput.config",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def audio() -> dict:
    return {key: rpc("Settings.GetSettingValue", {"setting": key})["value"]
            for key in AUDIO_SETTINGS}


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r36-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if sha(BUSY) != EXPECTED_BUSY or sha(SPLASH) != EXPECTED_SPLASH:
        raise RuntimeError("unexpected busy dialog or splash predecessor")
    updated = SOURCE.read_bytes()
    root = ET.fromstring(updated)
    if root.findtext("./controls/control/texture") != "special://home/media/Splash.png":
        raise RuntimeError("invalid AsterTV busy source")
    saved_audio = audio()

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(BUSY, CHECKPOINT / "DialogBusy.xml.before")
    (CHECKPOINT / "audio-before.json").write_text(
        json.dumps(saved_audio, indent=2, sort_keys=True) + "\n")
    try:
        atomic_write(BUSY, updated)
        subprocess.run(["/usr/bin/kodi-send", "--action=ReloadSkin()"], check=True,
                       timeout=10, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
        if sha(BUSY) != hashlib.sha256(updated).hexdigest():
            raise RuntimeError("installed busy dialog hash mismatch")
        if audio() != saved_audio:
            raise RuntimeError("audio configuration changed during skin reload")
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        atomic_write(BUSY, (CHECKPOINT / "DialogBusy.xml.before").read_bytes())
        RECOVERY.write_text("r36 busy-dialog rollback required\n")
        raise

    result = {"installed": True, "checkpoint": str(CHECKPOINT),
              "dialog_sha256": sha(BUSY), "splash_sha256": sha(SPLASH),
              "audio": audio(), "active_players": rpc("Player.GetActivePlayers")}
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
