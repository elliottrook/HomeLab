"""Bounded lab-only Kodi E-AC-3 software-path probe; always restore stereo."""

import json
import os
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import xbmc


CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-lab-eac3-path-20261029-v3")
RESULT = Path("/tmp/astertv-lab-eac3-path-result-v3.json")
SETTINGS = Path("/storage/.kodi/userdata/guisettings.xml")
KODI_LOG = Path("/storage/.kodi/temp/kodi.log")
HDMI = "ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH"
EPISODE = 1546  # previously watched, indexed lab test episode


def rpc(method, params=None):
    response = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})))
    if "error" in response:
        key = (params or {}).get("setting", "")
        raise RuntimeError("rpc-error:" + method + ":" + key)
    return response["result"]


def value(key):
    return rpc("Settings.GetSettingValue", {"setting": key})["value"]


def set_value(key, new):
    rpc("Settings.SetSettingValue", {"setting": key, "value": new})
    if value(key) != new:
        raise RuntimeError("setting-not-applied:" + key)


def connected_eld():
    matches = []
    for path in Path("/proc/asound/card0").glob("eld#*"):
        text = path.read_text()
        if "monitor_present\t\t1" in text and "eld_valid\t\t1" in text:
            matches.append(text)
    return len(matches) == 1 and "monitor_name\t\tLG HDR 4K" in matches[0]


def saved_value(key):
    rows = [row.text for row in ET.parse(SETTINGS).getroot().findall("setting")
            if row.attrib.get("id") == key]
    if len(rows) != 1:
        raise RuntimeError("saved-setting-missing:" + key)
    return rows[0]


def main():
    started = False
    changed = False
    result = {"probe": "eac3-kodi-software-path", "host": "AsterTV",
              "passed": False, "restored": False}
    try:
        if (os.uname().nodename != "AsterTV" or CHECKPOINT.exists()
                or not SETTINGS.is_file() or SETTINGS.is_symlink()
                or not connected_eld() or rpc("Player.GetActivePlayers")):
            raise RuntimeError("preflight")
        before = {key: value(key) for key in
                  ("audiooutput.audiodevice", "audiooutput.passthroughdevice",
                   "audiooutput.passthrough", "audiooutput.channels",
                   "audiooutput.config")}
        if before != {"audiooutput.audiodevice": HDMI,
                      "audiooutput.passthroughdevice": HDMI,
                      "audiooutput.passthrough": False,
                      "audiooutput.channels": 1,
                      "audiooutput.config": 2} or saved_value("audiooutput.eac3passthrough") != "true":
            raise RuntimeError("unexpected-stereo-predecessor")
        episode = rpc("VideoLibrary.GetEpisodeDetails", {
            "episodeid": EPISODE, "properties": ["file", "playcount"]})["episodedetails"]
        if episode.get("playcount", 0) < 1 or not episode.get("file"):
            raise RuntimeError("not-watched-or-no-file")
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        shutil.copy2(SETTINGS, CHECKPOINT / "guisettings.xml.before")
        os.chmod(CHECKPOINT / "guisettings.xml.before", 0o600)
        (CHECKPOINT / "audio-before.json").write_text(json.dumps(before, sort_keys=True) + "\n")
        os.chmod(CHECKPOINT / "audio-before.json", 0o600)
        xbmc.log("ASTER_EAC3_PATH_PROBE_BEGIN", xbmc.LOGINFO)
        changed = True
        set_value("audiooutput.config", 3)  # Best match; restore Optimized below.
        set_value("audiooutput.passthrough", True)
        rpc("Player.Open", {"item": {"file": episode["file"]}})
        started = True
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline and not rpc("Player.GetActivePlayers"):
            xbmc.sleep(250)
        players = rpc("Player.GetActivePlayers")
        if not any(p.get("type") == "video" for p in players):
            raise RuntimeError("video-did-not-start")
        xbmc.sleep(6000)
        props = rpc("Player.GetProperties", {"playerid": 1,
            "properties": ["currentaudiostream", "audiostreams"]})
        stream = props.get("currentaudiostream", {})
        result["stream"] = {key: stream.get(key) for key in
                            ("codec", "channels", "language")}
        result["kodi_passthrough_setting_during_test"] = value("audiooutput.passthrough")
        log_window = KODI_LOG.read_text(errors="replace").rsplit(
            "ASTER_EAC3_PATH_PROBE_BEGIN", 1)[-1]
        opens = [line for line in log_window.splitlines()
                 if 'CAESinkALSA::Initialize - Opened device "hdmi:CARD=PCH,DEV=0' in line]
        result["sink_mode"] = ("non-audio-raw" if opens and "AES0=0x06" in opens[-1]
                               else "pcm" if opens and "AES0=0x04" in opens[-1]
                               else "unobserved")
        result["passed"] = (stream.get("codec", "").lower() in ("eac3", "e-ac-3")
                            and result["kodi_passthrough_setting_during_test"] is True
                            and result["sink_mode"] == "non-audio-raw")
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        if started:
            try:
                rpc("Player.Stop", {"playerid": 1})
            except Exception as exc:
                result["stop_error"] = str(exc)
        if changed:
            try:
                set_value("audiooutput.passthrough", False)
                set_value("audiooutput.config", 2)
                result["restored"] = (value("audiooutput.audiodevice") == HDMI
                                      and value("audiooutput.passthroughdevice") == HDMI
                                      and value("audiooutput.channels") == 1)
            except Exception as exc:
                result["restore_error"] = str(exc)
        else:
            result["restored"] = True
        xbmc.log("ASTER_EAC3_PATH_PROBE_END", xbmc.LOGINFO)
        RESULT.write_text(json.dumps(result, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
