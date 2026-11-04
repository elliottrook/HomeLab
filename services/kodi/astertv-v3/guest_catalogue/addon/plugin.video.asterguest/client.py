"""Credential-private Jellyfin client for the Guest adapter."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from core import GuestCatalogueError, api_path, shape_item, shape_items


CREDENTIAL = Path("/storage/.aster-private/jellyfin-guest.json")


def credential():
    details = CREDENTIAL.stat()
    if details.st_mode & 0o077:
        raise GuestCatalogueError("credential-permissions")
    value = json.loads(CREDENTIAL.read_text(encoding="utf-8"))
    if (value.get("schema") != 1 or not value.get("access_token")
            or not value.get("user_id") or not value.get("server_url")):
        raise GuestCatalogueError("credential-schema")
    return value


def request(path):
    auth = credential()
    authorization = (
        "MediaBrowser Client=AsterTV Guest, Device=AsterTV-Jen, "
        "DeviceId=" + auth["device_id"] + ", Version=1, Token=" + auth["access_token"]
    )
    query = urllib.request.Request(
        auth["server_url"].rstrip("/") + path,
        headers={"Accept": "application/json", "X-Emby-Token": auth["access_token"],
                 "Authorization": authorization},
    )
    try:
        with urllib.request.urlopen(query, timeout=15) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
    except (urllib.error.URLError, TimeoutError) as error:
        raise GuestCatalogueError("catalogue-unavailable") from error
    if len(raw) > 4 * 1024 * 1024:
        raise GuestCatalogueError("catalogue-response-too-large")
    return json.loads(raw)


def libraries():
    auth = credential()
    allowed = {row["id"].lower(): row for row in auth["allowed_folders"]}
    rows = request(api_path("libraries", user_id=auth["user_id"])).get("Items", [])
    result = []
    for row in rows:
        identifier = str(row.get("Id", "")).lower()
        if identifier in allowed and row.get("Name") == allowed[identifier]["name"]:
            result.append({"Id": identifier, "Name": row["Name"],
                           "CollectionType": allowed[identifier]["type"]})
    if len(result) != 4:
        raise GuestCatalogueError("library-authority-drift")
    return result


def items(parent_id, kind):
    auth = credential()
    return shape_items(request(api_path("items", user_id=auth["user_id"],
                                        parent_id=parent_id, item=kind)), [kind])


def item(identifier):
    auth = credential()
    return shape_item(request(api_path("item", user_id=auth["user_id"], item=identifier)))
