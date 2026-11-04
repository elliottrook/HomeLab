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

