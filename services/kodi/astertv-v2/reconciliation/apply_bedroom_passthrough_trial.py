#!/usr/bin/env python3
"""Apply the verified Dolby-compatible Bedroom passthrough profile."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import time


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-bedroom-passthrough-20261031"
)
RECOVERY = Path("/storage/.aster-recovery-required")
KODI = "kodi.service"
PULSE = "pulseaudio.service"
ROUTE = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"
TARGET = {
    "audiooutput.audiodevice": ROUTE,
    "audiooutput.channels": 1,
    "audiooutput.passthrough": True,
    "audiooutput.passthroughdevice": ROUTE,
    "audiooutput.ac3passthrough": True,
    "audiooutput.eac3passthrough": True,
    "audiooutput.dtspassthrough": False,
    # The DisplayPort/TV path rejects TrueHD's eight-channel carrier. Kodi must
    # decode TrueHD locally while continuing to pass AC-3 and E-AC-3 through.
    "audiooutput.truehdpassthrough": False,
    "audiooutput.dtshdpassthrough": False,
    "audiooutput.stereoupmix": False,
}


def run(*command: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, text=True, capture_output=True, timeout=30)


def state(unit: str, operation: str) -> str:
    result = run("systemctl", operation, unit, check=False)
    return (result.stdout or result.stderr).strip()


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


def wait_kodi(active: bool) -> None:
    for _ in range(30):
        if (state(KODI, "is-active") == "active") is active:
            if not active:
                return
            try:
                if rpc("Player.GetActivePlayers") == []:
                    return
            except (OSError, TimeoutError, RuntimeError):
                pass
        time.sleep(1)
    raise RuntimeError("Kodi state timeout")


def settings(keys) -> dict:
    return {key: rpc("Settings.GetSettingValue", {"setting": key})["value"]
            for key in keys}


def set_settings(values: dict) -> None:
    for key, value in values.items():
        if rpc("Settings.SetSettingValue", {"setting": key, "value": value}) is not True:
            raise RuntimeError("setting rejected: " + key)
    if settings(values) != values:
        raise RuntimeError("audio setting verification failed")


def restore(before: dict) -> None:
    try:
        if state(KODI, "is-active") == "active":
            set_settings(before["settings"])
        run("systemctl", "stop", KODI, check=False)
        run("systemctl", "unmask", PULSE, check=False)
        if before["pulse_enabled"] == "enabled":
            run("systemctl", "enable", PULSE)
        else:
            run("systemctl", "disable", PULSE)
        if before["pulse_active"] == "active":
            run("systemctl", "start", PULSE)
        else:
            run("systemctl", "stop", PULSE, check=False)
        run("systemctl", "start", KODI)
        wait_kodi(True)
        set_settings(before["settings"])
    except Exception:
        RECOVERY.write_text("Bedroom passthrough trial rollback required\n")
        raise


def main() -> None:
    if os.uname().nodename != "AsterTV-Bedroom":
        raise RuntimeError("Bedroom host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    before = {
        "settings": settings(TARGET),
        "pulse_active": state(PULSE, "is-active"),
        "pulse_enabled": state(PULSE, "is-enabled"),
        "kodi_active": state(KODI, "is-active"),
    }
    if before["kodi_active"] != "active":
        raise RuntimeError("Kodi is not active")
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / "before.json").write_text(
        json.dumps(before, indent=2, sort_keys=True) + "\n")

    try:
        run("systemctl", "stop", KODI)
        wait_kodi(False)
        run("systemctl", "stop", PULSE, check=False)
        run("systemctl", "mask", PULSE)
        if state(PULSE, "is-active") == "active" or state(PULSE, "is-enabled") != "masked":
            raise RuntimeError("PulseAudio did not enter the exclusive-HDMI state")
        run("systemctl", "start", KODI)
        wait_kodi(True)
        set_settings(TARGET)
        time.sleep(2)
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        restore(before)
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "settings": settings(TARGET),
        "pulse_active": state(PULSE, "is-active"),
        "pulse_enabled": state(PULSE, "is-enabled"),
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
