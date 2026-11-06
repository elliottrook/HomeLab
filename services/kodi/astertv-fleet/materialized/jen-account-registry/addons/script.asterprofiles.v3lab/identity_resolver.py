#!/usr/bin/env python3
"""Resolve Jen's existing credential custody to non-secret profile subjects."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from pathlib import Path


SHA256 = re.compile(r"^[0-9a-f]{64}$")


class IdentityError(ValueError):
    pass


def home_subject(identity):
    if (not isinstance(identity, dict)
            or set(identity) != {"schema", "kind", "authority"}
            or identity.get("schema") != 1
            or identity.get("kind") != "astertv-home-display"
            or identity.get("authority") != "ha-home-dashboard-v4"):
        raise IdentityError("home-identity-invalid")
    # Identity is semantic. Whitespace and key order may differ between the
    # installer and the fleet renderer, so never bind authority to raw JSON.
    canonical = (json.dumps(identity, sort_keys=True) + "\n").encode()
    return ("local:home-assistant:display:sha256:"
            + hashlib.sha256(canonical).hexdigest())


def _json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError) as error:
        raise IdentityError("identity-state-unavailable:" + path.name) from error


def _private_file(path):
    try:
        details = path.stat()
        return path.is_file() and details.st_mode & 0o077 == 0
    except OSError:
        return False


def discover(root=Path("/")):
    storage = root / "storage" if root != Path("/") else Path("/storage")
    profile = storage / ".kodi/userdata/addon_data"
    subjects = {}

    home_identity = storage / ".aster-home/display-identity.json"
    if _private_file(home_identity):
        identity = _json(home_identity)
        try:
            subjects["home_assistant"] = home_subject(identity)
        except IdentityError:
            pass

    guest_path = storage / ".aster-private/jellyfin-guest.json"
    if _private_file(guest_path):
        guest = _json(guest_path)
        guest_id = guest.get("user_id") if isinstance(guest, dict) else None
        guest_hash = guest.get("user_id_sha256") if isinstance(guest, dict) else None
        folders = guest.get("allowed_folders") if isinstance(guest, dict) else None
        if (guest.get("schema") == 1 and isinstance(guest_id, str) and guest_id
                and guest_hash == hashlib.sha256(guest_id.encode()).hexdigest()
                and isinstance(guest.get("access_token"), str) and guest["access_token"]
                and guest.get("device_id") == "astertv-jen-guest-catalogue"
                and isinstance(folders, list) and len(folders) == 4
                and {row.get("name") for row in folders if isinstance(row, dict)}
                    == {"Movies", "Shows", "Archive Movies", "Archive TV"}):
            subjects["jellyfin_guest"] = (
                "local:jellyfin-guest:sha256:" + guest_hash
            )

    jellyfin = profile / "plugin.video.jellyfin"
    data_path = jellyfin / "data.json"
    provisioning_path = jellyfin / "provisioning.json"
    if _private_file(data_path) and _private_file(provisioning_path):
        data = _json(data_path)
        provisioning = _json(provisioning_path)
        servers = data.get("Servers")
        if (isinstance(data, dict) and isinstance(provisioning, dict)
                and isinstance(servers, list) and len(servers) == 1
                and isinstance(servers[0], dict)):
            server = servers[0]
            user_id = server.get("UserId")
            access = server.get("AccessToken")
            if isinstance(user_id, str) and user_id and isinstance(access, str) and access:
                subject_hash = hashlib.sha256(user_id.encode()).hexdigest()
                if provisioning.get("user_id_sha256") == subject_hash:
                    subjects["jellyfin"] = "local:jellyfin:sha256:" + subject_hash

    books = profile / "plugin.audio.asterbooks"
    client_path = books / "client.json"
    progress_path = books / "progress-enabled.json"
    if _private_file(client_path) and _private_file(progress_path):
        client = _json(client_path)
        progress = _json(progress_path)
        account_hash = progress.get("account_sha256") if isinstance(progress, dict) else None
        if (isinstance(client, dict) and isinstance(progress, dict)
                and progress.get("enabled") is True and isinstance(account_hash, str)
                and SHA256.fullmatch(account_hash)
                and isinstance(client.get("api_key"), str) and client["api_key"]
                and isinstance(client.get("server_url"), str) and client["server_url"]):
            subjects["audiobookshelf"] = (
                "local:audiobookshelf:sha256:" + account_hash
            )

    seerr_path = storage / ".aster-private/seerr-token"
    if _private_file(seerr_path):
        try:
            present = bool(seerr_path.read_text(encoding="utf-8").strip())
        except OSError:
            present = False
        if present:
            subjects["seerr"] = "local:seerr:client:astertv-jen"

    aster_tv_path = storage / ".aster-private/astertv-broker.key"
    if _private_file(aster_tv_path):
        try:
            broker_key = aster_tv_path.read_text(encoding="utf-8").strip()
        except OSError:
            broker_key = ""
        if len(broker_key) >= 32:
            subjects["aster_tv"] = (
                "local:astertv-broker:sha256:"
                + hashlib.sha256(broker_key.encode()).hexdigest()
            )

    youtube = profile / "plugin.video.youtube"
    youtube_access = youtube / "access_manager.json"
    youtube_keys = youtube / "api_keys.json"
    youtube_settings = youtube / "settings.xml"
    if all(_private_file(path) for path in
           (youtube_access, youtube_keys, youtube_settings)):
        access = _json(youtube_access)
        keys = _json(youtube_keys)
        manager = access.get("access_manager") if isinstance(access, dict) else None
        users = manager.get("users") if isinstance(manager, dict) else None
        current = manager.get("current_user") if isinstance(manager, dict) else None
        user = users.get(str(current)) if isinstance(users, dict) else None
        user_keys = keys.get("keys", {}).get("user") if isinstance(keys, dict) else None
        if (isinstance(user, dict) and isinstance(user.get("id"), str)
                and user["id"] and isinstance(user.get("access_token"), str)
                and user["access_token"] and isinstance(user.get("refresh_token"), str)
                and user["refresh_token"] and isinstance(user_keys, dict)
                and all(isinstance(user_keys.get(field), str) and user_keys[field]
                        for field in ("api_key", "client_id", "client_secret"))):
            subjects["youtube"] = (
                "local:youtube:sha256:"
                + hashlib.sha256(user["id"].encode()).hexdigest()
            )
    return subjects


def resolve_registry(registry, root=Path("/")):
    """Return an effective copy; unresolved mappings fail closed in memory."""
    effective = copy.deepcopy(registry)
    try:
        subjects = discover(root)
        status = "resolved"
    except IdentityError:
        subjects = {}
        status = "identity-state-unavailable"
    mismatch = False
    for profile in effective.get("profiles", ()):
        for mapping in profile.get("service_mappings", ()):
            if mapping.get("enabled") is True:
                expected = subjects.get(mapping.get("service"))
                if expected != mapping.get("opaque_subject_id"):
                    mapping["enabled"] = False
                    mismatch = True
    if mismatch:
        status = "identity-mismatch"
    return effective, status

