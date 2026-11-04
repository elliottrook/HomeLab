#!/usr/bin/env python3
"""Provision one independently revocable AsterTV-Jen Guest Jellyfin user."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import socket
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


HOST = "AsterTV-Jen"
SERVER = "http://192.168.20.40:8096"
USERNAME = "AsterTV-Guest"
LIBRARIES = {"Movies": "movies", "Shows": "tvshows",
             "Archive Movies": "movies", "Archive TV": "tvshows"}
STATE = Path("/storage/.aster-staging/astertv-guest-admin.json")
CREDENTIAL = Path("/storage/.aster-private/jellyfin-guest.json")
DEVICE_ID = "astertv-jen-guest-catalogue"


def atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path); os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def auth_header(device_id, token=None):
    values = {"Client": "AsterTV Guest Provisioner", "Device": HOST,
              "DeviceId": device_id, "Version": "1"}
    if token:
        values["Token"] = token
    return "MediaBrowser " + ", ".join(
        key + "=" + urllib.parse.quote(value, safe="") for key, value in values.items()
    )


def request(path, *, method="GET", token=None, device_id=DEVICE_ID,
            body=None, expected=(200,)):
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    query = urllib.request.Request(
        SERVER + path, data=payload, method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "Authorization": auth_header(device_id, token)})
    try:
        with urllib.request.urlopen(query, timeout=15) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code; raw = error.read(4096)
    if status not in expected or len(raw) > 4 * 1024 * 1024:
        raise RuntimeError("jellyfin-http-" + str(status))
    return None if not raw else json.loads(raw)


def build_policy(current, folder_ids, *, device_enabled):
    policy = dict(current)
    changes = {
        "IsAdministrator": False, "IsHidden": True, "IsDisabled": False,
        "EnableUserPreferenceAccess": False, "EnableRemoteAccess": True,
        "EnableMediaPlayback": True, "EnableAudioPlaybackTranscoding": True,
        "EnableVideoPlaybackTranscoding": True, "EnablePlaybackRemuxing": True,
        "ForceRemoteSourceTranscoding": False, "EnableContentDownloading": False,
        "EnableSyncTranscoding": False, "EnableMediaConversion": False,
        "EnableContentDeletion": False, "EnableContentDeletionFromFolders": [],
        "EnableCollectionManagement": False, "EnableSubtitleManagement": False,
        "EnableLyricManagement": False, "EnablePublicSharing": False,
        "EnableLiveTvAccess": False, "EnableLiveTvManagement": False,
        "EnableRemoteControlOfOtherUsers": False, "EnableSharedDeviceControl": False,
        "EnableAllChannels": False, "EnabledChannels": [],
        "EnableAllFolders": False, "EnabledFolders": list(folder_ids),
        "BlockedMediaFolders": [], "EnableAllDevices": bool(device_enabled),
        "EnabledDevices": [] if device_enabled else [DEVICE_ID],
        "MaxActiveSessions": 2, "SyncPlayAccess": "None",
    }
    policy.update(changes)
    return policy


def initiate():
    if STATE.exists():
        raise RuntimeError("guest-provisioning-state")
    device_id = uuid.uuid4().hex
    result = request("/QuickConnect/Initiate", method="POST", body={}, device_id=device_id)
    if (not isinstance(result, dict) or result.get("Authenticated") is not False
            or not isinstance(result.get("Secret"), str)
            or not isinstance(result.get("Code"), str)):
        raise RuntimeError("quick-connect-schema")
    atomic(STATE, (json.dumps({"schema": 1, "phase": "initiated",
                              "device_id": device_id, "quick_connect": result},
                             sort_keys=True) + "\n").encode())
    print(json.dumps({"initiated": True, "code": result["Code"],
                      "credential_output": False}, sort_keys=True))


def connect_admin():
    state = json.loads(STATE.read_text())
    if state.get("phase") != "initiated":
        raise RuntimeError("quick-connect-phase")
    secret = state["quick_connect"]["Secret"]
    status = request("/QuickConnect/Connect?Secret=" + urllib.parse.quote(secret, safe=""),
                     device_id=state["device_id"])
    if status.get("Authenticated") is not True:
        raise RuntimeError("quick-connect-not-authorized")
    auth = request("/Users/AuthenticateWithQuickConnect", method="POST",
                   body={"Secret": secret}, device_id=state["device_id"])
    token = auth.get("AccessToken"); user = auth.get("User") or {}
    if not isinstance(token, str) or len(token) < 16 or not user.get("Id"):
        raise RuntimeError("admin-auth-schema")
    full = request("/Users/" + user["Id"], token=token, device_id=state["device_id"])
    if (full.get("Policy") or {}).get("IsAdministrator") is not True:
        raise RuntimeError("quick-connect-user-not-admin")
    atomic(STATE, (json.dumps({"schema": 1, "phase": "admin-connected",
                              "device_id": state["device_id"], "admin_token": token,
                              "admin_user_id": user["Id"]}, sort_keys=True) + "\n").encode())
    print(json.dumps({"admin_connected": True, "credential_output": False}, sort_keys=True))


def _admin_state():
    value = json.loads(STATE.read_text())
    if value.get("phase") != "admin-connected" or not value.get("admin_token"):
        raise RuntimeError("admin-state-unavailable")
    return value


def create_guest():
    state = _admin_state(); admin = state["admin_token"]; admin_device = state["device_id"]
    users = request("/Users", token=admin, device_id=admin_device)
    if any(row.get("Name", "").casefold() == USERNAME.casefold() for row in users):
        raise RuntimeError("guest-user-collision")
    folders = request("/Library/VirtualFolders", token=admin, device_id=admin_device)
    selected = []
    for name, collection_type in LIBRARIES.items():
        matches = [row for row in folders if row.get("Name") == name
                   and row.get("CollectionType") == collection_type and row.get("ItemId")]
        if len(matches) != 1:
            raise RuntimeError("guest-library-selection:" + name)
        selected.append({"id": matches[0]["ItemId"], "name": name, "type": collection_type})
    password = secrets.token_urlsafe(36)
    created = request("/Users/New", method="POST", token=admin, device_id=admin_device,
                      body={"Name": USERNAME, "Password": password})
    user_id = created.get("Id")
    if not isinstance(user_id, str):
        raise RuntimeError("guest-create-schema")
    try:
        current = request("/Users/" + user_id, token=admin, device_id=admin_device)["Policy"]
        initial = build_policy(current, [row["id"] for row in selected], device_enabled=True)
        request("/Users/" + user_id + "/Policy", method="POST", token=admin,
                device_id=admin_device, body=initial, expected=(204,))
        auth = request("/Users/AuthenticateByName", method="POST", device_id=DEVICE_ID,
                       body={"Username": USERNAME, "Pw": password})
        guest_token = auth.get("AccessToken"); guest = auth.get("User") or {}
        if not isinstance(guest_token, str) or guest.get("Id") != user_id:
            raise RuntimeError("guest-auth-schema")
        final = build_policy(initial, [row["id"] for row in selected], device_enabled=False)
        request("/Users/" + user_id + "/Policy", method="POST", token=admin,
                device_id=admin_device, body=final, expected=(204,))
        credential = {"schema": 1, "server_url": SERVER, "user_id": user_id,
                      "user_id_sha256": hashlib.sha256(user_id.encode()).hexdigest(),
                      "access_token": guest_token, "device_id": DEVICE_ID,
                      "allowed_folders": selected}
        atomic(CREDENTIAL, (json.dumps(credential, sort_keys=True) + "\n").encode())
    except Exception:
        request("/Users/" + user_id, method="DELETE", token=admin,
                device_id=admin_device, expected=(204,))
        raise
    print(json.dumps({"created": True, "libraries": [x["name"] for x in selected],
                      "playback": True, "credential_output": False}, sort_keys=True))


def delete_guest():
    state = _admin_state(); admin = state["admin_token"]; admin_device = state["device_id"]
    users = request("/Users", token=admin, device_id=admin_device)
    matches = [row for row in users if row.get("Name", "").casefold() == USERNAME.casefold()]
    if len(matches) != 1:
        raise RuntimeError("guest-user-count")
    request("/Users/" + matches[0]["Id"], method="DELETE", token=admin,
            device_id=admin_device, expected=(204,))
    CREDENTIAL.unlink(missing_ok=True)
    print(json.dumps({"deleted": True, "credential_output": False}, sort_keys=True))


def update_policy():
    state = _admin_state(); admin = state["admin_token"]; admin_device = state["device_id"]
    credential = json.loads(CREDENTIAL.read_text())
    users = request("/Users", token=admin, device_id=admin_device)
    matches = [row for row in users if row.get("Name", "").casefold() == USERNAME.casefold()
               and row.get("Id") == credential.get("user_id")]
    if len(matches) != 1:
        raise RuntimeError("guest-user-identity-drift")
    folder_ids = [row["id"] for row in credential.get("allowed_folders", [])]
    if len(folder_ids) != 4:
        raise RuntimeError("guest-folder-authority-drift")
    current = request("/Users/" + matches[0]["Id"], token=admin,
                      device_id=admin_device)["Policy"]
    updated = build_policy(current, folder_ids, device_enabled=False)
    request("/Users/" + matches[0]["Id"] + "/Policy", method="POST", token=admin,
            device_id=admin_device, body=updated, expected=(204,))
    print(json.dumps({"policy_updated": True, "audio_transcode": True,
                      "credential_output": False}, sort_keys=True))


def close_admin():
    state = _admin_state()
    request("/Sessions/Logout", method="POST", token=state["admin_token"],
            device_id=state["device_id"], body={}, expected=(204,))
    STATE.unlink()
    print(json.dumps({"admin_session_closed": True, "credential_output": False}, sort_keys=True))


def main():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("initiate", "connect-admin", "create", "delete",
                                           "update-policy", "close-admin"))
    action = parser.parse_args().action
    {"initiate": initiate, "connect-admin": connect_admin, "create": create_guest,
     "delete": delete_guest, "update-policy": update_policy,
     "close-admin": close_admin}[action]()


if __name__ == "__main__":
    main()
