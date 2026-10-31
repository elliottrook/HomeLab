#!/usr/bin/env python3
"""Corrected ALSA-exclusive HDMI trial with explicit route preservation."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

import apply_production_alsa_exclusive_r44_trial as base


CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-alsa-exclusive-r45-20261031")
ROUTE = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"


def routed(data: bytes) -> bytes:
    text = data.decode()
    for setting in ("audiooutput.audiodevice", "audiooutput.passthroughdevice"):
        pattern = (r'(<setting id="' + re.escape(setting) + r'">)[^<]*(</setting>)')
        text, count = re.subn(pattern, r"\g<1>" + ROUTE + r"\g<2>", text, count=1)
        if count != 1:
            raise RuntimeError("missing audio route: " + setting)
    return text.encode()


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r45-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def restore_audible_route() -> None:
    base.run("systemctl", "stop", "kodi.service", check=False)
    base.run("systemctl", "start", "pulseaudio.service")
    base.wait_active("pulseaudio.service", True)
    atomic_write(base.GUISETTINGS, routed(base.GUISETTINGS.read_bytes()))
    base.run("systemctl", "start", "kodi.service")
    base.wait_active("kodi.service", True)
    base.wait_kodi_rpc()
    for setting in ("audiooutput.audiodevice", "audiooutput.passthroughdevice"):
        base.rpc("Settings.SetSettingValue", {"setting": setting, "value": ROUTE})


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or base.RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if base.rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if base.state("kodi.service", "is-active") != "active":
        raise RuntimeError("Kodi not active")
    if base.state("pulseaudio.service", "is-active") != "active":
        raise RuntimeError("PulseAudio predecessor not active")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(base.GUISETTINGS, CHECKPOINT / "guisettings.xml.before")
    try:
        base.run("systemctl", "stop", "kodi.service")
        base.wait_active("kodi.service", False)
        base.run("systemctl", "stop", "pulseaudio.service")
        base.wait_active("pulseaudio.service", False)
        atomic_write(base.GUISETTINGS, routed(base.GUISETTINGS.read_bytes()))
        base.run("systemctl", "start", "kodi.service")
        base.wait_active("kodi.service", True)
        base.wait_kodi_rpc()
        time.sleep(3)
        log = base.KODI_LOG.read_text(errors="replace")
        required = (
            "m_deviceName      : hdmi:CARD=PCH,DEV=0",
            "Beyond TV",
            "STREAM_TYPE_EAC3",
            "STREAM_TYPE_TRUEHD",
            'Opened device "hdmi:CARD=PCH,DEV=0',
        )
        if not all(value in log for value in required):
            raise RuntimeError("connected HDMI passthrough capabilities not enumerated")
        bad = (
            "audio output device setting has been updated from "
            "'ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH'"
        )
        if bad in log:
            raise RuntimeError("Kodi rewrote HDMI 0 after exclusive enumeration")
        if base.state("pulseaudio.service", "is-active") == "active":
            raise RuntimeError("PulseAudio unexpectedly restarted")
    except Exception:
        restore_audible_route()
        (CHECKPOINT / "result.json").write_text(json.dumps({
            "installed": False,
            "rolled_back": True,
            "reason": "corrected exclusive HDMI validation failed",
        }, indent=2, sort_keys=True) + "\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "kodi_active": base.state("kodi.service", "is-active"),
        "pulseaudio_active": base.state("pulseaudio.service", "is-active"),
        "pulseaudio_enabled_unchanged": base.state(
            "pulseaudio.service", "is-enabled"),
        "hdmi_device": ROUTE,
        "eac3_capability_enumerated": True,
        "truehd_capability_enumerated": True,
        "active_players": base.rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
