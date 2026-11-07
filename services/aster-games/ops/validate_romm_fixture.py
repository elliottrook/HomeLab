#!/usr/bin/env python3
"""Trigger the bounded RomM scan and verify one fixture without naming it."""

from __future__ import annotations

import json
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE = os.environ.get("ROMM_URL", "http://192.168.20.38:8080").rstrip("/")
TOKEN = os.environ.get("ROMM_ROMARR_API_KEY", "")


def call(path: str, payload: dict | None = None) -> tuple[int, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        BASE + path,
        data=data,
        method="GET" if data is None else "POST",
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def main() -> int:
    if len(TOKEN) < 20:
        raise RuntimeError("ROMM_ROMARR_API_KEY is missing")
    scan_status, _ = call(
        "/api/tasks/scan", {"type": "quick", "platform_fs_slugs": ["nes"]}
    )
    if scan_status not in (202, 409):
        raise RuntimeError(f"RomM scan request failed with HTTP {scan_status}")
    count = -1
    fields: set[str] = set()
    for _ in range(30):
        status, document = call("/api/roms?limit=10")
        if status == 200:
            rows = document.get("items", document) if isinstance(document, dict) else document
            if isinstance(rows, list):
                count = len(rows)
                fields = set(rows[0]) if rows else set()
                if count == 1:
                    break
        time.sleep(2)
    result = {
        "scan_http": scan_status,
        "catalogue_items": count,
        "record_has_id": "id" in fields,
        "record_has_platform": bool({"platform", "platform_slug"} & fields),
    }
    result["ok"] = (
        count == 1 and result["record_has_id"] and result["record_has_platform"]
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
