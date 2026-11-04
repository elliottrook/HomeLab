#!/usr/bin/env python3
"""Issue a distinct Jellyfin Quick Connect session for AsterTV-Jen."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import tempfile
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET


HOST = "AsterTV-Jen"
SERVER = "http://192.168.20.40:8096"
STATE = Path("/storage/.aster-staging/jellyfin-quick-connect.json")
PROFILE = Path("/storage/.kodi/userdata/addon_data/plugin.video.jellyfin")
SETTINGS_TEMPLATE = Path("/storage/.aster-staging/jellyfin-family-settings.xml")


def atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def request(path: str, *, headers: dict[str, str], body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    req = urllib.request.Request(
        SERVER + path, data=data, method="POST" if body is not None else "GET",
        headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("jellyfin-http-status")
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise RuntimeError("jellyfin-response-size")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("jellyfin-response-schema")
    return value


def base_headers(device_id: str) -> dict[str, str]:
    values = {
        "Client": "Jellyfin for Kodi",
        "Device": HOST,
        "DeviceId": device_id,
        "Version": "2.2.0+py3",
    }
    auth = "MediaBrowser " + ", ".join(
        key + "=" + urllib.parse.quote(value, safe="") for key, value in values.items())
    return {"Accept": "application/json", "Authorization": auth,
            "X-Application": "Jellyfin for Kodi/2.2.0+py3"}


def initiate() -> None:
    if STATE.exists() or PROFILE.exists():
        raise RuntimeError("jellyfin-provisioning-state")
    device_id = uuid.uuid4().hex
    result = request("/QuickConnect/Initiate", headers=base_headers(device_id), body={})
    if (set(result) < {"Secret", "Code", "Authenticated"}
            or not isinstance(result["Secret"], str)
            or not isinstance(result["Code"], str)
            or result["Authenticated"] is not False):
        raise RuntimeError("jellyfin-quick-connect-schema")
    atomic(STATE, (json.dumps({"device_id": device_id, **result}, sort_keys=True)
                   + "\n").encode())
    print(json.dumps({"initiated": True, "credential_output": False}, sort_keys=True))


def finish() -> None:
    if not STATE.is_file() or not SETTINGS_TEMPLATE.is_file() or PROFILE.exists():
        raise RuntimeError("jellyfin-finish-state")
    state = json.loads(STATE.read_text())
    status = request(
        "/QuickConnect/Connect?Secret=" + urllib.parse.quote(state["Secret"], safe=""),
        headers=base_headers(state["device_id"]))
    if status.get("Authenticated") is not True:
        raise RuntimeError("jellyfin-quick-connect-not-authorized")
    auth = request("/Users/AuthenticateWithQuickConnect",
                   headers=base_headers(state["device_id"]),
                   body={"Secret": state["Secret"]})
    user = auth.get("User") or {}
    if (not isinstance(auth.get("AccessToken"), str) or len(auth["AccessToken"]) < 16
            or not isinstance(auth.get("ServerId"), str)
            or not isinstance(user.get("Id"), str)
            or not isinstance(user.get("Name"), str)):
        raise RuntimeError("jellyfin-auth-schema")

    settings = ET.parse(SETTINGS_TEMPLATE)
    for setting in settings.getroot().findall("setting"):
        identity = setting.get("id")
        if identity == "deviceName":
            setting.text = HOST
        elif identity == "server":
            setting.text = SERVER
        elif identity == "serverName":
            setting.text = "elliottrook"
        elif identity == "username":
            setting.text = user["Name"]
        elif identity == "LastIncrementalSync":
            setting.text = ""
        elif identity == "SyncInstallRunDone":
            setting.text = "false"
    credentials = {"Servers": [{
        "AccessToken": auth["AccessToken"],
        "DateLastAccessed": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "Id": auth["ServerId"],
        "Name": "elliottrook",
        "UserId": user["Id"],
        "Users": [{"Id": user["Id"], "IsSignedInOffline": True}],
        "address": SERVER,
    }]}
    PROFILE.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        atomic(PROFILE / "data.json",
               (json.dumps(credentials, sort_keys=True) + "\n").encode())
        # Jellyfin for Kodi reads this file verbatim. A trailing newline is
        # harmless in percent-encoded HTTP auth but breaks its websocket
        # Authorization header with an HTTP 400 response.
        atomic(PROFILE / "jellyfin_guid", state["device_id"].encode())
        raw = ET.tostring(settings.getroot(), encoding="utf-8", xml_declaration=True)
        atomic(PROFILE / "settings.xml", raw + b"\n")
        atomic(PROFILE / "provisioning.json", (json.dumps({
            "kind": "jellyfin-quick-connect",
            "device": HOST,
            "server": SERVER,
            "user_id_sha256": __import__("hashlib").sha256(user["Id"].encode()).hexdigest(),
            "token_sha256": __import__("hashlib").sha256(auth["AccessToken"].encode()).hexdigest(),
        }, sort_keys=True) + "\n").encode())
    except Exception:
        import shutil
        shutil.rmtree(PROFILE, ignore_errors=True)
        raise
    STATE.unlink()
    print(json.dumps({"provisioned": True, "device": HOST,
                      "same_user": user["Name"], "credential_output": False}, sort_keys=True))


def main() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("initiate", "finish"))
    args = parser.parse_args()
    {"initiate": initiate, "finish": finish}[args.action]()


if __name__ == "__main__":
    main()
