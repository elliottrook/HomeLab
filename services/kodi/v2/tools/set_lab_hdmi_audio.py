"""Select the connected LG display's HDMI 0 stereo sink on idle HP lab."""

import json
import os
from pathlib import Path
import shutil

import xbmc


SETTINGS = Path("/storage/.kodi/userdata/guisettings.xml")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-lab-hdmi-audio-20261029")
KEY = "audiooutput.audiodevice"
ANALOG = "ALSA:@|Default (HDA Intel PCH CX20632 Analog)"
HDMI = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"


def rpc(method, **params):
    answer = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params})))
    if "error" in answer:
        raise RuntimeError("audio-rpc-failed:" + method)
    return answer["result"]


def value(key):
    return rpc("Settings.GetSettingValue", setting=key)["value"]


def main():
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab-host-only")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-player")
    if not SETTINGS.is_file() or SETTINGS.is_symlink() or CHECKPOINT.exists():
        raise RuntimeError("audio-checkpoint-preflight")
    before = {key: value(key) for key in (KEY, "audiooutput.passthroughdevice",
              "audiooutput.passthrough", "audiooutput.channels")}
    if before != {KEY: ANALOG, "audiooutput.passthroughdevice": HDMI,
                  "audiooutput.passthrough": False, "audiooutput.channels": 1}:
        raise RuntimeError("unexpected-audio-predecessor")
    rows = rpc("Settings.GetSettings", level="expert",
               filter={"section": "system", "category": "audio"}).get("settings", [])
    device = next((row for row in rows if row.get("id") == KEY), None)
    if not device or HDMI not in {option.get("value") for option in device.get("options", [])}:
        raise RuntimeError("connected-hdmi-choice-unavailable")
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(SETTINGS, CHECKPOINT / "guisettings.xml.before")
    os.chmod(CHECKPOINT / "guisettings.xml.before", 0o600)
    (CHECKPOINT / "runtime-before.json").write_text(json.dumps(before, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT / "runtime-before.json", 0o600)
    try:
        rpc("Settings.SetSettingValue", setting=KEY, value=HDMI)
        if value(KEY) != HDMI:
            raise RuntimeError("audio-selector-not-set")
    except Exception:
        rpc("Settings.SetSettingValue", setting=KEY, value=ANALOG)
        raise
    (CHECKPOINT / "installed.json").write_text('{"hdmi_0_selected": true, "passthrough": false}\n')
    xbmc.log("Aster lab: connected LG HDMI 0 stereo selected", xbmc.LOGINFO)


if __name__ == "__main__":
    main()
