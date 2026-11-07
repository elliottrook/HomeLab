#!/usr/bin/env python3
"""Run the bounded CC0 fixture through ROMarr manual verification/import."""

from __future__ import annotations

import json
import os
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE = os.environ.get("ROMARR_URL", "http://192.168.20.38:6868").rstrip("/")
API_KEY = os.environ.get("ROMARR_API_KEY", "")
FILENAME = "Aster Infrastructure Test (World) (Homebrew).nes"
STAGING = "/media/usenet/complete/retro-games/aster-infrastructure-test"


def request(path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    call = Request(
        BASE + path,
        data=data,
        method="GET" if data is None else "POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": API_KEY,
        },
    )
    with urlopen(call, timeout=30) as response:
        return json.load(response)


def main() -> int:
    if len(API_KEY) < 20:
        raise RuntimeError("ROMARR_API_KEY is missing")
    setup = request("/api/v1/setup/status")
    scan = request("/api/v1/manualimport?path=" + quote(STAGING, safe="/"))
    candidates = [
        item for item in scan.get("candidates", []) if item.get("filename") == FILENAME
    ]
    if len(candidates) != 1 or candidates[0].get("platform") != "nes":
        raise RuntimeError("synthetic fixture was not uniquely identified as NES")
    imported = request(
        "/api/v1/manualimport",
        {"path": STAGING + "/" + FILENAME, "platform": "nes", "force": False},
    )
    rows = imported.get("imported", [])
    verified = (
        imported.get("ok") is True
        and len(rows) == 1
        and rows[0].get("verdict") == "verified"
        and rows[0].get("forced") is False
        and not imported.get("refused")
    )
    refresh = request("/api/v1/command", {"name": "RefreshLibrary"})
    result = {
        "fixture_license": "CC0-1.0",
        "dat_loaded": int(setup.get("dat_loaded") or 0),
        "scan_candidates": len(candidates),
        "platform": "nes" if candidates else "",
        "verified_import": verified,
        "forced": False,
        "library_refresh_reported": bool(refresh.get("message")),
    }
    result["ok"] = all(
        (
            result["dat_loaded"] >= 1,
            result["scan_candidates"] == 1,
            result["platform"] == "nes",
            result["verified_import"],
            result["library_refresh_reported"],
        )
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
