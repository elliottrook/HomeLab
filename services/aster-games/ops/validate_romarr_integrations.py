#!/usr/bin/env python3
"""Test ROMarr dependencies without printing credentials or catalogue data."""

from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE = os.environ.get("ROMARR_URL", "http://192.168.20.38:6868").rstrip("/")
API_KEY = os.environ.get("ROMARR_API_KEY", "")
SABNZBD_URL = os.environ.get("SABNZBD_URL", "").rstrip("/")
SABNZBD_API_KEY = os.environ.get("SABNZBD_API_KEY", "")


def request(path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    method = "GET" if data is None else "POST"
    call = Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": API_KEY,
        },
    )
    with urlopen(call, timeout=10) as response:
        return json.load(response)


def exactly_one(items: list[dict], item_type: str) -> dict:
    matches = [item for item in items if item.get("type") == item_type]
    if len(matches) != 1:
        types = sorted(str(item.get("type")) for item in items)
        raise RuntimeError(f"expected exactly one {item_type} entry; found {types}")
    return matches[0]


def main() -> int:
    if len(API_KEY) < 20:
        raise RuntimeError("ROMARR_API_KEY is missing")
    if not SABNZBD_URL or len(SABNZBD_API_KEY) < 20:
        raise RuntimeError("SABnzbd connection settings are missing")
    config = request("/api/v1/config")
    configured = {
        "romm": exactly_one(config.get("libraries", []), "romm"),
        "prowlarr": exactly_one(config.get("indexers", []), "prowlarr"),
        "sabnzbd": exactly_one(config.get("download_clients", []), "sabnzbd"),
    }
    checks = {
        "romm": request(
            "/api/v1/library/test", configured["romm"]
        ),
        "prowlarr": request(
            "/api/v1/indexer/test", configured["prowlarr"]
        ),
        "sabnzbd": request(
            "/api/v1/downloadclient/test",
            configured["sabnzbd"],
        ),
    }
    result = {
        name: {
            "ok": bool(value.get("ok")),
            "enabled": bool(configured[name].get("enable")),
        }
        for name, value in checks.items()
    }
    sab_request = SABNZBD_URL + "/api?" + urlencode(
        {"mode": "get_cats", "output": "json", "apikey": SABNZBD_API_KEY}
    )
    with urlopen(sab_request, timeout=10) as response:
        categories = json.load(response).get("categories", [])
    result["sabnzbd"]["dedicated_category"] = (
        configured["sabnzbd"].get("category") == "retro-games"
        and "retro-games" in categories
    )
    result["policy_ok"] = (
        result["romm"]["ok"]
        and result["prowlarr"]["ok"]
        and result["sabnzbd"]["ok"]
        and result["romm"]["enabled"]
        and not result["prowlarr"]["enabled"]
        and not result["sabnzbd"]["enabled"]
        and result["sabnzbd"]["dedicated_category"]
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["policy_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
