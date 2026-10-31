#!/usr/bin/env python3
"""Bounded production trial: enumerate connected HDMI with PulseAudio stopped."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-alsa-exclusive-r44-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
GUISETTINGS = Path("/storage/.kodi/userdata/guisettings.xml")
KODI_LOG = Path("/storage/.kodi/temp/kodi.log")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def state(unit: str, verb: str) -> str:
    return run("systemctl", verb, unit, check=False).stdout.strip()


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


def wait_active(unit: str, wanted: bool, timeout: float = 20) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if (state(unit, "is-active") == "active") == wanted:
            return
        time.sleep(.25)
    raise RuntimeError(unit + " state timeout")


def wait_kodi_rpc(timeout: float = 30) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            if rpc("Player.GetActivePlayers") == []:
                return
        except (OSError, RuntimeError):
            pass
        time.sleep(.5)
    raise RuntimeError("Kodi JSON-RPC did not become ready")


def rollback() -> None:
    run("systemctl", "stop", "kodi.service", check=False)
    run("systemctl", "start", "pulseaudio.service")
    wait_active("pulseaudio.service", True)
    run("systemctl", "start", "kodi.service")
    wait_active("kodi.service", True)
    wait_kodi_rpc()


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if state("kodi.service", "is-active") != "active":
        raise RuntimeError("Kodi not active")
    if state("pulseaudio.service", "is-active") != "active":
        raise RuntimeError("PulseAudio predecessor not active")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(GUISETTINGS, CHECKPOINT / "guisettings.xml.before")
    before = {
        "kodi_active": state("kodi.service", "is-active"),
        "pulseaudio_active": state("pulseaudio.service", "is-active"),
        "pulseaudio_enabled": state("pulseaudio.service", "is-enabled"),
    }
    (CHECKPOINT / "service-state.before.json").write_text(
        json.dumps(before, indent=2, sort_keys=True) + "\n")

    try:
        run("systemctl", "stop", "kodi.service")
        wait_active("kodi.service", False)
        run("systemctl", "stop", "pulseaudio.service")
        wait_active("pulseaudio.service", False)
        run("systemctl", "start", "kodi.service")
        wait_active("kodi.service", True)
        wait_kodi_rpc()
        time.sleep(3)
        log = KODI_LOG.read_text(errors="replace")
        required = (
            "m_deviceName      : hdmi:CARD=PCH,DEV=0",
            "m_displayNameExtra: Beyond TV",
            "STREAM_TYPE_EAC3",
            "STREAM_TYPE_TRUEHD",
        )
        if not all(value in log for value in required):
            raise RuntimeError("connected HDMI passthrough capabilities not enumerated")
        bad = (
            "audio output device setting has been updated from "
            "'ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH'"
        )
        if bad in log:
            raise RuntimeError("Kodi rewrote HDMI 0 after exclusive enumeration")
        if state("pulseaudio.service", "is-active") == "active":
            raise RuntimeError("PulseAudio unexpectedly restarted")
    except Exception:
        rollback()
        (CHECKPOINT / "result.json").write_text(json.dumps({
            "installed": False,
            "rolled_back": True,
            "reason": "exclusive HDMI capability validation failed",
        }, indent=2, sort_keys=True) + "\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "kodi_active": state("kodi.service", "is-active"),
        "pulseaudio_active": state("pulseaudio.service", "is-active"),
        "pulseaudio_enabled_unchanged": state("pulseaudio.service", "is-enabled"),
        "hdmi_device": "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH",
        "eac3_capability_enumerated": True,
        "truehd_capability_enumerated": True,
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
